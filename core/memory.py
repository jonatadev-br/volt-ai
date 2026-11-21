import sqlite3
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from .config import CONFIG_DIR

DB_FILE = CONFIG_DIR / "sessions.db"


def init_db():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_FILE) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                project_dir TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                tool_calls TEXT,
                tool_call_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                args TEXT,
                result TEXT,
                status TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
        """)


def create_session(name: str, project_dir: str = "") -> int:
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute(
            "INSERT INTO sessions (name, project_dir) VALUES (?, ?)",
            (name, project_dir)
        )
        return cur.lastrowid


def list_sessions() -> List[Dict[str, Any]]:
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]


def get_session(session_id: int) -> Optional[Dict[str, Any]]:
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None


def update_session(session_id: int, name: str = None, project_dir: str = None):
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if project_dir is not None:
            updates.append("project_dir = ?")
            params.append(project_dir)
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(session_id)
        conn.execute(f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?", params)


def delete_session(session_id: int):
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM tool_calls WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))


def add_message(session_id: int, role: str, content: str = None,
                tool_calls: List = None, tool_call_id: str = None) -> int:
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute(
            "INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, json.dumps(tool_calls) if tool_calls else None, tool_call_id)
        )
        return cur.lastrowid


def get_messages(session_id: int) -> List[Dict[str, Any]]:
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at", (session_id,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d["tool_calls"]:
                d["tool_calls"] = json.loads(d["tool_calls"])
            result.append(d)
        return result


def add_tool_call(session_id: int, name: str, args: Dict, result: Dict, status: str):
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO tool_calls (session_id, name, args, result, status) VALUES (?, ?, ?, ?, ?)",
            (session_id, name, json.dumps(args), json.dumps(result), status)
        )


def get_tool_calls(session_id: int) -> List[Dict[str, Any]]:
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM tool_calls WHERE session_id = ? ORDER BY created_at", (session_id,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["args"] = json.loads(d["args"])
            d["result"] = json.loads(d["result"])
            result.append(d)
        return result


def read_agents_md(project_dir: str) -> str:
    path = Path(project_dir).expanduser() / "AGENTS.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def write_agents_md(project_dir: str, content: str):
    path = Path(project_dir).expanduser() / "AGENTS.md"
    path.write_text(content, encoding="utf-8")