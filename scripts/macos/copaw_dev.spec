# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for CoPaw macOS .app **Dev** variant (console=True for logs).
# Run from repo root: pyinstaller scripts/macos/copaw_dev.spec

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

REPO_ROOT = Path.cwd().resolve()
_SPEC_DIR = REPO_ROOT / "scripts" / "macos"
CONSOLE_STATIC = REPO_ROOT / "src" / "copaw" / "console"
MD_FILES_SRC = REPO_ROOT / "src" / "copaw" / "agents" / "md_files"
SKILLS_SRC = REPO_ROOT / "src" / "copaw" / "agents" / "skills"
TOKENIZER_SRC = REPO_ROOT / "src" / "copaw" / "tokenizer"
_DEV_LAUNCHER = _SPEC_DIR / "dev_gui_launcher.py"

_console_datas = (
    [(str(CONSOLE_STATIC), "copaw/console")] if CONSOLE_STATIC.is_dir() else []
)
_md_datas = (
    [(str(MD_FILES_SRC), "copaw/agents/md_files")] if MD_FILES_SRC.is_dir() else []
)
_skills_datas = (
    [(str(SKILLS_SRC), "copaw/agents/skills")] if SKILLS_SRC.is_dir() else []
)
_tokenizer_datas = (
    [(str(TOKENIZER_SRC), "copaw/tokenizer")] if TOKENIZER_SRC.is_dir() else []
)
try:
    _reme_hidden = ["reme"] + list(collect_submodules("reme"))
except Exception:
    _reme_hidden = ["reme"]

a = Analysis(
    [str(_DEV_LAUNCHER)],
    pathex=[str(REPO_ROOT), str(REPO_ROOT / "src"), str(_SPEC_DIR)],
    binaries=[],
    datas=_console_datas + _md_datas + _skills_datas + _tokenizer_datas,
    hiddenimports=collect_submodules("copaw")
    + _reme_hidden
    + [
        "webview",
        "pyobjc",
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
    name="CoPaw-Dev",
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
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="CoPaw-Dev",
)
