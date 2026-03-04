#!/usr/bin/env bash
#
# Clean stale desktop build/runtime artifacts for CoPaw.
#
# Usage:
#   ./scripts/clean_desktop.sh
#   ./scripts/clean_desktop.sh --with-applications

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

WITH_APPLICATIONS=false
for arg in "$@"; do
  case "$arg" in
    --with-applications) WITH_APPLICATIONS=true ;;
    *)
      echo "Unknown option: $arg"
      echo "Usage: ./scripts/clean_desktop.sh [--with-applications]"
      exit 1
      ;;
  esac
done

echo "Stopping running CoPaw processes..."
pkill -f '/Contents/MacOS/copaw$' 2>/dev/null || true
pkill -f 'copaw-backend' 2>/dev/null || true

echo "Removing local desktop build artifacts..."
rm -rf "$PROJECT_ROOT/src-tauri/target/release/bundle/macos/CoPaw.app"
rm -rf "$PROJECT_ROOT/src-tauri/target/release/bundle/dmg"
rm -f "$PROJECT_ROOT/dist/CoPaw.dmg"

echo "Cleaning PyInstaller outputs..."
rm -rf "$PROJECT_ROOT/desktop/pyinstaller/build/CoPawBackend"
rm -rf "$PROJECT_ROOT/desktop/pyinstaller/dist/copaw-backend"
rm -rf "$PROJECT_ROOT/src-tauri/binaries/_internal"

if [ "$WITH_APPLICATIONS" = true ]; then
  echo "Removing /Applications/CoPaw.app ..."
  rm -rf "/Applications/CoPaw.app"
fi

echo "Done."
