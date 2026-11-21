import litellm
import json
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
from .config import load_config, get_litellm_config
from .tools import execute_tool, get_all_tool_functions
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
        self.tool_functions = get_all_tool_functions(self.skills)
        self.agents_md = ""
        if project_dir:
            from .memory import read_agents_md
            self.agents_md = read_agents_md(project_dir)

    def _get_system_prompt(self) -> str:
        return build_system_prompt(self.skills, self.agents_md)

    def _get_litellm_params(self) -> Dict[str, Any]:
        return get_litellm_config(self.config)

    async def chat(self, user_message: str) -> AsyncGenerator[Dict[str, Any], None]:
        messages = self._build_messages(user_message)
        tools = get_all_tools(self.skills)
        params = self._get_litellm_params()

        add_message(self.session_id, "user", user_message)

        iteration = 0
        while iteration < MAX_TOOL_ITERATIONS:
            iteration += 1
            try:
                response = litellm.completion(
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    stream=True,
                    **params
                )
            except Exception as e:
                yield {"type": "error", "content": f"LLM error: {e}"}
                return

            tool_calls = []
            content_parts = []

            for chunk in response:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta.content:
                    content_parts.append(delta.content)
                    yield {"type": "content", "content": delta.content}
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        if tc.index >= len(tool_calls):
                            tool_calls.append({"id": "", "name": "", "arguments": ""})
                        t = tool_calls[tc.index]
                        if tc.id:
                            t["id"] = tc.id
                        if tc.function.name:
                            t["name"] = tc.function.name
                        if tc.function.arguments:
                            t["arguments"] += tc.function.arguments

            if tool_calls:
                for tc in tool_calls:
                    yield {"type": "tool_start", "name": tc["name"], "id": tc["id"]}
                    try:
                        args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                    except json.JSONDecodeError:
                        args = {}
                    result = execute_tool(tc["name"], args)
                    add_tool_call(self.session_id, tc["name"], args, result, "done" if "error" not in result else "error")
                    yield {"type": "tool_result", "name": tc["name"], "id": tc["id"], "result": result}
                    messages.append({
                        "role": "assistant",
                        "tool_calls": [{"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": tc["arguments"]}}]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(result)
                    })
                continue

            full_content = "".join(content_parts)
            if full_content:
                add_message(self.session_id, "assistant", full_content)
            yield {"type": "done", "content": full_content}
            break
        else:
            yield {"type": "error", "content": f"Max tool iterations ({MAX_TOOL_ITERATIONS}) reached"}

    def _build_messages(self, user_message: str) -> List[Dict]:
        messages = [{"role": "system", "content": self._get_system_prompt()}]
        history = get_messages(self.session_id)
        for msg in history[-20:]:
            if msg["role"] == "tool":
                continue
            m = {"role": msg["role"]}
            if msg["content"]:
                m["content"] = msg["content"]
            if msg["tool_calls"]:
                m["tool_calls"] = msg["tool_calls"]
            if msg["tool_call_id"]:
                m["tool_call_id"] = msg["tool_call_id"]
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