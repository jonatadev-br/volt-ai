#!/usr/bin/env bash
# Build Volt-AI locally on Termux (aarch64)
# Run this on your phone in Termux to build the binary yourself

set -euo pipefail

cd "$(dirname "$0")"

log() { echo -e "\033[0;34m[Build]\033[0m $*"; }
ok() { echo -e "\033[0;32m[OK]\033[0m $*"; }
err() { echo -e "\033[0;31m[ERR]\033[0m $*"; exit 1; }

# Install system deps
log "Installing system dependencies..."
pkg update -y && pkg install -y python git clang libffi openssl upx 2>/dev/null || true

# Install Python deps (use versions compatible with Python 3.14)
log "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir \
  'litellm<1.83.0' \
  'fastapi<0.116.0' \
  'uvicorn<0.31.0' \
  'typer<0.13.0' \
  'pydantic<2.10.0' \
  'pydantic-settings<2.5.0' \
  'python-dotenv<1.1.0' \
  'pyyaml<6.1.0' \
  'keyring<26.0.0' \
  'cryptography<43.0.0' \
  'httpx<0.28.0' \
  'rich<14.0.0' \
  'python-multipart<0.1.0' \
  'tiktoken<0.8.0' \
  pyinstaller

# Build
log "Building with PyInstaller..."
cd build
chmod +x build_linux.sh
./build_linux.sh

# Verify
if [[ -f dist/Volt-AI ]]; then
  ok "Build successful: dist/Volt-AI"
  file dist/Volt-AI
  ./dist/Volt-AI --help 2>&1 | head -5 || true
else
  err "Build failed — no dist/Volt-AI"
fi

echo
log "To install locally:"
echo "  mkdir -p ~/.local/bin"
echo "  cp dist/Volt-AI ~/.local/bin/volt-ai"
echo "  chmod +x ~/.local/bin/volt-ai"
echo "  volt-ai chat --no-browser"