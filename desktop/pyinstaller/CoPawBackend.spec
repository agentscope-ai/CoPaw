# -*- coding: utf-8 -*-
"""PyInstaller spec file for CoPaw backend."""
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Project root
PROJECT_ROOT = Path(SPECPATH).parent.parent  # noqa: F821

block_cipher = None

# ============================================================================
# Collect data files
# ============================================================================
datas = []

# Console static files (frontend build output)
console_dist = PROJECT_ROOT / "console" / "dist"
if console_dist.exists():
    datas.append((str(console_dist), "copaw/console"))
else:
    print(f"Warning: Console dist not found at {console_dist}")
    print("Please build the frontend first: cd console && npm run build")

# Agent MD files and skills
agents_dir = PROJECT_ROOT / "src" / "copaw" / "agents"
if agents_dir.exists():
    md_files = agents_dir / "md_files"
    if md_files.exists():
        datas.append((str(md_files), "copaw/agents/md_files"))
    skills = agents_dir / "skills"
    if skills.exists():
        datas.append((str(skills), "copaw/agents/skills"))

# Tokenizer files
tokenizer_dir = PROJECT_ROOT / "src" / "copaw" / "tokenizer"
if tokenizer_dir.exists():
    datas.append((str(tokenizer_dir), "copaw/tokenizer"))

# ============================================================================
# Hidden imports
# ============================================================================
hiddenimports = [
    # Uvicorn components
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    # FastAPI
    "fastapi",
    "pydantic",
    # CLI
    "click",
    # Core packages
    "agentscope",
    "agentscope_runtime",
    "tokenizers",
    # Playwright (Python bindings only; driver downloaded at runtime)
    "playwright",
    "playwright.async_api",
    "playwright.sync_api",
    # Others
    "mss",
    "PIL",
    "dingtalk_stream",
    "lark_oapi",
    "discord",
    "apscheduler",
    "apscheduler.schedulers.asyncio",
    "apscheduler.triggers.cron",
    "apscheduler.triggers.interval",
    "apscheduler.executors.pool",
    "apscheduler.jobstores.memory",
    # HTTP client
    "httpx",
    "httpcore",
    "h11",
    "anyio",
    # Config
    "dotenv",
    "pydantic_settings",
]

# Collect all submodules for key packages
for pkg in ["agentscope", "agentscope_runtime", "copaw"]:
    try:
        hiddenimports.extend(collect_submodules(pkg))
    except Exception as e:
        print(f"Warning: Could not collect submodules for {pkg}: {e}")

# ============================================================================
# Analysis
# ============================================================================
# Use absolute paths to avoid directory confusion
spec_dir = Path(SPECPATH)  # noqa: F821
a = Analysis(
    [str(spec_dir / "entry_point.py")],
    pathex=[str(PROJECT_ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(spec_dir / "hooks")],
    hooksconfig={},
    runtime_hooks=[str(spec_dir / "runtime_hooks" / "setup_paths.py")],
    excludes=[
        "tkinter",
        "matplotlib",
        "notebook",
        "jupyter",
        "IPython",
        "pytest",
        "sphinx",
        # Heavy packages replaced by lightweight alternatives
        "transformers",
        "onnxruntime",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================================================
# Post-analysis: strip heavy runtime blobs that are not needed at package time
# ============================================================================
import shutil as _shutil

def _strip_playwright_driver(module_table):
    """Remove Playwright's bundled Node.js binary (~112 MB) from datas.

    The driver is downloaded at runtime via `playwright install`."""
    cleaned = []
    for dest, source, typecode in module_table:
        # playwright/driver/node is the 112 MB Node.js binary
        if "playwright" in dest and ("driver/node" in dest or "driver\\node" in dest):
            print(f"  [strip] excluding playwright driver blob: {dest}")
            continue
        cleaned.append((dest, source, typecode))
    return cleaned

a.datas = _strip_playwright_driver(a.datas)
a.binaries = _strip_playwright_driver(a.binaries)

# ============================================================================
# PYZ Archive
# ============================================================================
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ============================================================================
# Executable
# ============================================================================
exe = EXE(
    pyz,
    a.scripts,
    [],
    name="copaw-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging; set False for production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=str(PROJECT_ROOT / "desktop" / "entitlements.plist")
    if (PROJECT_ROOT / "desktop" / "entitlements.plist").exists()
    else None,
    exclude_binaries=True,
)

# Build in onedir mode to avoid onefile extraction cold-start latency.
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="copaw-backend",
)
