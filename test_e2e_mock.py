"""End-to-end test of the agent loop against a local mock OpenAI-compatible server.

Proves: SSE streaming parse, tool-call accumulation, tool execution, and the
second round-trip carrying the tool result. No API key, no network.
"""
import asyncio
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.responses import StreamingResponse
from starlette.routing import Route

sys.path.insert(0, str(Path(__file__).parent))

PORT = 8811
BASE = f"http://127.0.0.1:{PORT}/v1"


def _sse(obj) -> str:
    return f"data: {json.dumps(obj)}\n\n"


async def completions(request):
    body = await request.json()
    messages = body.get("messages", [])
    saw_tool_result = any(m.get("role") == "tool" for m in messages)

    async def gen():
        if not saw_tool_result:
            # Round 1: emit a streamed tool call (split across chunks)
            yield _sse({"choices": [{"delta": {"tool_calls": [{
                "index": 0, "id": "call_abc",
                "function": {"name": "list_dir", "arguments": '{"path"'}}]}}]})
            yield _sse({"choices": [{"delta": {"tool_calls": [{
                "index": 0,
                "function": {"arguments": ': "."}'}}]}}]})
        else:
            # Round 2: stream the final answer
            for piece in ["Olá", ", ", "mundo", "!"]:
                yield _sse({"choices": [{"delta": {"content": piece}}]})
                await asyncio.sleep(0.01)
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


mock_app = Starlette(routes=[Route("/v1/chat/completions", completions, methods=["POST"])])


def start_mock():
    config = uvicorn.Config(mock_app, host="127.0.0.1", port=PORT, log_level="error")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(50):
        time.sleep(0.1)
        if server.started:
            return server
    raise RuntimeError("mock server failed to start")


def main():
    tmp = Path(tempfile.mkdtemp(prefix="volt-test-"))
    import core.config as cfg

    cfg.CONFIG_DIR = tmp
    cfg.CONFIG_FILE = tmp / "config.yaml"
    cfg.KEYS_FILE = tmp / "keys.json"

    config = cfg.load_config()
    config.active_provider = "openai_compatible"
    config.providers["openai_compatible"].base_url = BASE
    config.providers["openai_compatible"].model = "mock-model"
    cfg.save_config(config)
    assert cfg.set_api_key("openai_compatible", "test-key", config), "key save failed"

    from core.agent import Agent
    from core.memory import create_session

    sid = create_session("e2e", str(tmp))
    agent = Agent(sid, str(tmp))

    events = []

    async def drive():
        async for chunk in agent.chat("liste os arquivos"):
            events.append(chunk)

    asyncio.run(drive())

    kinds = [e["type"] for e in events]
    print("events:", kinds)
    content = "".join(e["content"] for e in events if e["type"] == "content")
    assert "tool_start" in kinds, "tool_start missing"
    assert "tool_result" in kinds, "tool_result missing"
    tr = next(e for e in events if e["type"] == "tool_result")
    assert "items" in tr["result"] or "error" in tr["result"], f"bad tool result: {tr}"
    assert content == "Olá, mundo!", f"bad streamed content: {content!r}"
    assert kinds[-1] == "done"
    print("TOOL RESULT:", json.dumps(tr["result"])[:120])
    print("CONTENT:", content)
    print("E2E OK")


if __name__ == "__main__":
    server = start_mock()
    try:
        main()
    finally:
        server.should_exit = True
