# CoPaw Desktop packaging scripts

One-click build: each script builds the console frontend, then uses a **temporary conda environment** and **conda-pack** (no current dev env). Dependencies follow `pyproject.toml`.

- **Windows**: console → conda-pack → unpack → NSIS installer (`.exe`)
- **macOS**: console → conda-pack → unpack into `.app` → optional zip

## Prerequisites

- **conda** (Miniconda/Anaconda) on PATH
- **Node.js / npm** (for the console frontend)
- (Windows only) **NSIS**: `makensis` on PATH
- (macOS, optional) Icon: if `scripts/pack/assets/icon.svg` exists, run `python scripts/pack/gen_icon_icns.py` once to generate `icon.icns`

## One-click build

From the **repo root**:

**macOS**
```bash
./scripts/pack/build_macos.sh
# Output: dist/CoPaw.app

CREATE_ZIP=1 ./scripts/pack/build_macos.sh   # also create dist/CoPaw-<version>-macOS.zip
```

**Windows (PowerShell)**
```powershell
./scripts/pack/build_win.ps1
# Output: dist/CoPaw-Setup-<version>.exe
```

## CI

`.github/workflows/desktop-release.yml`:

- **Triggers**: Release publish or manual workflow_dispatch
- **Windows**: Build console → temporary conda env + conda-pack → NSIS → upload artifact
- **macOS**: Build console → temporary conda env + conda-pack → .app → zip → upload artifact
- **Release**: When triggered by a release, uploads the Windows installer and macOS zip as release assets

## Script reference

| File | Description |
|------|-------------|
| `build_common.py` | Create temporary conda env, `pip install .`, conda-pack; produces archive. Used by macOS/Windows scripts. |
| `build_macos.sh` | One-click: build console → build_common → unpack into CoPaw.app; optional zip. |
| `build_win.ps1` | One-click: build console → build_common → unpack → launcher .bat → makensis installer. |
| `copaw_desktop.nsi` | NSIS script: pack `dist/win-unpacked` and create shortcuts. |
| `gen_icon_icns.py` | (macOS only) Generate `icon.icns` from `assets/icon.svg` (rounded, transparent). |
