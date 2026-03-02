# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for CoPaw macOS .app (used by scripts/macos/build_dmg.sh).
# Run from repo root: pyinstaller scripts/macos/copaw.spec
#
# Console static files must exist at src/copaw/console (build script copies
# console/dist there before running PyInstaller).

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

# Build script runs PyInstaller from repo root, so cwd is repo root.
REPO_ROOT = Path.cwd().resolve()
_SPEC_DIR = REPO_ROOT / "scripts" / "macos"
CONSOLE_STATIC = REPO_ROOT / "src" / "copaw" / "console"
_LAUNCHER = _SPEC_DIR / "launcher.py"

_console_datas = (
    [(str(CONSOLE_STATIC), "copaw/console")] if CONSOLE_STATIC.is_dir() else []
)

a = Analysis(
    [str(_LAUNCHER)],
    pathex=[str(REPO_ROOT), str(REPO_ROOT / "src")],
    binaries=[],
    datas=_console_datas,
    hiddenimports=collect_submodules("copaw")
    + [
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
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CoPaw",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
# One-dir: COLLECT gathers binaries/datas into dist/CoPaw/.

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="CoPaw",
)
