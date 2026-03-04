#!/usr/bin/env bash
# Build CoPaw sidecar as universal2 (arm64 + x86_64) in onedir mode.
#
# Output:
#   - src-tauri/binaries/copaw-backend-aarch64-apple-darwin (universal2)
#   - src-tauri/binaries/copaw-backend-x86_64-apple-darwin (universal2)
#   - src-tauri/binaries/_internal (merged runtime dir)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SPEC_DIR="$PROJECT_ROOT/desktop/pyinstaller"

X86_PY="$PROJECT_ROOT/.venv/bin/python"
ARM_VENV="$PROJECT_ROOT/.venv-arm64-u13"
ARM_PY="$ARM_VENV/bin/python"
ARM_UV_PY="/Users/zhaobomin/.local/bin/python3.13"

X86_DIST="$PROJECT_ROOT/build/sidecar-x86-dist"
X86_WORK="$PROJECT_ROOT/build/sidecar-x86-work"
ARM_DIST="$PROJECT_ROOT/build/sidecar-arm64-dist"
ARM_WORK="$PROJECT_ROOT/build/sidecar-arm64-work"
UNI_DIR="$PROJECT_ROOT/build/sidecar-universal/copaw-backend"

echo "▶ Build universal2 sidecar (onedir)"

command -v uv >/dev/null || { echo "uv not found"; exit 1; }
[ -x "$X86_PY" ] || { echo "missing x86 python: $X86_PY"; exit 1; }

if [ ! -x "$ARM_PY" ]; then
  echo "▶ Creating arm64 venv: $ARM_VENV"
  uv python install 3.13
  uv venv "$ARM_VENV" --python "$ARM_UV_PY"
fi

echo "▶ Ensuring arm64 deps"
uv pip install -p "$ARM_PY" -e "$PROJECT_ROOT" pyinstaller >/dev/null

echo "▶ Ensuring x86 deps"
"$X86_PY" -m pip install -q pyinstaller

echo "▶ Building x86_64 sidecar"
(cd "$SPEC_DIR" && "$X86_PY" -m PyInstaller --clean --noconfirm --distpath "$X86_DIST" --workpath "$X86_WORK" CoPawBackend.spec)

echo "▶ Building arm64 sidecar"
(cd "$SPEC_DIR" && "$ARM_PY" -m PyInstaller --clean --noconfirm --distpath "$ARM_DIST" --workpath "$ARM_WORK" CoPawBackend.spec)

ARM_ROOT="$ARM_DIST/copaw-backend"
X86_ROOT="$X86_DIST/copaw-backend"
[ -x "$ARM_ROOT/copaw-backend" ] || { echo "missing arm sidecar"; exit 1; }
[ -x "$X86_ROOT/copaw-backend" ] || { echo "missing x86 sidecar"; exit 1; }

echo "▶ Merging to universal runtime tree"
mkdir -p "$(dirname "$UNI_DIR")"
if [ -d "$UNI_DIR" ]; then
  mv "$UNI_DIR" "${UNI_DIR}.bak.$(date +%s)"
fi
mkdir -p "$UNI_DIR"
rsync -a "$ARM_ROOT"/ "$UNI_DIR"/
rsync -a --ignore-existing "$X86_ROOT"/ "$UNI_DIR"/

lipo -create "$X86_ROOT/copaw-backend" "$ARM_ROOT/copaw-backend" -output "$UNI_DIR/copaw-backend"
chmod +x "$UNI_DIR/copaw-backend"

# Merge all same-path Mach-O files.
while IFS= read -r rel; do
  af="$ARM_ROOT/$rel"
  xf="$X86_ROOT/$rel"
  uf="$UNI_DIR/$rel"
  if [ -f "$xf" ] && file "$af" | rg -q 'Mach-O' && file "$xf" | rg -q 'Mach-O'; then
    lipo -create "$xf" "$af" -output "$uf" 2>/dev/null || cp "$af" "$uf"
  fi
done < <(cd "$ARM_ROOT" && find _internal -type f)

# Ensure both CPython names exist as universal, to satisfy either bootloader.
if [ -f "$X86_ROOT/_internal/Python" ] && [ -f "$ARM_ROOT/_internal/libpython3.13.dylib" ]; then
  lipo -create \
    "$X86_ROOT/_internal/Python" \
    "$ARM_ROOT/_internal/libpython3.13.dylib" \
    -output "$UNI_DIR/_internal/libpython3.13.dylib"
  cp "$UNI_DIR/_internal/libpython3.13.dylib" "$UNI_DIR/_internal/Python"
fi

echo "▶ Syncing to src-tauri/binaries"
mkdir -p "$PROJECT_ROOT/src-tauri/binaries"
cp "$UNI_DIR/copaw-backend" "$PROJECT_ROOT/src-tauri/binaries/copaw-backend-aarch64-apple-darwin"
cp "$UNI_DIR/copaw-backend" "$PROJECT_ROOT/src-tauri/binaries/copaw-backend-x86_64-apple-darwin"
if [ -d "$PROJECT_ROOT/src-tauri/binaries/_internal" ]; then
  mv "$PROJECT_ROOT/src-tauri/binaries/_internal" "$PROJECT_ROOT/src-tauri/binaries/_internal.bak.$(date +%s)"
fi
cp -R "$UNI_DIR/_internal" "$PROJECT_ROOT/src-tauri/binaries/_internal"
chmod +x \
  "$PROJECT_ROOT/src-tauri/binaries/copaw-backend-aarch64-apple-darwin" \
  "$PROJECT_ROOT/src-tauri/binaries/copaw-backend-x86_64-apple-darwin"

echo "▶ Verify"
file "$PROJECT_ROOT/src-tauri/binaries/copaw-backend-aarch64-apple-darwin" | sed -n '1,3p'
file "$PROJECT_ROOT/src-tauri/binaries/_internal/libpython3.13.dylib" 2>/dev/null | sed -n '1,3p' || true

echo "✅ Universal2 sidecar ready."
