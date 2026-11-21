"""Config layer — stdlib dataclasses only (no pydantic, works on Python 3.14/Termux).

API keys: try the OS keyring when it actually works (desktop), otherwise fall
back to a 0600 JSON file at ~/.volt-ai/keys.json (Termux has no dbus).
"""
import os
import json
import logging
from dataclasses import dataclass, field, asdict, fields, is_dataclass
from pathlib import Path
from typing import Dict, Any, Optional, List

import yaml

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".volt-ai"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
KEYS_FILE = CONFIG_DIR / "keys.json"
KEYRING_SERVICE = "Volt-AI"

DEFAULT_PROVIDERS = {
    "nvidia_nim": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "meta/llama-3.3-70b-instruct",
        "label": "NVIDIA NIM",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "label": "OpenAI",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "model": "claude-3-5-sonnet-20241022",
        "label": "Anthropic",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
        "label": "Groq",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "meta-llama/llama-3.3-70b-instruct",
        "label": "OpenRouter",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "model": "llama3.1:70b",
        "label": "Ollama (local)",
    },
    "openai_compatible": {
        "base_url": "",
        "model": "",
        "label": "OpenAI-Compatible (custom)",
    },
}


@dataclass
class ProviderConfig:
    base_url: str = ""
    model: str = ""
    api_key_ref: str = ""


@dataclass
class SafetyConfig:
    shell_confirm: bool = True
    fs_root: Optional[str] = None
    blocklist: List[str] = field(default_factory=lambda: [
        "rm -rf /", "rm -rf /*", "dd if=", "mkfs", "shutdown", "reboot",
        ":(){ :|:& };:", "fork",
    ])


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8765


@dataclass
class SkillsConfig:
    enabled: List[str] = field(default_factory=list)


@dataclass
class AppConfig:
    active_provider: str = "nvidia_nim"
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
    skills: SkillsConfig = field(default_factory=SkillsConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    server: ServerConfig = field(default_factory=ServerConfig)


def _default_providers() -> Dict[str, ProviderConfig]:
    return {
        pid: ProviderConfig(
            base_url=p["base_url"], model=p["model"], api_key_ref=pid
        )
        for pid, p in DEFAULT_PROVIDERS.items()
    }


def _coerce(cls, data: Any):
    """Build a dataclass instance from a plain dict, ignoring unknown keys."""
    if not isinstance(data, dict):
        return cls()
    kwargs = {}
    for f in fields(cls):
        if f.name not in data:
            continue
        value = data[f.name]
        if is_dataclass(f.type) and isinstance(value, dict):
            kwargs[f.name] = _coerce(f.type, value)
        else:
            kwargs[f.name] = value
    return cls(**kwargs)


def _default_skills() -> List[str]:
    """Enable every skill shipped in ./skills on a fresh install."""
    skills_dir = Path(__file__).parent.parent / "skills"
    if not skills_dir.is_dir():
        return []
    return sorted(
        p.name for p in skills_dir.iterdir()
        if p.is_dir() and (p / "manifest.yaml").exists()
    )


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "logs").mkdir(parents=True, exist_ok=True)


def load_config() -> AppConfig:
    ensure_config_dir()
    if not CONFIG_FILE.exists():
        config = AppConfig(
            providers=_default_providers(),
            skills=SkillsConfig(enabled=_default_skills()),
        )
        save_config(config)
        return config
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning("Config read failed (%s), using defaults", e)
        data = {}

    config = AppConfig()
    config.active_provider = data.get("active_provider", config.active_provider)
    config.skills = _coerce(SkillsConfig, data.get("skills", {}))
    config.safety = _coerce(SafetyConfig, data.get("safety", {}))
    config.server = _coerce(ServerConfig, data.get("server", {}))

    providers = _default_providers()
    for pid, pdata in (data.get("providers") or {}).items():
        if isinstance(pdata, dict):
            providers[pid] = _coerce(ProviderConfig, pdata)
            if not providers[pid].api_key_ref:
                providers[pid].api_key_ref = pid
    config.providers = providers
    return config


def save_config(config: AppConfig):
    ensure_config_dir()
    data = asdict(config)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


# ---------------------------------------------------------------- key storage

_keyring_state = None  # None = untested, True = works, False = unusable


def _keyring_works() -> bool:
    global _keyring_state
    if _keyring_state is not None:
        return _keyring_state
    try:
        import keyring
        from keyring.errors import KeyringError
        try:
            keyring.get_password(KEYRING_SERVICE, "__probe__")
            _keyring_state = True
        except KeyringError:
            _keyring_state = False
        except Exception:
            _keyring_state = False
    except Exception:
        _keyring_state = False
    if not _keyring_state:
        logger.info("Keyring unavailable — using %s", KEYS_FILE)
    return _keyring_state


def _read_keys_file() -> Dict[str, str]:
    if not KEYS_FILE.exists():
        return {}
    try:
        return json.loads(KEYS_FILE.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _write_keys_file(keys: Dict[str, str]):
    ensure_config_dir()
    tmp = KEYS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(keys, indent=2), encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(KEYS_FILE)


def get_api_key(provider_id: str, config: AppConfig) -> Optional[str]:
    provider = config.providers.get(provider_id)
    if not provider or not provider.api_key_ref:
        return None
    ref = provider.api_key_ref
    if _keyring_works():
        try:
            import keyring
            value = keyring.get_password(KEYRING_SERVICE, ref)
            if value:
                return value
        except Exception as e:
            logger.warning("Keyring read failed: %s", e)
    return _read_keys_file().get(ref)


def set_api_key(provider_id: str, key: str, config: AppConfig) -> bool:
    provider = config.providers.get(provider_id)
    if not provider or not provider.api_key_ref:
        return False
    ref = provider.api_key_ref
    if _keyring_works():
        try:
            import keyring
            keyring.set_password(KEYRING_SERVICE, ref, key)
            return True
        except Exception as e:
            logger.warning("Keyring write failed: %s", e)
    keys = _read_keys_file()
    keys[ref] = key
    _write_keys_file(keys)
    return True


def delete_api_key(provider_id: str, config: AppConfig) -> bool:
    provider = config.providers.get(provider_id)
    if not provider or not provider.api_key_ref:
        return False
    ref = provider.api_key_ref
    removed = False
    if _keyring_works():
        try:
            import keyring
            keyring.delete_password(KEYRING_SERVICE, ref)
            removed = True
        except Exception:
            pass
    keys = _read_keys_file()
    if ref in keys:
        del keys[ref]
        _write_keys_file(keys)
        removed = True
    return removed


def test_provider_connection(provider_id: str, config: AppConfig) -> tuple:
    """One tiny non-streaming call to prove the key + endpoint work."""
    import httpx
    from .providers import get_completion_config

    if provider_id not in config.providers:
        return False, "Provider not found"
    api_key = get_api_key(provider_id, config)
    if not api_key:
        return False, "API key not set"
    params = get_completion_config(config, provider_id)
    base_url = (params.get("api_base") or "").rstrip("/")
    if not base_url:
        return False, "Base URL not set"
    try:
        resp = httpx.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": params["model"],
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1,
                "stream": False,
            },
            timeout=20,
        )
        if resp.status_code >= 400:
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
        return True, "OK"
    except Exception as e:
        return False, str(e)
