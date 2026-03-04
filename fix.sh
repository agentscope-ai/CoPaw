APP="/Users/zhaobomin/Documents/projects/thirdpart/CoPaw/src-tauri/target/release/bundle/macos/CoPaw.app" && \
set -e && \
echo "==> Ensure bundle structure" && \
mkdir -p "$APP/Contents/Resources" && \
echo "==> Remove existing signatures (best-effort)" && \
find "$APP" -name "_CodeSignature" -type d -prune -exec rm -rf {} + 2>/dev/null || true && \
find "$APP" -name "CodeResources" -type f -delete 2>/dev/null || true && \
echo "==> Ad-hoc sign all Mach-O binaries (dylib/so/executables)" && \
while IFS= read -r -d '' f; do \
  codesign --force --sign - --timestamp=none "$f" >/dev/null; \
done < <( \
  find "$APP/Contents" -type f \( -name "*.dylib" -o -name "*.so" -o -perm -111 \) -print0 \
) && \
echo "==> Sign app bundle" && \
codesign --force --sign - --timestamp=none "$APP" && \
echo "==> Verify" && \
codesign --verify --deep --strict --verbose=4 "$APP" && \
echo "==> Gatekeeper check (may still be rejected without notarization)" && \
spctl -a -vv "$APP" || true && \
echo "DONE"
