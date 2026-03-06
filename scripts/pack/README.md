# CoPaw Desktop packaging scripts

Uses a **temporary conda environment** and **conda-pack**; does not depend on the current dev environment.

- **Windows**: conda-pack → unpack → NSIS installer (`.exe`)
- **macOS**: conda-pack → unpack into `.app` → optional zip

Dependencies follow `pyproject.toml`. Build the console frontend and copy it into `src/copaw/console/` before packing.

## Local build

### Prerequisites

- Miniconda/Anaconda installed, `conda` on PATH
- (Windows) NSIS installed, `makensis` on PATH
- (macOS) Optional: if `scripts/pack/assets/icon.svg` exists (rounded, transparent; from copaw-symbol), run `python scripts/pack/gen_icon_icns.py` to generate `icon.icns`

### Build console (required)

```bash
cd console && npm ci && npm run build
# Copy into package
rm -rf ../src/copaw/console && mkdir -p ../src/copaw/console
cp -R dist/* ../src/copaw/console/
cd ..
```

### macOS

```bash
./scripts/pack/build_macos.sh
# Output: dist/CoPaw.app

# Also create zip
CREATE_ZIP=1 ./scripts/pack/build_macos.sh
# Output: dist/CoPaw.app, dist/CoPaw-<version>-macOS.zip
```

### Windows (PowerShell)

```powershell
# After building console and copying to src/copaw/console, run:
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
| `build_macos.sh` | Run build_common → unpack into CoPaw.app, write Info.plist and launcher; optional zip. |
| `build_win.ps1` | Run build_common → unpack → write desktop launcher .bat → run makensis to build installer. |
| `copaw_desktop.nsi` | NSIS script: pack `dist/win-unpacked` and create shortcuts. |
| `gen_icon_icns.py` | (macOS only) Generate `icon.icns` from `assets/icon.svg` (rounded, transparent). |
