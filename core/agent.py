"""Agent loop — OpenAI-compatible streaming over plain httpx (no litellm)."""
import json
import logging
from typing import Any, AsyncGenerator, Dict, List

import httpx

from .config import load_config
from .providers import get_completion_config
from .tools import execute_tool_async
from .skills import get_enabled_skills, build_system_prompt, get_all_tools
from .memory import get_messages, add_message, add_tool_call

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 10


class Agent:
    def __init__(self, session_id: int, project_dir: str = ""):
        self.session_id = session_id
        self.project_dir = project_dir
        self.config = load_config()
        self.skills = get_enabled_skills(self.config)
        self.agents_md = ""
        if project_dir:
            from .memory import read_agents_md
            self.agents_md = read_agents_md(project_dir)

    def _get_system_prompt(self) -> str:
        return build_system_prompt(self.skills, self.agents_md)

    async def _stream(self, messages: List[Dict], tools: List[Dict]) -> AsyncGenerator[Dict, None]:
        params = get_completion_config(self.config)
        base = params["api_base"]
        if not base:
            raise RuntimeError("Base URL não configurado para o provedor ativo")
        headers = {"Content-Type": "application/json"}
        if params.get("api_key"):
            headers["Authorization"] = f"Bearer {params['api_key']}"
        if params["provider"] == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/jonataprezende-commits/volt-ai"
            headers["X-Title"] = "Volt-AI"

        payload: Dict[str, Any] = {
            "model": params["model"],
            "messages": messages,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        timeout = httpx.Timeout(300.0, connect=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST", f"{base}/chat/completions", json=payload, headers=headers
            ) as resp:
                if resp.status_code >= 400:
                    body = (await resp.aread()).decode("utf-8", "replace")
                    raise RuntimeError(f"HTTP {resp.status_code}: {body[:400]}")
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        return
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue

    async def chat(self, user_message: str) -> AsyncGenerator[Dict[str, Any], None]:
        messages = self._build_messages(user_message)
        tools = get_all_tools(self.skills)

        add_message(self.session_id, "user", user_message)

        iteration = 0
        while iteration < MAX_TOOL_ITERATIONS:
            iteration += 1
            tool_calls: List[Dict[str, str]] = []
            content_parts: List[str] = []

            try:
                async for chunk in self._stream(messages, tools):
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    if delta.get("content"):
                        content_parts.append(delta["content"])
                        yield {"type": "content", "content": delta["content"]}
                    for tc in delta.get("tool_calls") or []:
                        idx = tc.get("index", 0)
                        while len(tool_calls) <= idx:
                            tool_calls.append({"id": "", "name": "", "arguments": ""})
                        slot = tool_calls[idx]
                        if tc.get("id"):
                            slot["id"] = tc["id"]
                        fn = tc.get("function") or {}
                        if fn.get("name"):
                            slot["name"] = fn["name"]
                        if fn.get("arguments"):
                            slot["arguments"] += fn["arguments"]
            except Exception as e:
                yield {"type": "error", "content": f"LLM error: {e}"}
                return

            if tool_calls:
                for tc in tool_calls:
                    if not tc["name"]:
                        continue
                    yield {"type": "tool_start", "name": tc["name"], "id": tc["id"]}
                    try:
                        args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                    except json.JSONDecodeError:
                        args = {}
                    result = await execute_tool_async(tc["name"], args)
                    status = "error" if "error" in result else "done"
                    add_tool_call(self.session_id, tc["name"], args, result, status)
                    yield {"type": "tool_result", "name": tc["name"], "id": tc["id"], "result": result}
                    messages.append({
                        "role": "assistant",
                        "content": "".join(content_parts) or "",
                        "tool_calls": [{
                            "id": tc["id"],
                            "type": "function",
                            "function": {"name": tc["name"], "arguments": tc["arguments"]},
                        }],
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(result, ensure_ascii=False),
                    })
                    add_message(self.session_id, "tool",
                                json.dumps(result, ensure_ascii=False),
                                tool_call_id=tc["id"])
                continue

            full_content = "".join(content_parts)
            if full_content:
                add_message(self.session_id, "assistant", full_content)
            yield {"type": "done", "content": full_content}
            break
        else:
            yield {"type": "error", "content": f"Max tool iterations ({MAX_TOOL_ITERATIONS}) reached"}

    def _build_messages(self, user_message: str) -> List[Dict]:
        messages: List[Dict] = [{"role": "system", "content": self._get_system_prompt()}]
        history = get_messages(self.session_id)
        for msg in history[-20:]:
            m: Dict[str, Any] = {"role": msg["role"]}
            if msg["content"]:
                m["content"] = msg["content"]
            if msg.get("tool_calls"):
                m["tool_calls"] = msg["tool_calls"]
            messages.append(m)
        messages.append({"role": "user", "content": user_message})
        return messages


def run_one_shot(prompt: str, project_dir: str = "") -> str:
    import asyncio
    from .memory import create_session

    session_id = create_session("cli-one-shot", project_dir)
    agent = Agent(session_id, project_dir)
    result = ""

    async def collect():
        nonlocal result
        async for chunk in agent.chat(prompt):
            if chunk["type"] == "content":
                result += chunk["content"]
            elif chunk["type"] == "error":
                result = f"Error: {chunk['content']}"
                break

    asyncio.run(collect())
    return result
