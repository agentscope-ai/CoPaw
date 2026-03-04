#!/usr/bin/env bash
# Quick sidecar build for development
#
# This script builds the Python sidecar binary without rebuilding
# the frontend or the full Tauri app. Useful for testing backend changes.
#
# Usage: ./scripts/build_sidecar.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "🔧 Building Python sidecar..."

# Build frontend if needed
if [ ! -d "console/dist" ] || [ ! -f "src/copaw/console/index.html" ]; then
    echo "📦 Building frontend..."
    pushd console >/dev/null
    npm ci
    npm run build
    popd >/dev/null

    echo "📂 Copying frontend to Python package..."
    mkdir -p src/copaw/console
    rm -rf src/copaw/console/*
    cp -r console/dist/. src/copaw/console/
fi

# Build with PyInstaller
echo "🐍 Running PyInstaller..."
python3 -m PyInstaller --clean --noconfirm desktop/pyinstaller/CoPawBackend.spec

# Copy to Tauri binaries
echo "📂 Copying to Tauri binaries directory..."
mkdir -p src-tauri/binaries
cp dist/copaw-backend/copaw-backend "src-tauri/binaries/copaw-backend-aarch64-apple-darwin"
cp dist/copaw-backend/copaw-backend "src-tauri/binaries/copaw-backend-x86_64-apple-darwin"
rm -rf src-tauri/binaries/_internal
cp -R dist/copaw-backend/_internal src-tauri/binaries/_internal
chmod +x \
  "src-tauri/binaries/copaw-backend-aarch64-apple-darwin" \
  "src-tauri/binaries/copaw-backend-x86_64-apple-darwin"

echo ""
echo "✅ Sidecar built successfully!"
echo "   Binaries:"
echo "   - src-tauri/binaries/copaw-backend-aarch64-apple-darwin"
echo "   - src-tauri/binaries/copaw-backend-x86_64-apple-darwin"
echo "   - src-tauri/binaries/_internal"
