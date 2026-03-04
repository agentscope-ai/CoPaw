# CoPaw Desktop App

This directory contains the Tauri-based desktop application wrapper for CoPaw.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CoPaw.app                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Tauri (Rust) Shell                      │   │
│  │  • Manages WebView window                           │   │
│  │  • Starts/stops Python Sidecar                      │   │
│  │  • Handles app lifecycle                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Python Sidecar (copaw-backend)             │   │
│  │  • FastAPI + Uvicorn (127.0.0.1:8088)               │   │
│  │  • All business logic and AI Agent                  │   │
│  │  • Serves React frontend                           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Rust**: Install from https://rustup.rs/
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Tauri CLI**:
   ```bash
   cargo install tauri-cli
   ```

3. **PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

## Building

### Full Build

```bash
# From project root
python scripts/desktop_build.py --dmg
```

### Development Build

```bash
# Build sidecar only (for testing backend changes)
./scripts/build_sidecar.sh

# Run Tauri in dev mode
cargo tauri dev
```

### Step-by-Step Build

1. **Build frontend**:
   ```bash
   cd console && npm run build
   cp -r dist/* ../src/copaw/console/
   ```

2. **Build Python sidecar**:
   ```bash
   python -m PyInstaller --clean --noconfirm desktop/pyinstaller/CoPawBackend.spec
   ```

3. **Copy sidecar to Tauri**:
   ```bash
   # For Apple Silicon
   cp dist/copaw-backend/copaw-backend src-tauri/binaries/copaw-backend-aarch64-apple-darwin

   # For Intel Mac
   cp dist/copaw-backend/copaw-backend src-tauri/binaries/copaw-backend-x86_64-apple-darwin
   ```

4. **Build Tauri app**:
   ```bash
   cargo tauri build
   ```

## Output

- **App Bundle**: `src-tauri/target/release/bundle/macos/CoPaw.app`
- **DMG Installer**: `dist/CoPaw.dmg`

## Configuration

- `tauri.conf.json` - Tauri configuration
- `entitlements/app.entitlements` - macOS permissions
- `splash.html` - Loading screen shown while backend starts

## Code Signing (Optional)

To distribute the app to other users, you need to sign and notarize it:

```bash
# Sign the app
codesign --force --deep --sign "Developer ID Application: Your Name (TEAM_ID)" \
    --options runtime \
    --entitlements entitlements/app.entitlements \
    src-tauri/target/release/bundle/macos/CoPaw.app

# Create and sign DMG
hdiutil create -volname "CoPaw" -srcfolder src-tauri/target/release/bundle/macos/CoPaw.app \
    -ov -format UDZO dist/CoPaw.dmg
codesign --sign "Developer ID Application: Your Name (TEAM_ID)" dist/CoPaw.dmg

# Notarize
xcrun notarytool submit dist/CoPaw.dmg \
    --apple-id "your@email.com" \
    --team-id "TEAM_ID" \
    --password "@keychain:AC_PASSWORD" \
    --wait

# Staple
xcrun stapler staple dist/CoPaw.dmg
```

## Troubleshooting

### "Sidecar not found"
Make sure you've built the Python sidecar and copied it to `src-tauri/binaries/` with the correct architecture-specific name.

### "Backend failed to start"
Check the console output for errors. The backend logs are printed to stdout/stderr.

### Large app size
The app includes Python runtime and all dependencies. To reduce size:
- Use `--exclude-module` in PyInstaller spec to remove unused packages
- Consider downloading Playwright browsers on first run instead of bundling
