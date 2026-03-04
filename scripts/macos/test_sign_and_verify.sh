#!/usr/bin/env bash
# Test: strip all local signatures, re-apply ad-hoc signing (Mach-O + app with --deep),
# then verify with codesign and spctl. Matches GitHub CI (see release-macos-dmg.yml).
# Run from repo root: bash scripts/macos/test_sign_and_verify.sh [CoPaw-Dev.app]
# Usage: build_dmg.sh --quick first, then run this on dist/CoPaw-Dev.app
#
# Note: Ad-hoc signed apps pass codesign --verify (and --strict when using --deep).
# spctl -a -t open may still reject (unknown developer); users who see "damaged"
# can run: xattr -cr /path/to/CoPaw.app

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

APP_PATH="${1:-dist/CoPaw-Dev.app}"
APP_DIR="$(cd "$(dirname "$APP_PATH")" && pwd)/$(basename "$APP_PATH")"

if [[ ! -d "$APP_DIR" ]]; then
  echo "ERROR: App not found: $APP_DIR" >&2
  echo "Usage: bash scripts/macos/test_sign_and_verify.sh [path/to/App.app]" >&2
  exit 1
fi

echo "[test_sign] App: $APP_DIR"
echo "[test_sign] Step 1: Strip all code signatures (clean state like CI runner)..."

# Remove bundle-level _CodeSignature so we start clean
rm -rf "$APP_DIR/Contents/_CodeSignature"

# Remove signature from app bundle first (removes seal only)
/usr/bin/codesign --remove-signature "$APP_DIR" 2>/dev/null || true

# Remove signature from every Mach-O (order: sign was inner then app, so remove app then inner)
while IFS= read -r -d '' f; do
  if /usr/bin/file -b "$f" | /usr/bin/grep -q 'Mach-O'; then
    /usr/bin/codesign --remove-signature "$f" 2>/dev/null || true
  fi
done < <(find "$APP_DIR" -type f -print0)

echo "[test_sign] Step 2: Re-apply ad-hoc signing (same as GitHub CI)..."

# Clean before signing (never modify after signing) — same as CI
find "$APP_DIR" -type d -name "*.dist-info" -print0 | xargs -0 rm -rf 2>/dev/null || true
find "$APP_DIR" -type f -name "py.typed" -delete 2>/dev/null || true
mkdir -p "$APP_DIR/Contents/Resources"

# Fix dirs with a period so codesign --deep does not fail (same as CI)
internal="$APP_DIR/Contents/Frameworks/_internal"
if [[ -d "$internal" ]]; then
  for path in "$internal"/python3.* "$internal"/Python.framework; do
    [[ -d "$path" ]] && ! [[ -L "$path" ]] || continue
    name=$(basename "$path")
    [[ "$name" != *.* ]] && continue
    dir_renamed=$(dirname "$path")/${name//./}
    [[ "$dir_renamed" != "$path" ]] && [[ ! -e "$dir_renamed" ]] || continue
    mv "$path" "$dir_renamed" && ln -s "$(basename "$dir_renamed")" "$path"
  done
fi

# 1) Sign Mach-O files only (do not exit on single failure; log and continue)
MACHO_FAIL=0
while IFS= read -r -d '' f; do
  if /usr/bin/file -b "$f" | /usr/bin/grep -q 'Mach-O'; then
    /usr/bin/codesign --force --sign - --timestamp=none "$f" || { MACHO_FAIL=$((MACHO_FAIL+1)); true; }
  fi
done < <(find "$APP_DIR" -type f -print0)
[[ "$MACHO_FAIL" -gt 0 ]] && echo "[test_sign] Mach-O sign failures: $MACHO_FAIL"

# 2) Sign the app bundle (--deep so nested _internal is sealed; required on macOS 15+)
/usr/bin/codesign --force --sign - --timestamp=none --deep "$APP_DIR"

echo "[test_sign] Step 3: Verify with codesign..."
if /usr/bin/codesign --verify --verbose=2 "$APP_DIR" 2>&1; then
  echo "[test_sign] codesign verify: OK"
else
  echo "[test_sign] codesign verify failed"
fi
if /usr/bin/codesign --verify --strict --verbose=2 "$APP_DIR" 2>&1; then
  echo "[test_sign] codesign --verify --strict: OK"
else
  echo "[test_sign] codesign --verify --strict: failed"
fi
set +e

echo "[test_sign] Step 4: Verify with spctl (Gatekeeper / 'damaged' check)..."
# Ad-hoc signed apps: spctl may reject 'open' but 'execute' can pass
(spctl -a -t open -v --context context:primary-signature "$APP_DIR" 2>&1) && true || \
  echo "[test_sign] spctl open (expected to fail for ad-hoc from unknown dev)"
(spctl -a -t execute -v "$APP_DIR" 2>&1) && echo "[test_sign] spctl execute: OK" || \
  echo "[test_sign] spctl execute: (see above)"
echo "[test_sign] spctl check done"

echo "[test_sign] Step 5: Summary..."
/usr/bin/codesign -dv --verbose=4 "$APP_DIR" 2>&1 | head -20
echo ""
echo ""
echo "[test_sign] Try opening the app..."
if open "$APP_DIR" 2>/dev/null; then
  echo "[test_sign] open succeeded; app should have launched."
else
  echo "[test_sign] open failed or could not confirm."
fi
echo "  Or run from Terminal: $APP_DIR/Contents/MacOS/$(basename "$APP_DIR" .app)"
