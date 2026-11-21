#!/usr/bin/env bash
# Volt-AI Termux Installer — one command install
# Usage: curl -fsSL https://raw.githubusercontent.com/USER/volt-ai/main/install-termux.sh | bash

set -euo pipefail

REPO="jonataprezende-commits/volt-ai"
TAG="termux-latest"
BIN_NAME="Volt-AI"
INSTALL_DIR="${HOME}/.local/bin"
CONFIG_DIR="${HOME}/.volt-ai"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[Volt-AI]${NC} $*"; }
ok() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err() { echo -e "${RED}[ERR]${NC} $*"; exit 1; }

# Check Termux
[[ -n "${TERMUX_VERSION:-}" ]] || warn "Not running in Termux — continuing anyway"

# Check arch
ARCH=$(uname -m)
[[ "$ARCH" == "aarch64" ]] || err "This binary is for aarch64 (ARM64). Your arch: $ARCH"

# Create dirs
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR"
[[ ":$PATH:" == *":$INSTALL_DIR:"* ]] || {
  warn "$INSTALL_DIR not in PATH. Add to ~/.bashrc or ~/.zshrc:"
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
}

# Download
URL="https://github.com/${REPO}/releases/download/${TAG}/${BIN_NAME}"
log "Downloading from $URL"
curl -fsSL -o "${INSTALL_DIR}/volt-ai" "$URL" || err "Download failed. Check release exists: https://github.com/${REPO}/releases/tag/${TAG}"

chmod +x "${INSTALL_DIR}/volt-ai"
ok "Installed to ${INSTALL_DIR}/volt-ai"

# Verify
log "Verifying binary..."
"${INSTALL_DIR}/volt-ai" --help 2>&1 | head -3 || warn "Binary runs but --help failed (may be expected)"

# Config hint
if [[ ! -f "${CONFIG_DIR}/config.yaml" ]]; then
  log "First run will create config at ${CONFIG_DIR}/config.yaml"
  log "Add your NVIDIA NIM API key in the GUI (Config tab) or via CLI:"
  echo "  volt-ai config set-key nvidia_nim \"your-key\""
fi

# Done
echo
ok "Volt-AI installed!"
echo
echo "Run GUI:     volt-ai chat"
echo "Run CLI:     volt-ai run \"your prompt\""
echo "Config:      volt-ai config show"
echo "Skills:      volt-ai skills list"
echo
echo "Open browser at http://127.0.0.1:8765 after 'volt-ai chat'"