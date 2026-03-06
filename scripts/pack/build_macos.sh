#!/usr/bin/env bash
# One-click build: console -> conda-pack -> CoPaw.app. Run from repo root.
# Requires: conda, node/npm (for console). Optional: icon.icns in assets/.

set -e
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
PACK_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST="${DIST:-dist}"
ARCHIVE="${DIST}/copaw-env.tar.gz"
APP_NAME="CoPaw"
APP_DIR="${DIST}/${APP_NAME}.app"

echo "== Building wheel (includes console frontend) =="
# Skip wheel_build if dist already has a wheel for current version
VERSION_FILE="${REPO_ROOT}/src/copaw/__version__.py"
CURRENT_VERSION=""
if [[ -f "${VERSION_FILE}" ]]; then
  CURRENT_VERSION="$(
    sed -n 's/^__version__[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' \
      "${VERSION_FILE}" 2>/dev/null
  )"
fi
if [[ -n "${CURRENT_VERSION}" ]]; then
  shopt -s nullglob
  whls=("${REPO_ROOT}/dist/copaw-${CURRENT_VERSION}-"*.whl)
  if [[ ${#whls[@]} -gt 0 ]]; then
    echo "dist/ already has wheel for version ${CURRENT_VERSION}, skipping."
  else
    bash scripts/wheel_build.sh
  fi
else
  bash scripts/wheel_build.sh
fi

echo "== Building conda-packed env =="
python "${PACK_DIR}/build_common.py" --output "$ARCHIVE" --format tar.gz

echo "== Building .app bundle =="
rm -rf "$APP_DIR"
mkdir -p "${APP_DIR}/Contents/MacOS"
mkdir -p "${APP_DIR}/Contents/Resources"

# Unpack conda env into Resources/env
mkdir -p "${APP_DIR}/Contents/Resources/env"
tar -xzf "$ARCHIVE" -C "${APP_DIR}/Contents/Resources/env" --strip-components=0

# Fix paths for portability (required or app will crash on launch)
if [[ -x "${APP_DIR}/Contents/Resources/env/bin/conda-unpack" ]]; then
  (cd "${APP_DIR}/Contents/Resources/env" && ./bin/conda-unpack)
fi

# Launcher: force packed env; when no TTY log to ~/.copaw/desktop.log (no exec so we see errors)
cat > "${APP_DIR}/Contents/MacOS/${APP_NAME}" << 'LAUNCHER'
#!/usr/bin/env bash
ENV_DIR="$(cd "$(dirname "$0")/../Resources/env" && pwd)"
LOG="$HOME/.copaw/desktop.log"
unset PYTHONPATH
export PYTHONHOME="$ENV_DIR"
export COPAW_DESKTOP_APP=1
cd "$HOME" || true
if [ ! -t 2 ]; then
  mkdir -p "$HOME/.copaw"
  { echo "=== $(date) CoPaw starting ==="
    echo "ENV_DIR=$ENV_DIR"
    echo "Python: $ENV_DIR/bin/python (exists=$([ -x "$ENV_DIR/bin/python" ] && echo yes || echo no))"
  } >> "$LOG"
  exec 2>> "$LOG"
  exec 1>> "$LOG"
  if [ ! -x "$ENV_DIR/bin/python" ]; then
    echo "ERROR: python not executable at $ENV_DIR/bin/python"
    exit 1
  fi
  if [ ! -f "$HOME/.copaw/config.json" ]; then
    "$ENV_DIR/bin/python" -u -m copaw init --defaults --accept-security
  fi
  echo "Launching python..."
  "$ENV_DIR/bin/python" -u -m copaw desktop
  EXIT=$?
  if [ $EXIT -ge 128 ]; then
    SIG=$((EXIT - 128))
    echo "Exit code: $EXIT (killed by signal $SIG, e.g. 9=SIGKILL 15=SIGTERM)"
  else
    echo "Exit code: $EXIT"
  fi
  echo "--- Full log: $LOG (scroll up for Python traceback if app exited early) ---"
  exit $EXIT
fi
if [ ! -f "$HOME/.copaw/config.json" ]; then
  "$ENV_DIR/bin/python" -u -m copaw init --defaults --accept-security
fi
exec "$ENV_DIR/bin/python" -u -m copaw desktop
LAUNCHER
chmod +x "${APP_DIR}/Contents/MacOS/${APP_NAME}"

# Icon: generate icon.icns from icon.svg if missing (macOS only)
if [[ -f "${PACK_DIR}/assets/icon.svg" ]] && [[ ! -f "${PACK_DIR}/assets/icon.icns" ]]; then
  echo "== Generating icon.icns from icon.svg =="
  python "${PACK_DIR}/gen_icon_icns.py" || echo "Warning: gen_icon_icns.py failed, app will have no icon."
fi

# Info.plist (include icon key if icon.icns exists)
VERSION="$("${APP_DIR}/Contents/Resources/env/bin/python" -c \
  "from importlib.metadata import version; print(version('copaw'))" 2>/dev/null \
  || echo "0.0.0")"
ICON_PLIST=""
if [[ -f "${PACK_DIR}/assets/icon.icns" ]]; then
  cp "${PACK_DIR}/assets/icon.icns" "${APP_DIR}/Contents/Resources/"
  ICON_PLIST="<key>CFBundleIconFile</key><string>icon.icns</string>
  "
fi
cat > "${APP_DIR}/Contents/Info.plist" << INFOPLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" \
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key><string>${APP_NAME}</string>
  <key>CFBundleIdentifier</key><string>com.copaw.desktop</string>
  <key>CFBundleName</key><string>${APP_NAME}</string>
  <key>CFBundleVersion</key><string>${VERSION}</string>
  <key>CFBundleShortVersionString</key><string>${VERSION}</string>
  ${ICON_PLIST}<key>NSHighResolutionCapable</key><true/>
  <key>LSMinimumSystemVersion</key><string>10.13</string>
  <key>NSDesktopFolderUsageDescription</key><string>CoPaw may access files in your Desktop folder if you use file-related features. You can choose Don'\''t Allow; the app will still run with limited file access.</string>
</dict>
</plist>
INFOPLIST

echo "== Built ${APP_DIR} =="
# Optional: create zip and DMG for distribution (set CREATE_ZIP=1)
if [[ -n "${CREATE_ZIP}" ]]; then
  ZIP_NAME="${DIST}/CoPaw-${VERSION}-macOS.zip"
  ditto -c -k --sequesterRsrc --keepParent "${APP_DIR}" "${ZIP_NAME}"
  echo "== Created ${ZIP_NAME} =="
  DMG_NAME="${DIST}/CoPaw-${VERSION}-macOS.dmg"
  hdiutil create -volname "CoPaw ${VERSION}" -srcfolder "${APP_DIR}" \
    -ov -format UDZO "${DMG_NAME}"
  echo "== Created ${DMG_NAME} =="
fi
