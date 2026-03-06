#!/usr/bin/env bash
# One-click build: console -> conda-pack -> CoPaw.app. Run from repo root.
# Requires: conda, node/npm (for console). Optional: icon.icns in assets/.

set -e
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
PACK_DIR="$(dirname "$0")"
DIST="${DIST:-dist}"
ARCHIVE="${DIST}/copaw-env.tar.gz"
APP_NAME="CoPaw"
APP_DIR="${DIST}/${APP_NAME}.app"

echo "== Building console frontend =="
if [[ -f "console/package.json" ]]; then
  (cd console && npm ci && npm run build)
  rm -rf src/copaw/console
  mkdir -p src/copaw/console
  cp -R console/dist/* src/copaw/console/
else
  echo "Warning: console/ not found; packing without web console." >&2
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

# Launcher: use env's python -m so we never pick up system conda
cat > "${APP_DIR}/Contents/MacOS/${APP_NAME}" << 'LAUNCHER'
#!/usr/bin/env bash
exec "$(dirname "$0")/../Resources/env/bin/python" -m copaw.cli.main desktop
LAUNCHER
chmod +x "${APP_DIR}/Contents/MacOS/${APP_NAME}"

# Info.plist
VERSION="$("${APP_DIR}/Contents/Resources/env/bin/python" -c \
  "from importlib.metadata import version; print(version('copaw'))" 2>/dev/null \
  || echo "0.0.0")"
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
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
INFOPLIST

# Icon: generate from icon.svg if needed, then copy into app
if [[ -f "${PACK_DIR}/assets/icon.svg" ]] && [[ ! -f "${PACK_DIR}/assets/icon.icns" ]]; then
  python "${PACK_DIR}/gen_icon_icns.py" || true
fi
if [[ -f "${PACK_DIR}/assets/icon.icns" ]]; then
  cp "${PACK_DIR}/assets/icon.icns" "${APP_DIR}/Contents/Resources/"
  /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string icon.icns" \
    "${APP_DIR}/Contents/Info.plist" 2>/dev/null || true
fi

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
