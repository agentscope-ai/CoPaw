#!/usr/bin/env bash
# =============================================================================
# CoPaw Desktop Build Script
# =============================================================================
# Usage:
#   ./build.sh                  # Full build: frontend + sidecar + app + dmg
#   ./build.sh --skip-frontend  # Skip frontend build
#   ./build.sh --skip-sidecar   # Skip sidecar (PyInstaller) build
#   ./build.sh --no-dmg         # Build app only, skip DMG creation
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# ── Color helpers ─────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}▶ $*${NC}"; }
success() { echo -e "${GREEN}✔ $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠ $*${NC}"; }
error()   { echo -e "${RED}✘ $*${NC}"; exit 1; }
step()    { echo; echo -e "${CYAN}══════════════════════════════════════════${NC}"; echo -e "${CYAN}  $*${NC}"; echo -e "${CYAN}══════════════════════════════════════════${NC}"; }

# ── Parse args ────────────────────────────────────────────────────────────────
SKIP_FRONTEND=false
SKIP_SIDECAR=false
NO_DMG=false

for arg in "$@"; do
  case "$arg" in
    --skip-frontend) SKIP_FRONTEND=true ;;
    --skip-sidecar)  SKIP_SIDECAR=true  ;;
    --no-dmg)        NO_DMG=true        ;;
    *) error "Unknown option: $arg" ;;
  esac
done

# ── Detect architecture ───────────────────────────────────────────────────────
ARCH="$(uname -m)"
# Force ARM64 build for Apple Silicon
TARGET="aarch64-apple-darwin"
info "Forcing ARM64 build (aarch64-apple-darwin)"

sync_sidecar_binaries() {
  local src="$1"
  local dst_dir="$2"
  mkdir -p "$dst_dir"

  if [ "$(uname -s)" = "Darwin" ]; then
    # Keep both macOS target names in sync. Tauri may resolve either one
    # depending on runtime environment/toolchain architecture.
    cp "$src" "$dst_dir/copaw-backend-aarch64-apple-darwin"
    cp "$src" "$dst_dir/copaw-backend-x86_64-apple-darwin"
    chmod +x "$dst_dir/copaw-backend-aarch64-apple-darwin" "$dst_dir/copaw-backend-x86_64-apple-darwin"
    success "Sidecar → src-tauri/binaries/copaw-backend-{aarch64,x86_64}-apple-darwin"
  else
    local dst="$dst_dir/copaw-backend-$TARGET"
    cp "$src" "$dst"
    chmod +x "$dst"
    success "Sidecar → src-tauri/binaries/copaw-backend-$TARGET"
  fi
}

# ── Locate Python (prefer arm64 .venv-arm64, fallback to .venv) ───────────────
ARM64_PYTHON="/opt/homebrew/bin/python3.11"

if [ -f "$PROJECT_ROOT/.venv-arm64/bin/python" ]; then
  PYTHON="$PROJECT_ROOT/.venv-arm64/bin/python"
  info "Using arm64 venv: $PYTHON"
elif [ -f "$ARM64_PYTHON" ]; then
  warn ".venv-arm64 not found, creating from arm64 Python..."
  "$ARM64_PYTHON" -m venv "$PROJECT_ROOT/.venv-arm64"
  PYTHON="$PROJECT_ROOT/.venv-arm64/bin/python"
  "$PYTHON" -m pip install -e "$PROJECT_ROOT[dev]" -q
  info "Created arm64 venv: $PYTHON"
