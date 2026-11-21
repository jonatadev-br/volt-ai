#!/usr/bin/env bash
# Instala o Volt-AI a partir DESTA pasta (dev/local, sem binário).
set -euo pipefail
cd "$(dirname "$0")"

ROOT="${HOME}/.volt-ai"
VENV="${ROOT}/venv-dev"
BIN="${HOME}/.local/bin"

log() { printf "\033[0;34m[dev]\033[0m %s\n" "$*"; }

command -v python >/dev/null 2>&1 || { pkg install -y python 2>/dev/null || true; }
mkdir -p "$ROOT" "$BIN"

[ -x "$VENV/bin/python" ] || { log "criando venv..."; python -m venv "$VENV"; }
"$VENV/bin/python" -m pip install -q --upgrade pip
log "instalando deps..."
"$VENV/bin/python" -m pip install -q -r requirements.txt

cat > "${BIN}/volt-ai" <<EOF
#!/usr/bin/env bash
exec "${VENV}/bin/python" "$(pwd)/cli.py" "\$@"
EOF
chmod +x "${BIN}/volt-ai"

log "pronto: ${BIN}/volt-ai"
"${BIN}/volt-ai" --version
echo "Rode: volt-ai chat"
