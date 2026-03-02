# macOS DMG packaging

Build CoPaw as a macOS `.app` and DMG for distribution.

## Files

- **`build_dmg.sh`** – Main build script. Run from repo root: `bash scripts/macos/build_dmg.sh [version]`
- **`launcher.py`** – PyInstaller entry point (runs `copaw app --host 0.0.0.0`)
- **`copaw.spec`** – PyInstaller spec (one-dir bundle + console static)

## Prerequisites

- macOS
- Node.js (for console frontend)
- Python 3.10+ and `pip install pyinstaller` (and project deps)
- Optional: `brew install create-dmg` for a nicer DMG

## Output

- `dist/CoPaw.app`
- `dist/CoPaw-<version>.dmg`

Compatible with macOS 10.15 (Catalina) and later. On release, the workflow `.github/workflows/release-macos-dmg.yml` builds the DMG and attaches it to the GitHub Release.

## First launch (DMG app)

The app uses **`~/Library/Application Support/CoPaw`** as the working directory. On first run, the launcher automatically runs `copaw init --defaults --accept-security` to create `config.json`, `HEARTBEAT.md`, and enable default skills, then starts the server. No manual init step is required after installing from DMG.
