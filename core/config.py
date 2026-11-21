import os
import yaml
import keyring
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".volt-ai"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
KEYRING_SERVICE = "Volt-AI"


class ProviderConfig(BaseModel):
    base_url: str = ""
    model: str = ""
    api_key_ref: str = ""


class SafetyConfig(BaseModel):
    shell_confirm: bool = True
    fs_root: Optional[str] = None
    blocklist: list[str] = Field(default_factory=lambda: [
        "rm -rf /", "rm -rf /*", "dd if=", "mkfs", "shutdown", "reboot",
        ":(){ :|:& };:", "fork"
    ])


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8765


class SkillsConfig(BaseModel):
    enabled: list[str] = Field(default_factory=list)


class AppConfig(BaseModel):
    active_provider: str = "nvidia_nim"
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "logs").mkdir(parents=True, exist_ok=True)


def load_config() -> AppConfig:
    ensure_config_dir()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            data = yaml.safe_load(f) or {}
        return AppConfig(**data)
    return AppConfig()


def save_config(config: AppConfig):
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config.model_dump(), f)


def get_api_key(provider_id: str, config: AppConfig) -> Optional[str]:
    provider = config.providers.get(provider_id)
    if not provider or not provider.api_key_ref:
        return None
    try:
        return keyring.get_password(KEYRING_SERVICE, provider.api_key_ref)
    except Exception as e:
        logger.warning(f"Keyring read failed: {e}")
        return None


def set_api_key(provider_id: str, key: str, config: AppConfig) -> bool:
    provider = config.providers.get(provider_id)
    if not provider or not provider.api_key_ref:
        return False
    try:
        keyring.set_password(KEYRING_SERVICE, provider.api_key_ref, key)
        return True
    except Exception as e:
        logger.warning(f"Keyring write failed: {e}")
        return False


def delete_api_key(provider_id: str, config: AppConfig) -> bool:
    provider = config.providers.get(provider_id)
    if not provider or not provider.api_key_ref:
        return False
    try:
        keyring.delete_password(KEYRING_SERVICE, provider.api_key_ref)
        return True
    except Exception:
        return False


def test_provider_connection(provider_id: str, config: AppConfig) -> tuple[bool, str]:
    import litellm
    provider = config.providers.get(provider_id)
    if not provider:
        return False, "Provider not found"
    api_key = get_api_key(provider_id, config)
    if not api_key:
        return False, "API key not set"
    try:
        litellm.api_key = api_key
        litellm.api_base = provider.base_url
        response = litellm.completion(
            model=provider.model,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1,
            timeout=10
        )
        return True, "OK"
    except Exception as e:
        return False, str(e)