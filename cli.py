"""Volt-AI CLI — argparse only (no typer/click dependency)."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.config import (  # noqa: E402
    load_config, save_config, set_api_key, test_provider_connection, CONFIG_DIR,
)
from core.providers import get_provider_list, set_active_provider  # noqa: E402
from core.skills import discover_skills  # noqa: E402
from core.memory import create_session, list_sessions  # noqa: E402

APP_DIR = Path(__file__).parent
VERSION = "1.0.0"


def cmd_chat(args):
    from main import run_server
    run_server(no_browser=args.no_browser, port=args.port)


def cmd_run(args):
    from core.agent import run_one_shot
    print(run_one_shot(args.prompt, args.dir))


def cmd_skills(args):
    config = load_config()
    if args.action == "list":
        enabled = config.skills.enabled
        found = discover_skills()
        if not found:
            print("Nenhuma skill encontrada em ./skills")
            return
        for name, skill in found.items():
            mark = "[ON] " if name in enabled else "[OFF]"
            print(f"{mark} {name}: {skill.manifest.get('description', '')}")
    elif args.action == "enable":
        if args.name not in config.skills.enabled:
            config.skills.enabled.append(args.name)
            save_config(config)
            print(f"Skill habilitada: {args.name}")
        else:
            print(f"Já habilitada: {args.name}")
    elif args.action == "disable":
        if args.name in config.skills.enabled:
            config.skills.enabled.remove(args.name)
            save_config(config)
            print(f"Skill desabilitada: {args.name}")
        else:
            print(f"Não estava habilitada: {args.name}")


def cmd_config(args):
    config = load_config()
    if args.action == "show":
        for p in get_provider_list(config):
            active = " *ATIVO*" if p["is_active"] else ""
            key = "SET" if p["has_key"] else "NÃO SET"
            print(f"{p['id']}{active}: {p['label']} | model={p['model']} | key={key}")
        print(f"\nAtivo: {config.active_provider}")
        print(f"Skills: {config.skills.enabled}")
        print(f"Config: {CONFIG_DIR / 'config.yaml'}")
    elif args.action == "set-provider":
        if set_active_provider(args.provider, config):
            save_config(config)
            print(f"Provedor ativo: {args.provider}")
        else:
            print(f"Provedor desconhecido: {args.provider}")
    elif args.action == "set-key":
        if set_api_key(args.provider, args.key, config):
            print(f"Chave salva para {args.provider}")
        else:
            print(f"Falhou ao salvar a chave de {args.provider}")
    elif args.action == "test":
        ok, msg = test_provider_connection(args.provider, config)
        print(f"{'OK' if ok else 'FALHOU'}: {msg}")
    elif args.action == "set-model":
        if args.provider not in config.providers:
            print(f"Provedor desconhecido: {args.provider}")
            return
        config.providers[args.provider].model = args.model
        if args.base_url:
            config.providers[args.provider].base_url = args.base_url
        save_config(config)
        print(f"{args.provider}: model={args.model}")


def cmd_sessions(args):
    if args.action == "list":
        rows = list_sessions()
        if not rows:
            print("Nenhuma sessão ainda.")
            return
        for s in rows:
            print(f"{s['id']}: {s['name']} ({s['project_dir'] or '-'}) - {s['updated_at']}")
    elif args.action == "new":
        sid = create_session(args.name or "New Session", args.dir or ".")
        print(f"Sessão criada: {sid}")


def cmd_update(args):
    print(f"Atualizando {APP_DIR} ...")
    r = subprocess.run(["git", "-C", str(APP_DIR), "pull", "--ff-only"])
    if r.returncode != 0:
        print("git pull falhou — reinstale com o instalador.")
        return
    req = APP_DIR / "requirements.txt"
    py = sys.executable
    r2 = subprocess.run([py, "-m", "pip", "install", "-q", "-r", str(req)])
    print("Atualizado." if r2.returncode == 0 else "Código atualizado, deps falharam.")


def build_parser():
    p = argparse.ArgumentParser(prog="volt-ai", description="Volt-AI — agente desktop com GUI local")
    p.add_argument("--version", action="version", version=f"Volt-AI {VERSION}")
    sub = p.add_subparsers(dest="command")

    c = sub.add_parser("chat", help="Abrir a interface web")
    c.add_argument("--no-browser", action="store_true")
    c.add_argument("--port", type=int, default=None)
    c.set_defaults(func=cmd_chat)

    r = sub.add_parser("run", help="Executar um prompt único")
    r.add_argument("prompt")
    r.add_argument("--dir", "-d", default=".")
    r.set_defaults(func=cmd_run)

    s = sub.add_parser("skills", help="Gerenciar skills")
    s.add_argument("action", choices=["list", "enable", "disable"])
    s.add_argument("name", nargs="?")
    s.set_defaults(func=cmd_skills)

    cf = sub.add_parser("config", help="Configuração de provedores")
    cf.add_argument("action", choices=["show", "set-provider", "set-key", "test", "set-model"])
    cf.add_argument("provider", nargs="?")
    cf.add_argument("key", nargs="?")
    cf.add_argument("--model")
    cf.add_argument("--base-url", dest="base_url")
    cf.set_defaults(func=cmd_config)

    se = sub.add_parser("sessions", help="Sessões")
    se.add_argument("action", choices=["list", "new"])
    se.add_argument("name", nargs="?")
    se.add_argument("--dir", "-d")
    se.set_defaults(func=cmd_sessions)

    u = sub.add_parser("update", help="Atualizar código e dependências")
    u.set_defaults(func=cmd_update)
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
