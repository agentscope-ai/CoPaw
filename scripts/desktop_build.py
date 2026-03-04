#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main build orchestrator for CoPaw desktop app.

This script handles the complete build process:
1. Build React frontend
2. Copy frontend to Python package
3. Build Python sidecar with PyInstaller
4. Build Tauri application
5. Create DMG installer (optional)

Usage:
    python scripts/desktop_build.py [options]

Options:
    --skip-frontend    Skip frontend build (use existing)
    --skip-sidecar     Skip sidecar build (use existing)
    --dmg              Create DMG after build
    --release          Build in release mode (default)
    --dev              Build in development mode
"""

import argparse
import hashlib
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


def run_command(cmd, cwd=None, check=True, env=None):
    """Run a command and handle errors."""
    print(f"\n▶ Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd, cwd=cwd, check=False, capture_output=False, env=env
    )
    if check and result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result


def build_frontend():
    """Build the React frontend."""
    print("\n" + "=" * 60)
    print("📦 Step 1: Building frontend...")
    print("=" * 60)

    console_dir = PROJECT_ROOT / "console"

    # Install dependencies
    run_command(["npm", "ci"], cwd=console_dir)

    # Build
    run_command(["npm", "run", "build"], cwd=console_dir)

    # Copy to Python package for PyInstaller
    dest = PROJECT_ROOT / "src" / "copaw" / "console"
    dest.mkdir(parents=True, exist_ok=True)

    # Clear existing
    for item in dest.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    # Copy new build
    dist_dir = console_dir / "dist"
    for item in dist_dir.iterdir():
        if item.is_dir():
            shutil.copytree(item, dest / item.name)
        else:
            shutil.copy2(item, dest)

    print(f"✅ Frontend built and copied to {dest}")


def build_sidecar():
    """Build the Python sidecar binary using PyInstaller."""
    print("\n" + "=" * 60)
    print("🐍 Step 2: Building Python sidecar...")
    print("=" * 60)

    # Install PyInstaller if needed
    run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Build with spec file - run from the spec file's directory
    spec_dir = PROJECT_ROOT / "desktop" / "pyinstaller"
    spec_file = spec_dir / "CoPawBackend.spec"

    run_command(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            str(spec_file),
        ],
        cwd=spec_dir,  # Run from spec file directory
    )

    # Copy binary to Tauri expected location
    binary_name = "copaw-backend"
    if platform.system() == "Windows":
        binary_name += ".exe"

    # PyInstaller outputs to dist/ relative to the spec file directory
    sidecar_root = spec_dir / "dist" / "copaw-backend"
    src = sidecar_root / binary_name
    if not src.exists():
        print(f"❌ Sidecar binary not found at {src}")
        sys.exit(1)
    internal_src = sidecar_root / "_internal"
    if not internal_src.exists():
        print(f"❌ Sidecar runtime directory not found at {internal_src}")
        sys.exit(1)

    dst_dir = PROJECT_ROOT / "src-tauri" / "binaries"
    dst_dir.mkdir(parents=True, exist_ok=True)

    # Determine target triple
    if platform.system() == "Darwin":
        arch = platform.machine().lower()
        if arch in ("x86_64", "amd64"):
            target = "x86_64-apple-darwin"
        elif arch in ("arm64", "aarch64"):
            target = "aarch64-apple-darwin"
        else:
            print(f"❌ Unsupported architecture: {arch}")
            sys.exit(1)
    elif platform.system() == "Windows":
        target = "x86_64-pc-windows-msvc"
    else:
        target = "x86_64-unknown-linux-gnu"

    if platform.system() == "Darwin":
        # Keep both mac targets in sync to avoid stale sidecar selection.
        dst_aarch64 = dst_dir / f"{binary_name}-aarch64-apple-darwin"
        dst_x86 = dst_dir / f"{binary_name}-x86_64-apple-darwin"
        shutil.copy2(src, dst_aarch64)
        shutil.copy2(src, dst_x86)
        internal_dst = dst_dir / "_internal"
        if internal_dst.exists():
            shutil.rmtree(internal_dst)
        shutil.copytree(internal_src, internal_dst)
        dst_aarch64.chmod(0o755)
        dst_x86.chmod(0o755)
        print(f"✅ Sidecar built and copied to {dst_aarch64}")
        print(f"✅ Sidecar built and copied to {dst_x86}")
        print(f"✅ Sidecar runtime dir copied to {internal_dst}")
    else:
        dst = dst_dir / f"{binary_name}-{target}"
        shutil.copy2(src, dst)
        dst.chmod(0o755)
        print(f"✅ Sidecar built and copied to {dst}")


def build_tauri(release=True):
    """Build the Tauri application."""
    print("\n" + "=" * 60)
    print("🦀 Step 3: Building Tauri application...")
    print("=" * 60)

    # Check if Rust is installed
    result = run_command(["rustc", "--version"], check=False)
    if result.returncode != 0:
        print("❌ Rust is not installed. Please install from https://rustup.rs/")
        sys.exit(1)

    # Check if Tauri CLI is installed
    result = run_command(["cargo", "tauri", "--version"], check=False)
    if result.returncode != 0:
        print("Installing Tauri CLI...")
        run_command(["cargo", "install", "tauri-cli"])

    # Build
    cmd = ["cargo", "tauri", "build"]
    if not release:
        cmd.append("--debug")

    run_command(cmd, cwd=PROJECT_ROOT)

    print("✅ Tauri application built successfully")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_sidecar_hash(release=True):
    if platform.system() != "Darwin":
        return

    arch = platform.machine().lower()
    if arch in ("x86_64", "amd64"):
        target = "x86_64-apple-darwin"
    else:
        target = "aarch64-apple-darwin"

    src_sidecar = PROJECT_ROOT / "src-tauri" / "binaries" / f"copaw-backend-{target}"
    app_sidecar = (
        PROJECT_ROOT
        / "src-tauri"
        / "target"
        / ("release" if release else "debug")
        / "bundle"
        / "macos"
        / "CoPaw.app"
        / "Contents"
        / "MacOS"
        / "copaw-backend"
    )
    if not src_sidecar.exists() or not app_sidecar.exists():
        print("⚠️ Skip sidecar hash verification (missing sidecar file)")
        return

    src_sha = sha256_file(src_sidecar)
    app_sha = sha256_file(app_sidecar)
    if src_sha != app_sha:
        print(f"❌ Sidecar hash mismatch: src={src_sha} app={app_sha}")
        sys.exit(1)
    print(f"✅ Sidecar hash verified: {src_sha}")


def sync_sidecar_internal_to_app(release=True):
    if platform.system() != "Darwin":
        return

    internal_src = PROJECT_ROOT / "src-tauri" / "binaries" / "_internal"
    if not internal_src.exists():
        print("⚠️ Skip sidecar runtime dir sync (src-tauri/binaries/_internal missing)")
        return

    app_internal = (
        PROJECT_ROOT
        / "src-tauri"
        / "target"
        / ("release" if release else "debug")
        / "bundle"
        / "macos"
        / "CoPaw.app"
        / "Contents"
        / "MacOS"
        / "_internal"
    )
    if app_internal.exists():
        shutil.rmtree(app_internal)
    app_internal.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(internal_src, app_internal)
    print(f"✅ Sidecar runtime dir synced to {app_internal}")


def create_dmg():
    """Create DMG for distribution."""
    print("\n" + "=" * 60)
    print("💿 Step 4: Creating DMG installer...")
    print("=" * 60)

    if platform.system() != "Darwin":
        print("⚠️ DMG creation is only supported on macOS")
        return

    # Find the built app
    app_path = (
        PROJECT_ROOT
        / "src-tauri"
        / "target"
        / "release"
        / "bundle"
        / "macos"
        / "CoPaw.app"
    )
    if not app_path.exists():
        # Try debug build
        app_path = (
            PROJECT_ROOT
            / "src-tauri"
            / "target"
            / "debug"
            / "bundle"
            / "macos"
            / "CoPaw.app"
        )

    if not app_path.exists():
        print(f"❌ App bundle not found")
        sys.exit(1)

    # Create output directory
    output_dir = PROJECT_ROOT / "dist"
    output_dir.mkdir(exist_ok=True)

    dmg_path = output_dir / "CoPaw.dmg"

    # Remove existing DMG
    if dmg_path.exists():
        dmg_path.unlink()

    # Create DMG using hdiutil
    run_command(
        [
            "hdiutil",
            "create",
            "-volname",
            "CoPaw",
            "-srcfolder",
            str(app_path),
            "-ov",
            "-format",
            "UDZO",
            str(dmg_path),
        ]
    )

    print(f"✅ DMG created at {dmg_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Build CoPaw desktop app",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--skip-frontend",
        action="store_true",
        help="Skip frontend build (use existing)",
    )
    parser.add_argument(
        "--skip-sidecar",
        action="store_true",
        help="Skip sidecar build (use existing)",
    )
    parser.add_argument(
        "--dmg",
        action="store_true",
        help="Create DMG after build (macOS only)",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        default=True,
        help="Build in release mode (default)",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Build in development mode",
    )
    args = parser.parse_args()

    release = not args.dev

    # Ensure directories exist
    (PROJECT_ROOT / "dist").mkdir(exist_ok=True)

    print("=" * 60)
    print("🚀 CoPaw Desktop Build")
    print("=" * 60)
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Mode: {'Release' if release else 'Debug'}")
    print(f"Project root: {PROJECT_ROOT}")

    try:
        if not args.skip_frontend:
            build_frontend()
        else:
            print("\n⏭️ Skipping frontend build")

        if not args.skip_sidecar:
            build_sidecar()
        else:
            print("\n⏭️ Skipping sidecar build")

        build_tauri(release=release)
        sync_sidecar_internal_to_app(release=release)
        verify_sidecar_hash(release=release)

        if args.dmg:
            create_dmg()

        print("\n" + "=" * 60)
        print("✨ BUILD COMPLETE!")
        print("=" * 60)

        # Print output locations
        app_path = (
            PROJECT_ROOT
            / "src-tauri"
            / "target"
            / ("release" if release else "debug")
            / "bundle"
            / "macos"
            / "CoPaw.app"
        )
        if app_path.exists():
            print(f"📱 App: {app_path}")

        dmg_path = PROJECT_ROOT / "dist" / "CoPaw.dmg"
        if dmg_path.exists():
            print(f"💿 DMG: {dmg_path}")

    except KeyboardInterrupt:
        print("\n\n⚠️ Build cancelled by user")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\n\n❌ Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