elif [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
  PYTHON="$PROJECT_ROOT/.venv/bin/python"
  warn "arm64 Python not found, falling back to .venv: $PYTHON"
  warn "Sidecar may not be arm64. Install arm64 Python: /opt/homebrew/bin/brew install python@3.11"
else
  warn "No venv found, creating .build-env with system Python..."
  python3 -m venv "$PROJECT_ROOT/.build-env"
  PYTHON="$PROJECT_ROOT/.build-env/bin/python"
fi

# Ensure PyInstaller is installed in the chosen Python env
if ! "$PYTHON" -m PyInstaller --version &>/dev/null; then
  info "Installing PyInstaller into Python env..."
  "$PYTHON" -m pip install pyinstaller -q
fi

# Warn if Python is not arm64
PYTHON_ARCH="$(file "$PYTHON" | grep -o 'arm64\|x86_64' | head -1)"
if [ "$PYTHON_ARCH" != "arm64" ]; then
  warn "Python ($PYTHON) is $PYTHON_ARCH — sidecar will NOT be arm64!"
else
  info "Python arch: arm64 ✔"
fi

# ── Print build info ──────────────────────────────────────────────────────────
echo
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         CoPaw Desktop Build              ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo "  Platform : $(uname -s) $ARCH → $TARGET"
echo "  Python   : $PYTHON"
echo "  Skips    : frontend=$SKIP_FRONTEND  sidecar=$SKIP_SIDECAR  dmg=$NO_DMG"

# ── Step 1: Frontend ──────────────────────────────────────────────────────────
if [ "$SKIP_FRONTEND" = false ]; then
  step "Step 1/4  Frontend (React)"
  CONSOLE_DIR="$PROJECT_ROOT/console"
  [ -d "$CONSOLE_DIR" ] || error "console/ directory not found"
  info "npm ci..."
  npm ci --prefix "$CONSOLE_DIR" --silent
  info "npm run build..."
  npm run build --prefix "$CONSOLE_DIR"
  
  # Copy loading.html to dist so Tauri can serve it in release mode
  LOADING_HTML_SRC="$PROJECT_ROOT/src-tauri/loading.html"
  LOADING_HTML_DST="$CONSOLE_DIR/dist/loading.html"
  if [ -f "$LOADING_HTML_SRC" ]; then
    cp "$LOADING_HTML_SRC" "$LOADING_HTML_DST"
    success "Copied loading.html → console/dist/"
  else
    warn "loading.html not found at $LOADING_HTML_SRC"
  fi
  
  success "Frontend built → console/dist"
else
  warn "Step 1/4  Skipping frontend build"
  [ -d "$PROJECT_ROOT/console/dist" ] || error "console/dist not found. Run without --skip-frontend first."
  # Ensure loading.html is present in console/dist even when skipping frontend build
  LOADING_HTML_SRC="$PROJECT_ROOT/src-tauri/loading.html"
  LOADING_HTML_DST="$PROJECT_ROOT/console/dist/loading.html"
  if [ -f "$LOADING_HTML_SRC" ] && [ ! -f "$LOADING_HTML_DST" ]; then
    cp "$LOADING_HTML_SRC" "$LOADING_HTML_DST"
    info "Copied loading.html → console/dist/ (was missing)"
  fi
fi

# ── Step 2: Python Sidecar (PyInstaller) ──────────────────────────────────────
if [ "$SKIP_SIDECAR" = false ]; then
  step "Step 2/4  Python Sidecar (PyInstaller)"
  SPEC_DIR="$PROJECT_ROOT/desktop/pyinstaller"
  SPEC_FILE="$SPEC_DIR/CoPawBackend.spec"
  [ -f "$SPEC_FILE" ] || error "Spec file not found: $SPEC_FILE"

  info "Running PyInstaller (this takes a few minutes)..."
  # PyInstaller must run from spec dir for relative paths (runtime_hooks/, hooks/) to work
  (cd "$SPEC_DIR" && "$PYTHON" -m PyInstaller --clean --noconfirm CoPawBackend.spec)

  SIDECAR_SRC="$SPEC_DIR/dist/copaw-backend/copaw-backend"
  [ -f "$SIDECAR_SRC" ] || error "Sidecar binary not found at $SIDECAR_SRC"
  SIDECAR_INTERNAL="$SPEC_DIR/dist/copaw-backend/_internal"
  [ -d "$SIDECAR_INTERNAL" ] || error "Sidecar _internal dir not found at $SIDECAR_INTERNAL"

  # Pre-compile Python bytecode to speed up first startup
  info "Pre-compiling Python bytecode..."
  "$PYTHON" -m compileall -q -j 0 "$SIDECAR_INTERNAL" 2>/dev/null || true
  success "Bytecode pre-compilation done"

  BINARIES_DIR="$PROJECT_ROOT/src-tauri/binaries"
  sync_sidecar_binaries "$SIDECAR_SRC" "$BINARIES_DIR"
  rm -rf "$BINARIES_DIR/_internal"
  cp -R "$SIDECAR_INTERNAL" "$BINARIES_DIR/_internal"
  
  # Write sidecar version marker to avoid unnecessary rsync on startup
  SIDE_VERSION_FILE="$BINARIES_DIR/_internal/.copaw_sidecar_version"
  SIDE_VERSION_CONTENT="$(jq -r '.version' "$PROJECT_ROOT/src-tauri/tauri.conf.json" 2>/dev/null || echo "unknown")-$(shasum -a 256 "$SIDECAR_SRC" | cut -c1-16)"
  echo "$SIDE_VERSION_CONTENT" > "$SIDE_VERSION_FILE"
  info "Wrote sidecar version marker: $SIDE_VERSION_CONTENT"
  
  success "Sidecar runtime dir → src-tauri/binaries/_internal"

  # After sidecar rebuild, ensure loading.html is in _internal/copaw/console/
  LOADING_HTML_SRC="$PROJECT_ROOT/src-tauri/loading.html"
  SIDECAR_CONSOLE_LOADING="$BINARIES_DIR/_internal/copaw/console/loading.html"
  if [ -f "$LOADING_HTML_SRC" ] && [ -d "$BINARIES_DIR/_internal/copaw/console" ]; then
    cp "$LOADING_HTML_SRC" "$SIDECAR_CONSOLE_LOADING"
    info "Copied loading.html → src-tauri/binaries/_internal/copaw/console/"
  fi
else
  warn "Step 2/4  Skipping sidecar build"
  SIDECAR_DST="$PROJECT_ROOT/src-tauri/binaries/copaw-backend-$TARGET"
  [ -f "$SIDECAR_DST" ] || error "Sidecar binary not found. Run without --skip-sidecar first."
  # Ensure loading.html is in _internal/copaw/console/ even when skipping sidecar build
  LOADING_HTML_SRC="$PROJECT_ROOT/src-tauri/loading.html"
  SIDECAR_CONSOLE_LOADING="$PROJECT_ROOT/src-tauri/binaries/_internal/copaw/console/loading.html"
  if [ -f "$LOADING_HTML_SRC" ] && [ -d "$PROJECT_ROOT/src-tauri/binaries/_internal/copaw/console" ]; then
    if [ ! -f "$SIDECAR_CONSOLE_LOADING" ] || [ "$LOADING_HTML_SRC" -nt "$SIDECAR_CONSOLE_LOADING" ]; then
      cp "$LOADING_HTML_SRC" "$SIDECAR_CONSOLE_LOADING"
      info "Copied loading.html → src-tauri/binaries/_internal/copaw/console/"
    fi
  fi
fi

# ── Step 3: Tauri App ─────────────────────────────────────────────────────────
step "Step 3/4  Tauri App (cargo build)"

# Tauri 2 embeds frontendDist via Rust macros. If loading.html was just added/updated
# in console/dist, cargo may not detect the change and skip recompilation.
# Force a recompile by touching main.rs when loading.html is newer than the binary.
MAIN_RS="$PROJECT_ROOT/src-tauri/src/main.rs"
TAURI_BIN="$PROJECT_ROOT/src-tauri/target/release/copaw"
LOADING_IN_DIST="$PROJECT_ROOT/console/dist/loading.html"
if [ -f "$LOADING_IN_DIST" ] && [ -f "$TAURI_BIN" ] && [ "$LOADING_IN_DIST" -nt "$TAURI_BIN" ]; then
  touch "$MAIN_RS"
  info "Touched main.rs to force Tauri recompile (loading.html updated)"
fi

# Source cargo env if exists (needed for non-interactive shells)
if [ -f "$HOME/.cargo/env" ]; then
    # shellcheck disable=SC1090
    . "$HOME/.cargo/env"
fi

# Check Rust installation
if ! type rustc &>/dev/null; then
    error "Rust not installed. Visit https://rustup.rs"
fi
if ! type cargo &>/dev/null; then
    error "cargo not found"
fi

info "cargo tauri build --bundles app..."
(cd "$PROJECT_ROOT" && cargo tauri build --bundles app)

APP_PATH="$PROJECT_ROOT/src-tauri/target/release/bundle/macos/CoPaw.app"
[ -d "$APP_PATH" ] || error "CoPaw.app not found after build"
success "App → $APP_PATH"

# onedir sidecar needs sibling _internal directory at runtime.
if [ -d "$PROJECT_ROOT/src-tauri/binaries/_internal" ]; then
  # Place _internal under Contents/ (not MacOS/) so codesign does not scan it
  # as part of the MacOS executable directory — which would fail because
  # _internal contains non-Mach-O runtime files (.py, .json, .pem, etc.).
  # A symlink MacOS/_internal → ../_internal lets the PyInstaller sidecar
  # still find its runtime at the expected relative path.
  rm -rf "$APP_PATH/Contents/_internal"
  cp -R "$PROJECT_ROOT/src-tauri/binaries/_internal" "$APP_PATH/Contents/_internal"

  # Symlink MacOS/_internal → ../_internal (relative, so the bundle is relocatable)
  rm -f "$APP_PATH/Contents/MacOS/_internal"
  ln -s "../_internal" "$APP_PATH/Contents/MacOS/_internal"
  success "Bundled sidecar runtime dir → CoPaw.app/Contents/_internal"

  # PyInstaller's macOS bootloader sets PYTHONHOME to Contents/Frameworks/ and
  # resolves stdlib from there. Symlink Frameworks → _internal so paths resolve.
  FRAMEWORKS_LINK="$APP_PATH/Contents/Frameworks"
  rm -rf "$FRAMEWORKS_LINK"
  ln -s "_internal" "$FRAMEWORKS_LINK"
  success "Symlinked Contents/Frameworks → _internal"
fi

# Verify sidecar inside app matches source binary to prevent stale package issues.
APP_SIDECAR="$APP_PATH/Contents/MacOS/copaw-backend"
SRC_SIDECAR="$PROJECT_ROOT/src-tauri/binaries/copaw-backend-$TARGET"
if [ -f "$APP_SIDECAR" ] && [ -f "$SRC_SIDECAR" ]; then
  APP_SHA="$(shasum -a 256 "$APP_SIDECAR" | awk '{print $1}')"
  SRC_SHA="$(shasum -a 256 "$SRC_SIDECAR" | awk '{print $1}')"
  if [ "$APP_SHA" != "$SRC_SHA" ]; then
    error "Sidecar hash mismatch: app=$APP_SHA src=$SRC_SHA (stale sidecar detected)"
  fi
  success "Sidecar hash verified: $APP_SHA"
fi

# ── Code Signing ──────────────────────────────────────────────────────────────
# Sign all binaries with ad-hoc signature to ensure they can run on other Macs.
# Without proper signing, Gatekeeper will block the app on other machines.
step "Code Signing"

ENTITLEMENTS_FILE="$PROJECT_ROOT/desktop/entitlements.plist"
if [ ! -f "$ENTITLEMENTS_FILE" ]; then
  warn "Entitlements file not found at $ENTITLEMENTS_FILE, using default signing"
  ENTITLEMENTS_FILE=""
fi

# Function to sign a single binary
sign_binary() {
  local binary="$1"
  local opts="--force --sign - --timestamp=none"
  if [ -n "$ENTITLEMENTS_FILE" ]; then
    opts="$opts --entitlements \"$ENTITLEMENTS_FILE\""
  fi
  # Use eval to handle spaces in paths correctly
  eval codesign $opts \"\$binary\" 2>/dev/null || true
}

# Sign all dylibs and so files in _internal
info "Signing dylibs and shared libraries..."
find "$APP_PATH/Contents/_internal" -type f \( -name "*.dylib" -o -name "*.so" \) -print0 2>/dev/null | \
  sort -z -r | while IFS= read -r -d '' lib; do
    sign_binary "$lib"
done
success "Signed all embedded libraries"

# Sign the sidecar binary
info "Signing sidecar binary..."
sign_binary "$APP_PATH/Contents/MacOS/copaw-backend"
success "Signed sidecar"

# Sign the main Tauri binary (as a standalone Mach-O, not bundle context)
# This clears the linker-signed flag that would require a full _CodeSignature
info "Signing main binary..."
TMP_COPAW="/tmp/copaw_sign_$$"
cp "$APP_PATH/Contents/MacOS/copaw" "$TMP_COPAW"
codesign --force --sign - --timestamp=none \
  ${ENTITLEMENTS_FILE:+--entitlements "$ENTITLEMENTS_FILE"} \
  "$TMP_COPAW" 2>/dev/null || true
cp "$TMP_COPAW" "$APP_PATH/Contents/MacOS/copaw"
chmod +x "$APP_PATH/Contents/MacOS/copaw"
rm -f "$TMP_COPAW"
success "Signed main binary"

# Remove CSResourcesFileMapped from Info.plist so codesign does not expect
# a resource seal that we cannot satisfy with an unsigned _internal tree.
INFO_PLIST="$APP_PATH/Contents/Info.plist"
plutil -remove CSResourcesFileMapped "$INFO_PLIST" 2>/dev/null || true

# Sign the entire app bundle.
# _internal now lives at Contents/_internal (not MacOS/_internal), so codesign
# only sees the two Mach-O binaries inside MacOS/ and correctly seals the bundle.
info "Signing app bundle..."
codesign --force --sign - --timestamp=none \
  ${ENTITLEMENTS_FILE:+--entitlements "$ENTITLEMENTS_FILE"} \
  "$APP_PATH" 2>&1 || true

# Verify signature
if codesign --verify --deep --strict "$APP_PATH" 2>/dev/null; then
  success "App bundle signed and verified"
else
  warn "App bundle signature verification had issues, but continuing"
fi

# ── Step 4: DMG ───────────────────────────────────────────────────────────────
if [ "$NO_DMG" = false ]; then
  step "Step 4/4  DMG Installer (hdiutil)"
  mkdir -p "$PROJECT_ROOT/dist"
  DMG_NAME="CoPaw-arm64.dmg"
  DMG_PATH="$PROJECT_ROOT/dist/$DMG_NAME"
  TEMP_DMG_PATH="$PROJECT_ROOT/dist/CoPaw-arm64-tmp.dmg"
  STAGING_DIR="$(mktemp -d "$PROJECT_ROOT/dist/dmg-staging.XXXXXX")"
  VOLUME_NAME="CoPaw Installer"
  DMG_BG_NAME="dmg-background.png"
  DMG_BG_SRC="$PROJECT_ROOT/src-tauri/$DMG_BG_NAME"
  VOLUME_ICON_SRC="$PROJECT_ROOT/src-tauri/icons/icon.icns"

  [ -f "$DMG_PATH" ] && rm -f "$DMG_PATH"
  [ -f "$TEMP_DMG_PATH" ] && rm -f "$TEMP_DMG_PATH"
  rm -rf "$STAGING_DIR"
  mkdir -p "$STAGING_DIR"

  APP_BASENAME="$(basename "$APP_PATH")"
  APP_NAME="${APP_BASENAME%.app}"

  info "Preparing DMG staging folder..."
  cp -R "$APP_PATH" "$STAGING_DIR/$APP_BASENAME"
  ln -s /Applications "$STAGING_DIR/Applications"
  if [ -f "$VOLUME_ICON_SRC" ]; then
    cp "$VOLUME_ICON_SRC" "$STAGING_DIR/.VolumeIcon.icns"
  fi

  info "Creating writable DMG..."
  hdiutil create \
    -volname "$VOLUME_NAME" \
    -srcfolder "$STAGING_DIR" \
    -ov -format UDRW \
    "$TEMP_DMG_PATH"

  info "Configuring Finder layout..."
  ATTACH_LOG="$(hdiutil attach -readwrite -noverify -noautoopen "$TEMP_DMG_PATH")"
  DEVICE_NAME="$(echo "$ATTACH_LOG" | awk '/^\/dev\/disk/ {print $1; exit}')"
  MOUNT_POINT="$(echo "$ATTACH_LOG" | awk '/\/Volumes\// {print substr($0, index($0, "/Volumes/")); exit}')"
  MOUNT_NAME="$(basename "$MOUNT_POINT")"

  if [ -z "$DEVICE_NAME" ] || [ -z "$MOUNT_NAME" ] || [ ! -d "$MOUNT_POINT" ]; then
    error "Failed to mount temporary DMG for customization"
  fi

  mkdir -p "$MOUNT_POINT/.background"
  if [ -f "$DMG_BG_SRC" ]; then
    cp "$DMG_BG_SRC" "$MOUNT_POINT/.background/$DMG_BG_NAME"
  else
    warn "DMG background image not found at $DMG_BG_SRC"
  fi

  if [ -f "$VOLUME_ICON_SRC" ]; then
    if [ ! -f "$MOUNT_POINT/.VolumeIcon.icns" ]; then
      cp "$VOLUME_ICON_SRC" "$MOUNT_POINT/.VolumeIcon.icns"
    fi
    if command -v SetFile >/dev/null 2>&1; then
      SetFile -a C "$MOUNT_POINT" || true
      SetFile -a V "$MOUNT_POINT/.VolumeIcon.icns" || true
    else
      warn "SetFile not found, skipped custom volume icon flag"
    fi
  else
    warn "Volume icon source not found at $VOLUME_ICON_SRC"
  fi

osascript <<EOF
tell application "Finder"
  tell disk "$MOUNT_NAME"
    open
    set current view of container window to icon view
    set toolbar visible of container window to false
    set statusbar visible of container window to false
    set the bounds of container window to {100, 100, 1300, 900}
    set viewOptions to the icon view options of container window
    set arrangement of viewOptions to not arranged
    set icon size of viewOptions to 128
    set bgAlias to (POSIX file "$MOUNT_POINT/.background/$DMG_BG_NAME") as alias
    set background picture of viewOptions to bgAlias
    if exists item "$APP_BASENAME" then
      set position of item "$APP_BASENAME" to {180, 220}
    end if
    if exists item "Applications" then
      set position of item "Applications" to {980, 220}
    end if
    close
    open
    update without registering applications
    delay 2
  end tell
end tell
EOF

  sync
  hdiutil detach "$DEVICE_NAME"
  hdiutil convert "$TEMP_DMG_PATH" -format UDZO -imagekey zlib-level=9 -o "$DMG_PATH"
  rm -f "$TEMP_DMG_PATH"
  rm -rf "$STAGING_DIR"

  # Keep output naming aligned with existing scripts/users.
  if [ "$APP_NAME" != "CoPaw" ]; then
    warn "DMG contains app name '$APP_NAME' (expected CoPaw)"
  fi
  success "DMG → dist/$DMG_NAME"
else
  warn "Step 4/4  Skipping DMG creation"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           BUILD COMPLETE                 ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
[ -d "$APP_PATH" ]               && echo -e "  App  : ${GREEN}$APP_PATH${NC}"
[ -f "$PROJECT_ROOT/dist/CoPaw-arm64.dmg" ] && echo -e "  DMG  : ${GREEN}$PROJECT_ROOT/dist/CoPaw-arm64.dmg${NC}"
echo
