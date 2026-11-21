#!/usr/bin/env bash
# Volt-AI — instalador de um comando (Termux / Linux / macOS)
#
#   curl -fsSL https://raw.githubusercontent.com/jonataprezende-commits/volt-ai/main/install-termux.sh | bash
#
# Não compila nada: baixa o código, cria um venv e instala deps pure-Python.
set -euo pipefail

REPO="jonataprezende-commits/volt-ai"
ROOT="${HOME}/.volt-ai"
APP_DIR="${ROOT}/app"
VENV_DIR="${ROOT}/venv"
BIN_DIR="${HOME}/.local/bin"

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { printf "${BLUE}[Volt-AI]${NC} %s\n" "$*"; }
ok()   { printf "${GREEN}[OK]${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}[WARN]${NC} %s\n" "$*"; }
die()  { printf "${RED}[ERRO]${NC} %s\n" "$*"; exit 1; }

IS_TERMUX=0
[ -n "${TERMUX_VERSION:-}" ] && IS_TERMUX=1
[ -d "/data/data/com.termux" ] && IS_TERMUX=1

# ---------------------------------------------------------------- prerequisites
if [ "$IS_TERMUX" -eq 1 ]; then
  command -v pkg >/dev/null 2>&1 || die "pkg não encontrado — isso não parece Termux."
  NEED=""
  command -v git   >/dev/null 2>&1 || NEED="$NEED git"
  command -v python >/dev/null 2>&1 || NEED="$NEED python"
  if [ -n "$NEED" ]; then
    log "Instalando:$NEED"
    pkg install -y $NEED >/dev/null 2>&1 || die "pkg install falhou"
  fi
fi

PY=""
for cand in python3 python; do
  command -v "$cand" >/dev/null 2>&1 && { PY="$cand"; break; }
done
[ -n "$PY" ] || die "Python não encontrado."
command -v git >/dev/null 2>&1 || die "git não encontrado."

log "Python: $("$PY" -V 2>&1)"
mkdir -p "$ROOT" "$BIN_DIR"

# ---------------------------------------------------------------- code
if [ -d "$APP_DIR/.git" ]; then
  log "Atualizando código existente..."
  git -C "$APP_DIR" fetch --depth 1 origin main >/dev/null 2>&1 || true
  git -C "$APP_DIR" reset --hard origin/main >/dev/null 2>&1 || true
else
  log "Baixando código..."
  rm -rf "$APP_DIR"
  git clone --depth 1 "https://github.com/${REPO}.git" "$APP_DIR" >/dev/null 2>&1 \
    || die "git clone falhou (sem internet?)"
fi
ok "Código em $APP_DIR"

# ---------------------------------------------------------------- venv + deps
USE_VENV=1
if [ ! -x "$VENV_DIR/bin/python" ]; then
  log "Criando ambiente virtual..."
  if ! "$PY" -m venv "$VENV_DIR" >/dev/null 2>&1; then
    warn "venv falhou — usando instalação --user"
    USE_VENV=0
    rm -rf "$VENV_DIR"
  fi
fi

if [ "$USE_VENV" -eq 1 ]; then
  VPIP="$VENV_DIR/bin/python -m pip"
  "$VENV_DIR/bin/python" -m pip install -q --upgrade pip >/dev/null 2>&1 || true
else
  VPIP="$PY -m pip"
fi

log "Instalando dependências (1-2 min na primeira vez)..."
if ! $VPIP install -q -r "$APP_DIR/requirements.txt" 2>"$ROOT/pip.log"; then
  warn "pip falhou — tentando com mirror/compilação..."
  $VPIP install -r "$APP_DIR/requirements.txt" || {
    tail -20 "$ROOT/pip.log" 2>/dev/null
    die "Instalação de dependências falhou (log: $ROOT/pip.log)"
  }
fi
ok "Dependências instaladas"

# ---------------------------------------------------------------- launcher
cat > "${BIN_DIR}/volt-ai" <<EOF
#!/usr/bin/env bash
exec "${VENV_DIR}/bin/python" "${APP_DIR}/cli.py" "\$@"
EOF
if [ "$USE_VENV" -eq 0 ]; then
  cat > "${BIN_DIR}/volt-ai" <<EOF
#!/usr/bin/env bash
exec "${PY}" "${APP_DIR}/cli.py" "\$@"
EOF
fi
chmod +x "${BIN_DIR}/volt-ai"
ok "Comando: ${BIN_DIR}/volt-ai"

# ---------------------------------------------------------------- PATH
add_path_line() {
  local rc="$1"
  [ -f "$rc" ] || return 0
  grep -q '.local/bin' "$rc" 2>/dev/null && return 0
  printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$rc"
}
for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do add_path_line "$rc"; done
export PATH="${BIN_DIR}:$PATH"

# ---------------------------------------------------------------- verify
log "Verificando instalação..."
"${BIN_DIR}/volt-ai" --version || die "O comando não executou."

echo
ok "Volt-AI instalado!"
echo
printf "  %-34s %s\n" "Abrir interface (navegador):" "volt-ai chat"
printf "  %-34s %s\n" "Prompt único:"                "volt-ai run \"seu prompt\""
printf "  %-34s %s\n" "Ver provedores:"              "volt-ai config show"
printf "  %-34s %s\n" "Salvar chave NVIDIA NIM:"     "volt-ai config set-key nvidia_nim SUA_CHAVE"
printf "  %-34s %s\n" "Atualizar:"                   "volt-ai update"
echo
if [ "$IS_TERMUX" -eq 1 ]; then
  log "No Termux, rode: source ~/.bashrc  (para o comando valer em novas abas)"
fi
