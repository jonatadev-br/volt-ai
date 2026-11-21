import os
import subprocess
import httpx
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from .config import load_config


def _get_config():
    return load_config()


def _get_fs_root() -> Path:
    config = _get_config()
    return Path(config.safety.fs_root).expanduser() if config.safety.fs_root else Path.home()


def _validate_path(path: str) -> Path:
    p = Path(path).expanduser().resolve()
    try:
        p.relative_to(_get_fs_root())
    except ValueError:
        raise PermissionError(f"Path {path} is outside allowed root {_get_fs_root()}")
    return p


def _check_blocklist(cmd: str) -> bool:
    config = _get_config()
    for blocked in config.safety.blocklist:
        pattern = r'\b' + re.escape(blocked) + r'\b'
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False


def read_file(path: str) -> Dict[str, Any]:
    try:
        p = _validate_path(path)
        if not p.exists():
            return {"error": f"File not found: {path}"}
        if p.stat().st_size > 10_000_000:
            return {"error": "File too large (>10MB)"}
        content = p.read_text(encoding="utf-8", errors="replace")
        return {"content": content, "path": str(p)}
    except Exception as e:
        return {"error": str(e)}


def write_file(path: str, content: str) -> Dict[str, Any]:
    try:
        p = _validate_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"success": True, "path": str(p), "bytes": len(content.encode())}
    except Exception as e:
        return {"error": str(e)}


def list_dir(path: str = ".") -> Dict[str, Any]:
    try:
        p = _validate_path(path)
        if not p.exists():
            return {"error": f"Directory not found: {path}"}
        items = []
        for item in p.iterdir():
            items.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })
        return {"path": str(p), "items": items}
    except Exception as e:
        return {"error": str(e)}


def run_shell(cmd: str, cwd: str = ".", confirm: bool = True) -> Dict[str, Any]:
    config = _get_config()
    if confirm and config.safety.shell_confirm:
        return {"error": "Shell execution requires confirmation", "needs_confirmation": True, "command": cmd}
    if _check_blocklist(cmd):
        return {"error": f"Command blocked by safety policy: {cmd}"}
    try:
        work_dir = _validate_path(cwd)
        result = subprocess.run(
            cmd, shell=True, cwd=work_dir,
            capture_output=True, text=True, timeout=60
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "command": cmd
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out (60s)"}
    except Exception as e:
        return {"error": str(e)}


def run_shell_confirmed(cmd: str, cwd: str = ".") -> Dict[str, Any]:
    return run_shell(cmd, cwd, confirm=False)


async def fetch_url(url: str) -> Dict[str, Any]:
    try:
        headers = {"User-Agent": "zyvo-clone/1.0"}
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "text/html" in content_type:
            from html.parser import HTMLParser
            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = []
                    self.skip = False
                def handle_starttag(self, tag, attrs):
                    if tag in ("script", "style", "noscript"):
                        self.skip = True
                def handle_endtag(self, tag):
                    if tag in ("script", "style", "noscript"):
                        self.skip = False
                def handle_data(self, data):
                    if not self.skip:
                        self.text.append(data)
            parser = TextExtractor()
            parser.feed(resp.text)
            text = " ".join(parser.text)
            text = " ".join(text.split())[:10000]
            return {"url": url, "content": text, "title": ""}
        elif "application/json" in content_type:
            return {"url": url, "content": json.dumps(resp.json(), indent=2)[:10000]}
        else:
            return {"url": url, "content": resp.text[:10000]}
    except Exception as e:
        return {"error": str(e), "url": url}


NATIVE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file from the workspace",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "File path relative to workspace root"}},
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in the workspace",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to workspace root"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List directory contents",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Directory path", "default": "."}},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Execute a shell command (requires confirmation)",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string", "description": "Command to execute"},
                    "cwd": {"type": "string", "description": "Working directory", "default": "."}
                },
                "required": ["cmd"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "Fetch and extract text content from a URL",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "URL to fetch"}},
                "required": ["url"]
            }
        }
    }
]

TOOL_FUNCTIONS = {
    "read_file": read_file,
    "write_file": write_file,
    "list_dir": list_dir,
    "run_shell": run_shell,
    "fetch_url": fetch_url,
    "run_shell_confirmed": run_shell_confirmed
}


def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    func = TOOL_FUNCTIONS.get(name)
    if not func:
        return {"error": f"Unknown tool: {name}"}
    try:
        import inspect
        if inspect.iscoroutinefunction(func):
            import asyncio
            return asyncio.run(func(**args))
        return func(**args)
    except Exception as e:
        return {"error": f"Tool execution failed: {e}"}