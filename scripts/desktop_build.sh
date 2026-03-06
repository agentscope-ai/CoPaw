#!/usr/bin/env bash
# Build the CoPaw Mac desktop app (.dmg / .zip).
# Prepares the bundled Python runtime, then packages via Electron Forge.
# Run from repo root: bash scripts/desktop_build.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DESKTOP_DIR="$REPO_ROOT/desktop"
RUNTIME_DIR="$DESKTOP_DIR/runtime"
VENV_DIR="$RUNTIME_DIR/venv"
CONSOLE_DIR="$REPO_ROOT/console"
CONSOLE_DEST="$REPO_ROOT/src/copaw/console"
PYTHON_VERSION="3.12"

BOLD="\033[1m" GREEN="\033[0;32m" YELLOW="\033[0;33m" RED="\033[0;31m" RESET="\033[0m"
info()  { printf "${GREEN}[desktop_build]${RESET} %s\n" "$*"; }
warn()  { printf "${YELLOW}[desktop_build]${RESET} %s\n" "$*"; }
die()   { printf "${RED}[desktop_build]${RESET} %s\n" "$*" >&2; exit 1; }

# ── Step 1: Check tools ──────────────────────────────────────────────────────
command -v uv  &>/dev/null || die "uv is required. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
command -v npm &>/dev/null || die "npm is required. Install Node.js from https://nodejs.org/"
info "uv: $(uv --version), npm: $(npm --version)"

# ── Step 2: Build console frontend ───────────────────────────────────────────
if [ -f "$CONSOLE_DEST/index.html" ]; then
  info "Console assets already present, skipping build."
else
  info "Building console frontend..."
  (cd "$CONSOLE_DIR" && npm ci && npm run build)
  mkdir -p "$CONSOLE_DEST"
  cp -R "$CONSOLE_DIR/dist/"* "$CONSOLE_DEST/"
  info "Console build complete."
fi

# ── Step 3: Prepare Python runtime ───────────────────────────────────────────
if [ -d "$VENV_DIR" ]; then
  warn "Existing runtime found, recreating..."
  rm -rf "$VENV_DIR"
fi

info "Creating Python $PYTHON_VERSION venv..."
uv venv "$VENV_DIR" --python "$PYTHON_VERSION" --quiet
[ -x "$VENV_DIR/bin/python" ] || die "Failed to create venv"
info "Python venv ready ($("$VENV_DIR/bin/python" --version))"

info "Installing copaw from source..."
uv pip install "$REPO_ROOT" --python "$VENV_DIR/bin/python" --prerelease=allow --quiet
[ -x "$VENV_DIR/bin/copaw" ] || die "copaw CLI not found after install"
info "copaw installed."

SKIP_PLAYWRIGHT="${SKIP_PLAYWRIGHT:-}"
if [ -z "$SKIP_PLAYWRIGHT" ]; then
  info "Installing Playwright Chromium..."
  "$VENV_DIR/bin/python" -m playwright install chromium 2>/dev/null || {
    warn "Playwright install failed (non-fatal). Browser skills may not work."
  }
else
  info "Skipping Playwright (SKIP_PLAYWRIGHT is set)."
fi

# ── Step 4: Install Electron dependencies ─────────────────────────────────────
info "Installing desktop npm dependencies..."
(cd "$DESKTOP_DIR" && npm ci)

# ── Step 5: Package with Electron Forge ──────────────────────────────────────
info "Packaging Electron app..."
(cd "$DESKTOP_DIR" && npx electron-forge make)

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
printf "${GREEN}${BOLD}Desktop build complete!${RESET}\n"
VENV_SIZE="$(du -sh "$VENV_DIR" | cut -f1)"
printf "  Runtime size:  ${BOLD}%s${RESET}\n" "$VENV_SIZE"
echo ""
info "Output: $DESKTOP_DIR/out/make/"
ls -lh "$DESKTOP_DIR/out/make/"*/* 2>/dev/null || true
