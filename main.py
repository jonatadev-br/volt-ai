import sys
import os
import uvicorn
import webbrowser
import threading
import time
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent))

from core.config import load_config, save_config, test_provider_connection, set_api_key
from core.providers import get_provider_list, set_active_provider, update_provider
from core.agent import Agent
from core.memory import (
    create_session, list_sessions, get_session, update_session, delete_session,
    get_messages, read_agents_md, write_agents_md
)
from core.skills import discover_skills, get_enabled_skills
from core.tools import _validate_path

BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR / "frontend"


def get_resource_path(relative_path: str) -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / relative_path
    return BASE_DIR / relative_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Volt-AI", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=get_resource_path("frontend")), name="static")


@app.get("/")
async def root():
    return FileResponse(get_resource_path("frontend/index.html"))


@app.get("/api/config")
async def api_config():
    config = load_config()
    providers = get_provider_list(config)
    return {"providers": providers, "active": config.active_provider, "skills": config.skills.enabled, "safety": config.safety.model_dump()}


@app.post("/api/config/provider")
async def api_set_provider(data: dict):
    config = load_config()
    provider_id = data.get("provider_id")
    if set_active_provider(provider_id, config):
        save_config(config)
        return {"success": True}
    return {"success": False, "error": "Invalid provider"}


@app.post("/api/config/provider/update")
async def api_update_provider(data: dict):
    config = load_config()
    provider_id = data.get("provider_id")
    base_url = data.get("base_url", "")
    model = data.get("model", "")
    if update_provider(provider_id, base_url, model, config):
        save_config(config)
        return {"success": True}
    return {"success": False, "error": "Invalid provider"}


@app.post("/api/config/key")
async def api_set_key(data: dict):
    config = load_config()
    provider_id = data.get("provider_id")
    key = data.get("key")
    if set_api_key(provider_id, key, config):
        return {"success": True}
    return {"success": False, "error": "Failed to save key"}


@app.post("/api/config/key/delete")
async def api_delete_key(data: dict):
    config = load_config()
    provider_id = data.get("provider_id")
    from core.config import delete_api_key
    if delete_api_key(provider_id, config):
        return {"success": True}
    return {"success": False, "error": "Failed to delete key"}


@app.post("/api/config/test")
async def api_test_provider(data: dict):
    config = load_config()
    provider_id = data.get("provider_id")
    success, msg = test_provider_connection(provider_id, config)
    return {"success": success, "message": msg}


@app.get("/api/skills")
async def api_skills():
    config = load_config()
    all_skills = discover_skills()
    enabled = config.skills.enabled
    result = []
    for name, skill in all_skills.items():
        result.append({
            "name": name,
            "description": skill.manifest.get("description", ""),
            "enabled": name in enabled,
            "skill_md": skill.skill_md
        })
    return {"skills": result}


@app.post("/api/skills/toggle")
async def api_toggle_skill(data: dict):
    config = load_config()
    name = data.get("name")
    enable = data.get("enable", True)
    if enable and name not in config.skills.enabled:
        config.skills.enabled.append(name)
    elif not enable and name in config.skills.enabled:
        config.skills.enabled.remove(name)
    save_config(config)
    return {"success": True}


@app.get("/api/sessions")
async def api_sessions():
    return {"sessions": list_sessions()}


@app.post("/api/sessions")
async def api_create_session(data: dict):
    name = data.get("name", "New Session")
    project_dir = data.get("project_dir", "")
    sid = create_session(name, project_dir)
    return {"id": sid}


@app.get("/api/sessions/{session_id}")
async def api_get_session(session_id: int):
    session = get_session(session_id)
    if not session:
        return {"error": "Not found"}
    session["messages"] = get_messages(session_id)
    return session


@app.put("/api/sessions/{session_id}")
async def api_update_session(session_id: int, data: dict):
    update_session(session_id, data.get("name"), data.get("project_dir"))
    return {"success": True}


@app.delete("/api/sessions/{session_id}")
async def api_delete_session(session_id: int):
    delete_session(session_id)
    return {"success": True}


@app.get("/api/agents-md")
async def api_get_agents_md(project_dir: str = ""):
    if project_dir:
        try:
            _validate_path(project_dir)
        except PermissionError:
            return {"error": "Path not allowed"}
    return {"content": read_agents_md(project_dir) if project_dir else ""}


@app.post("/api/agents-md")
async def api_save_agents_md(data: dict):
    project_dir = data.get("project_dir", "")
    content = data.get("content", "")
    if project_dir:
        try:
            _validate_path(project_dir)
        except PermissionError:
            return {"error": "Path not allowed"}
    write_agents_md(project_dir, content)
    return {"success": True}


@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: int):
    config = load_config()
    origin = websocket.headers.get("origin", "")
    allowed = f"http://{config.server.host}:{config.server.port}"
    if origin and origin != allowed:
        await websocket.close(code=4003)
        return
    await websocket.accept()
    agent = Agent(session_id, get_session(session_id).get("project_dir", "") if get_session(session_id) else "")
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "chat":
                async for chunk in agent.chat(data.get("message", "")):
                    await websocket.send_json(chunk)
            elif data.get("type") == "confirm_shell":
                from core.tools import run_shell_confirmed, _check_blocklist
                cmd = data.get("cmd", "")
                if _check_blocklist(cmd):
                    await websocket.send_json({"type": "tool_result", "name": "run_shell", "id": data.get("id"), "result": {"error": "Command blocked by safety policy"}})
                else:
                    result = run_shell_confirmed(cmd, data.get("cwd", "."))
                    await websocket.send_json({"type": "tool_result", "name": "run_shell", "id": data.get("id"), "result": result})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "content": str(e)})


def run_server(host: str = "127.0.0.1", port: int = 8765, no_browser: bool = False):
    config = load_config()
    host = config.server.host
    port = config.server.port
    if not no_browser:
        def open_browser():
            time.sleep(1.5)
            webbrowser.open(f"http://{host}:{port}")
        threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    run_server(no_browser=args.no_browser, port=args.port)