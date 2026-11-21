# Volt-AI

Desktop AI agent inspired by Zyvo AI — local GUI, multi-provider (NVIDIA NIM, OpenAI, Anthropic, Groq, OpenRouter, Ollama), extensible skills system, CLI + Web UI.

## Features

- **Multi-provider**: NVIDIA NIM (primary), OpenAI, Anthropic, Groq, OpenRouter, Ollama, custom OpenAI-compatible
- **GUI**: Local web interface at `http://127.0.0.1:8765` (chat, config, skills, project memory, sessions)
- **CLI**: `volt-ai run "prompt"`, `volt-ai chat`, `volt-ai skills list`, etc.
- **Skills**: webdev, motion-animation, research, shell-assist, code-review (extensible)
- **Memory**: AGENTS.md per project + SQLite session history
- **Security**: API keys in system keyring, shell confirmations, path traversal protection, command blocklist
- **Build**: PyInstaller onefile executables for Windows/macOS/Linux

## Quick Start

### Install on Termux (Android) — One Command

```bash
curl -fsSL https://raw.githubusercontent.com/jonataprezende-commits/volt-ai/main/install-termux.sh | bash
```

Then run:
```bash
volt-ai chat          # GUI at http://127.0.0.1:8765
volt-ai run "prompt"  # CLI one-shot
```

> **Requires**: Termux on ARM64 (aarch64) — most modern Android phones.
> Binary is downloaded from GitHub Releases (`termux-latest` tag).

### Install (Development / Desktop)

```bash
git clone <repo>
cd volt-ai
pip install -r requirements.txt
cp config.yaml ~/.volt-ai/config.yaml  # auto-created on first run
volt-ai chat
```

### Configure API Keys

1. Open GUI (`volt-ai chat`)
2. Go to **Config** tab
3. Enter your NVIDIA NIM API key (or other provider)
4. Click **Test** to verify
5. Click **Save**

Get NVIDIA NIM key: https://integrate.api.nvidia.com/v1 (requires NVIDIA account)

### Run from Executable

```bash
# Linux/macOS
./dist/Volt-AI

# Windows
dist\Volt-AI.exe
```

Opens browser automatically at `http://127.0.0.1:8765`.

## CLI Usage

```bash
# One-shot prompt
volt-ai run "Create a landing page in ./my-project"

# Start GUI
volt-ai chat

# Skills
volt-ai skills list
volt-ai skills enable webdev

# Config
volt-ai config show
volt-ai config set-provider nvidia_nim
volt-ai config set-key nvidia_nim "your-key"
volt-ai config test nvidia_nim
```

## Skills

| Skill | Description | Trigger Words |
|-------|-------------|---------------|
| webdev | Scaffold landing page, portfolio, blog | landing page, portfolio, blog, website |
| motion-animation | GSAP animations for recording | animation, gsap, motion |
| research | Fetch URLs + structured summary | research, search, summarize |
| shell-assist | Explain commands, block destructive | shell, command, bash |
| code-review | Review code for issues | review, audit, lint |

### Using Skills

In chat, just ask: *"Create a landing page for my SaaS"* → webdev skill activates automatically.

Or manually toggle in **Skills** tab.

## Creating Custom Skills

Create a folder in `skills/your-skill/` with:

```
skills/your-skill/
├── manifest.yaml    # name, description, triggers, version
├── SKILL.md         # Instructions injected into system prompt
└── tools.py         # Optional: TOOLS list + functions
```

**manifest.yaml**
```yaml
name: your-skill
description: What it does
version: "1.0"
triggers:
  - keyword1
  - keyword2
dependencies: []
```

**SKILL.md** — Markdown instructions for the agent.

**tools.py** — Export `TOOLS` list (OpenAI function schema) and implement functions.

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "your_tool",
            "description": "What it does",
            "parameters": {
                "type": "object",
                "properties": {
                    "arg1": {"type": "string", "description": "..."}
                },
                "required": ["arg1"]
            }
        }
    }
]

def your_tool(arg1: str) -> dict:
    return {"success": True, "result": f"Processed {arg1}"}
```

Restart Volt-AI to load new skills.

## Building Executables

### Linux
```bash
cd build
chmod +x build_linux.sh
./build_linux.sh
# Output: dist/Volt-AI
```

### Windows
```bat
cd build
build_win.bat
# Output: dist\Volt-AI.exe
```

### macOS
```bash
cd build
chmod +x build_mac.sh
./build_mac.sh
# Output: dist/Volt-AI
# Optional .app: py2applet --make-setup ../main.py && python setup.py py2app
```

### Termux (Android) — Local Build
```bash
# Run on your phone in Termux
chmod +x build_termux_local.sh
./build_termux_local.sh
# Output: dist/Volt-AI (copies to ~/.local/bin/volt-ai)
```

**Requirements**: PyInstaller, Python 3.11+, all dependencies from `requirements.txt`.

## Configuration

Config file: `~/.volt-ai/config.yaml`

```yaml
active_provider: nvidia_nim
providers:
  nvidia_nim:
    base_url: "https://integrate.api.nvidia.com/v1"
    model: "meta/llama-3.3-70b-instruct"
    api_key_ref: "nvidia_nim"
skills:
  enabled: [webdev, motion-animation, research, shell-assist, code-review]
safety:
  shell_confirm: true
  fs_root: null  # null = home directory
server:
  host: "127.0.0.1"
  port: 8765
```

## Project Structure

```
volt-ai/
├── main.py              # FastAPI entrypoint
├── cli.py               # Typer CLI
├── core/
│   ├── agent.py         # Agent loop (LiteLLM + tools)
│   ├── config.py        # Config + keyring
│   ├── providers.py     # Provider registry
│   ├── memory.py        # SQLite + AGENTS.md
│   ├── tools.py         # Native tools (fs, shell, fetch)
│   └── skills.py        # Skills loader
├── skills/              # Built-in skills
├── frontend/            # Vanilla HTML/JS GUI
├── build/               # PyInstaller spec + scripts
└── README.md
```

## Acceptance Criteria

1. ✅ GUI opens in browser <3s
2. ✅ NVIDIA NIM key config + test works
3. ✅ Streaming chat + tool calls display
4. ✅ webdev skill creates files + opens browser
5. ✅ shell-assist confirms before running
6. ✅ Executable runs on clean machine (no Python)
7. ✅ `volt-ai run "..."` works in CLI
8. ✅ README documents usage + skill creation

## License

MIT — fork, modify, ship.