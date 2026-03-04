#!/usr/bin/env bash
# Build the website (Vite). Run from repo root: bash scripts/website_build.sh
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEBSITE_DIR="$REPO_ROOT/website"
cd "$WEBSITE_DIR"

echo "[website_build] Installing dependencies..."
if command -v pnpm &>/dev/null; then
  if ! pnpm install --frozen-lockfile 2>/dev/null; then
    pnpm install
  fi
else
  if ! npm ci 2>/dev/null; then
    npm install
  fi
fi

echo "[website_build] Building..."
if command -v pnpm &>/dev/null; then
  pnpm run build
else
  npm run build
fi

echo "[website_build] Done. Output: $WEBSITE_DIR/dist/"
