#!/usr/bin/env bash
# Build CoPaw as a macOS .app and DMG for distribution.
# Run from repo root: bash scripts/macos/build_dmg.sh [version]
#
# Prerequisites (on build machine):
#   - macOS (for building .app / DMG)
#   - Node.js (for console frontend)
#   - Python 3.10+ with venv
#   - pip install pyinstaller (and project deps)
#
# Output: dist/CoPaw-<version>.dmg (and dist/CoPaw.app)
# Compatible with macOS 10.15 (Catalina) and later (Intel & Apple Silicon).

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# Version: from arg (strip leading 'v' if present), or from copaw, or default
VERSION="${1:-}"
VERSION="${VERSION#v}"
if [[ -z "$VERSION" ]]; then
  VERSION=$(python3 -c "from src.copaw.__version__ import __version__; print(__version__)" 2>/dev/null || echo "0.0.0")
fi

CONSOLE_DIR="$REPO_ROOT/console"
CONSOLE_DEST="$REPO_ROOT/src/copaw/console"
DIST_DIR="$REPO_ROOT/dist"
APP_NAME="CoPaw"
DMG_NAME="${APP_NAME}-${VERSION}"
MACOSX_DEPLOYMENT_TARGET="${MACOSX_DEPLOYMENT_TARGET:-10.15}"

echo "[build_dmg] Version: $VERSION"
echo "[build_dmg] MACOSX_DEPLOYMENT_TARGET: $MACOSX_DEPLOYMENT_TARGET"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "[build_dmg] ERROR: This script must run on macOS." >&2
  exit 1
fi

# --- Build console frontend ---
echo "[build_dmg] Building console frontend..."
if [[ ! -f "$CONSOLE_DIR/package.json" ]]; then
  echo "[build_dmg] ERROR: console/package.json not found." >&2
  exit 1
fi
(cd "$CONSOLE_DIR" && npm ci)
(cd "$CONSOLE_DIR" && npm run build)

echo "[build_dmg] Copying console/dist -> src/copaw/console ..."
rm -rf "$CONSOLE_DEST"
mkdir -p "$CONSOLE_DEST"
cp -R "$CONSOLE_DIR/dist/"* "$CONSOLE_DEST/"

if [[ ! -f "$CONSOLE_DEST/index.html" ]]; then
  echo "[build_dmg] ERROR: console build did not produce index.html." >&2
  exit 1
fi

# --- Python env: use venv if present, else current interpreter ---
if [[ -d "$REPO_ROOT/.venv" ]]; then
  PYTHON="$REPO_ROOT/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi
echo "[build_dmg] Using Python: $PYTHON"

# Ensure pip is available (e.g. venv created with --without-pip)
if ! "$PYTHON" -m pip --version &>/dev/null; then
  echo "[build_dmg] Bootstrapping pip with ensurepip..."
  "$PYTHON" -m ensurepip --upgrade
fi
PIP_CMD=("$PYTHON" -m pip)

# --- Install project + PyInstaller ---
"${PIP_CMD[@]}" install --quiet -e ".[dev]"
"${PIP_CMD[@]}" install --quiet pyinstaller

# --- PyInstaller one-dir bundle ---
export MACOSX_DEPLOYMENT_TARGET
rm -rf "$REPO_ROOT/build" "$DIST_DIR/$APP_NAME"
"$PYTHON" -m PyInstaller --noconfirm --clean "scripts/macos/copaw.spec"

PYINSTALLER_OUT="$DIST_DIR/$APP_NAME"
if [[ ! -f "$PYINSTALLER_OUT/$APP_NAME" ]]; then
  echo "[build_dmg] ERROR: PyInstaller did not produce $PYINSTALLER_OUT/$APP_NAME" >&2
  exit 1
fi

# --- Wrap in .app bundle ---
# Rename PyInstaller binary so we can use a shell script as the app executable
# (script runs: exec CoPaw_bin app --host 0.0.0.0)
APP_DIR="$DIST_DIR/${APP_NAME}.app"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

mv "$PYINSTALLER_OUT/$APP_NAME" "$PYINSTALLER_OUT/${APP_NAME}_bin"
cp -R "$PYINSTALLER_OUT/"* "$APP_DIR/Contents/MacOS/"

# Launcher script: set working dir, run init on first launch, then start server
LAUNCHER="$APP_DIR/Contents/MacOS/$APP_NAME"
cat > "$LAUNCHER" << 'LAUNCHER_SCRIPT'
#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
export COPAW_WORKING_DIR="${HOME}/Library/Application Support/CoPaw"
if [[ ! -f "$COPAW_WORKING_DIR/config.json" ]]; then
  "$DIR/CoPaw_bin" init --defaults --accept-security
fi
exec "$DIR/CoPaw_bin" app --host 0.0.0.0
LAUNCHER_SCRIPT
chmod +x "$LAUNCHER"

# Info.plist for .app
cat > "$APP_DIR/Contents/Info.plist" << INFOPLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>CoPaw</string>
  <key>CFBundleIdentifier</key>
  <string>ai.agentscope.copaw</string>
  <key>CFBundleName</key>
  <string>CoPaw</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>${VERSION}</string>
  <key>CFBundleVersion</key>
  <string>${VERSION}</string>
  <key>LSMinimumSystemVersion</key>
  <string>${MACOSX_DEPLOYMENT_TARGET}</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
INFOPLIST

# Remove raw PyInstaller output dir so we only have .app
rm -rf "$PYINSTALLER_OUT"

echo "[build_dmg] Created $APP_DIR"

# --- Create DMG ---
DMG_PATH="$DIST_DIR/${DMG_NAME}.dmg"
# Use create-dmg if available (brew install create-dmg), else hdiutil
if command -v create-dmg &>/dev/null; then
  echo "[build_dmg] Creating DMG with create-dmg..."
  rm -f "$DMG_PATH"
  create-dmg \
    --volname "CoPaw $VERSION" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --app-drop-link 450 200 \
    --no-internet-enable \
    "$DMG_PATH" \
    "$APP_DIR"
else
  echo "[build_dmg] create-dmg not found, using hdiutil (plain DMG)."
  echo "  Install with: brew install create-dmg"
  TMP_DMG="$DIST_DIR/tmp_${DMG_NAME}.dmg"
  rm -f "$TMP_DMG" "$DMG_PATH"
  hdiutil create -volname "CoPaw $VERSION" -srcfolder "$APP_DIR" -ov -format UDZO "$TMP_DMG"
  mv "$TMP_DMG" "$DMG_PATH"
fi

echo "[build_dmg] Done."
echo "  App:  $APP_DIR"
echo "  DMG:  $DMG_PATH"
