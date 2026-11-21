"""Volt-AI HTTP + WebSocket server — Starlette (no FastAPI/pydantic)."""
import sys
import time
import threading
import webbrowser
from dataclasses import asdict
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

sys.path.insert(0, str(Path(__file__).parent))

from core.config import (  # noqa: E402
    load_config, save_config, test_provider_connection, set_api_key, delete_api_key,
)
from core.providers import get_provider_list, set_active_provider, update_provider  # noqa: E402
from core.agent import Agent  # noqa: E402
from core.memory import (  # noqa: E402
    create_session, list_sessions, get_session, update_session, delete_session,
    get_messages, read_agents_md, write_agents_md,
)
from core.skills import discover_skills  # noqa: E402
from core.tools import _validate_path  # noqa: E402

BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR / "frontend"


def get_resource_path(relative_path: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative_path
    return BASE_DIR / relative_path


# ------------------------------------------------------------------- handlers

async def root(request):
    return FileResponse(get_resource_path("frontend/index.html"))


async def health(request):
    return JSONResponse({"status": "ok", "app": "Volt-AI"})


async def api_config(request):
    config = load_config()
    return JSONResponse({
        "providers": get_provider_list(config),
        "active": config.active_provider,
        "skills": config.skills.enabled,
        "safety": asdict(config.safety),
        "server": asdict(config.server),
    })


async def api_set_provider(request):
    data = await request.json()
    config = load_config()
    if set_active_provider(data.get("provider_id"), config):
        save_config(config)
        return JSONResponse({"success": True})
    return JSONResponse({"success": False, "error": "Invalid provider"})


async def api_update_provider(request):
    data = await request.json()
    config = load_config()
    if update_provider(data.get("provider_id"), data.get("base_url", ""), data.get("model", ""), config):
        save_config(config)
        return JSONResponse({"success": True})
    return JSONResponse({"success": False, "error": "Invalid provider"})


async def api_set_key(request):
    data = await request.json()
    config = load_config()
    if set_api_key(data.get("provider_id"), data.get("key"), config):
        return JSONResponse({"success": True})
    return JSONResponse({"success": False, "error": "Failed to save key"})


async def api_delete_key(request):
    data = await request.json()
    config = load_config()
    if delete_api_key(data.get("provider_id"), config):
        return JSONResponse({"success": True})
    return JSONResponse({"success": False, "error": "Failed to delete key"})


async def api_test_provider(request):
    data = await request.json()
    config = load_config()
    success, msg = test_provider_connection(data.get("provider_id"), config)
    return JSONResponse({"success": success, "message": msg})


async def api_skills(request):
    config = load_config()
    enabled = config.skills.enabled
    result = [
        {
            "name": name,
            "description": skill.manifest.get("description", ""),
            "enabled": name in enabled,
            "skill_md": skill.skill_md,
        }
        for name, skill in discover_skills().items()
    ]
    return JSONResponse({"skills": result})


async def api_toggle_skill(request):
    data = await request.json()
    config = load_config()
    name = data.get("name")
    enable = data.get("enable", True)
    if enable and name not in config.skills.enabled:
        config.skills.enabled.append(name)
    elif not enable and name in config.skills.enabled:
        config.skills.enabled.remove(name)
    save_config(config)
    return JSONResponse({"success": True})


async def api_sessions(request):
    if request.method == "POST":
        data = await request.json()
        sid = create_session(data.get("name", "New Session"), data.get("project_dir", ""))
        return JSONResponse({"id": sid})
    return JSONResponse({"sessions": list_sessions()})


async def api_session(request):
    sid = int(request.path_params["session_id"])
    if request.method == "GET":
        session = get_session(sid)
        if not session:
            return JSONResponse({"error": "Not found"}, status_code=404)
        session["messages"] = get_messages(sid)
        return JSONResponse(session)
    if request.method == "PUT":
        data = await request.json()
        update_session(sid, data.get("name"), data.get("project_dir"))
        return JSONResponse({"success": True})
    delete_session(sid)
    return JSONResponse({"success": True})


async def api_agents_md(request):
    if request.method == "GET":
        project_dir = request.query_params.get("project_dir", "")
        if project_dir:
            try:
                _validate_path(project_dir)
            except PermissionError:
                return JSONResponse({"error": "Path not allowed"})
        return JSONResponse({"content": read_agents_md(project_dir) if project_dir else ""})
    data = await request.json()
    project_dir = data.get("project_dir", "")
    if project_dir:
        try:
            _validate_path(project_dir)
        except PermissionError:
            return JSONResponse({"error": "Path not allowed"})
    write_agents_md(project_dir, data.get("content", ""))
    return JSONResponse({"success": True})


async def ws_chat(websocket: WebSocket):
    session_id = int(websocket.path_params["session_id"])
    config = load_config()
    origin = websocket.headers.get("origin", "")
    allowed = {f"http://{config.server.host}:{config.server.port}",
               f"http://127.0.0.1:{config.server.port}",
               f"http://localhost:{config.server.port}"}
    if origin and origin not in allowed:
        await websocket.close(code=4003)
        return
    await websocket.accept()
    session = get_session(session_id)
    agent = Agent(session_id, session.get("project_dir", "") if session else "")
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
                    await websocket.send_json({
                        "type": "tool_result", "name": "run_shell", "id": data.get("id"),
                        "result": {"error": "Command blocked by safety policy"},
                    })
                else:
                    result = run_shell_confirmed(cmd, data.get("cwd", "."))
                    await websocket.send_json({
                        "type": "tool_result", "name": "run_shell", "id": data.get("id"),
                        "result": result,
                    })
    except WebSocketDisconnect:
        pass
    except Exception as e:  # noqa: BLE001
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass


routes = [
    Route("/", root),
    Route("/api/health", health),
    Route("/api/config", api_config),
    Route("/api/config/provider", api_set_provider, methods=["POST"]),
    Route("/api/config/provider/update", api_update_provider, methods=["POST"]),
    Route("/api/config/key", api_set_key, methods=["POST"]),
    Route("/api/config/key/delete", api_delete_key, methods=["POST"]),
    Route("/api/config/test", api_test_provider, methods=["POST"]),
    Route("/api/skills", api_skills),
    Route("/api/skills/toggle", api_toggle_skill, methods=["POST"]),
    Route("/api/sessions", api_sessions, methods=["GET", "POST"]),
    Route("/api/sessions/{session_id:int}", api_session, methods=["GET", "PUT", "DELETE"]),
    Route("/api/agents-md", api_agents_md, methods=["GET", "POST"]),
    WebSocketRoute("/ws/chat/{session_id:int}", ws_chat),
    Mount("/static", app=StaticFiles(directory=str(get_resource_path("frontend"))), name="static"),
]

app = Starlette(routes=routes)


def _open_browser(url: str):
    import shutil, subprocess
    for cmd in (
        ["termux-open-url", url],
        ["xdg-open", url],
        ["am", "start", "-a", "android.intent.action.VIEW", "-d", url],
    ):
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, check=False)
                return
            except Exception:
                pass
    try:
        webbrowser.open(url)
    except Exception:
        pass


def run_server(host: str = None, port: int = None, no_browser: bool = False):
    config = load_config()
    host = host or config.server.host or "127.0.0.1"
    port = int(port or config.server.port or 8765)
    if not no_browser:
        def open_browser():
            time.sleep(1.5)
            _open_browser(f"http://{host}:{port}")
        threading.Thread(target=open_browser, daemon=True).start()
        print(f"[Volt-AI] abrindo {host}:{port} no navegador...")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="volt-ai")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()
    run_server(no_browser=args.no_browser, port=args.port)
