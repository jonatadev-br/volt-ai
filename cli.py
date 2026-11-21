import typer
import json
from pathlib import Path
from typing import Optional

app = typer.Typer(name="volt-ai", help="Volt-AI — Desktop AI agent")

from core.config import load_config, save_config, get_api_key, set_api_key, test_provider_connection
from core.providers import get_provider_list, set_active_provider, update_provider
from core.agent import run_one_shot
from core.memory import create_session, list_sessions, get_session
from core.skills import discover_skills


@app.command()
def chat(
    no_browser: bool = typer.Option(False, "--no-browser", help="Don't open browser"),
    port: int = typer.Option(8765, "--port", help="Server port")
):
    """Launch GUI in browser"""
    from main import run_server
    run_server(no_browser=no_browser, port=port)


@app.command()
def run(
    user_prompt: str = typer.Argument(..., help="Prompt to execute"),
    project_dir: str = typer.Option(".", "--dir", "-d", help="Project directory")
):
    """Run a one-shot prompt"""
    result = run_one_shot(user_prompt, project_dir)
    typer.echo(result)


@app.command()
def skills_list():
    """List available skills"""
    config = load_config()
    all_skills = discover_skills()
    enabled = config.skills.enabled
    for name, skill in all_skills.items():
        status = "[ON]" if name in enabled else "[OFF]"
        desc = skill.manifest.get("description", "")
        typer.echo(f"{status} {name}: {desc}")


@app.command()
def skills_enable(name: str):
    """Enable a skill"""
    config = load_config()
    if name not in config.skills.enabled:
        config.skills.enabled.append(name)
        save_config(config)
        typer.echo(f"Enabled {name}")
    else:
        typer.echo(f"{name} already enabled")


@app.command()
def skills_disable(name: str):
    """Disable a skill"""
    config = load_config()
    if name in config.skills.enabled:
        config.skills.enabled.remove(name)
        save_config(config)
        typer.echo(f"Disabled {name}")
    else:
        typer.echo(f"{name} not enabled")


@app.command()
def config_show():
    """Show current config"""
    config = load_config()
    providers = get_provider_list(config)
    for p in providers:
        key_status = "SET" if p["has_key"] else "NOT SET"
        active = " *ACTIVE*" if p["is_active"] else ""
        typer.echo(f"{p['id']}{active}: {p['label']} | model={p['model']} | key={key_status}")
    typer.echo(f"\nActive: {config.active_provider}")
    typer.echo(f"Enabled skills: {config.skills.enabled}")


@app.command()
def config_set_provider(provider_id: str):
    """Set active provider"""
    config = load_config()
    if set_active_provider(provider_id, config):
        save_config(config)
        typer.echo(f"Active provider: {provider_id}")
    else:
        typer.echo(f"Unknown provider: {provider_id}")


@app.command()
def config_set_key(provider_id: str, key: str):
    """Set API key for provider"""
    config = load_config()
    if set_api_key(provider_id, key, config):
        typer.echo(f"Key saved for {provider_id}")
    else:
        typer.echo(f"Failed to save key for {provider_id}")


@app.command()
def config_test(provider_id: str):
    """Test provider connection"""
    config = load_config()
    success, msg = test_provider_connection(provider_id, config)
    typer.echo(f"{'OK' if success else 'FAIL'}: {msg}")


@app.command()
def sessions_list():
    """List sessions"""
    for s in list_sessions():
        typer.echo(f"{s['id']}: {s['name']} ({s['project_dir']}) - {s['updated_at']}")


@app.command()
def sessions_new(name: str = "New Session", project_dir: str = "."):
    """Create new session"""
    sid = create_session(name, project_dir)
    typer.echo(f"Created session {sid}")


if __name__ == "__main__":
    app()