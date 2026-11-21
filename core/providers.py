"""Provider registry — OpenAI-compatible chat/completions endpoints only.

No litellm: every supported provider speaks the OpenAI wire format, so plain
httpx does the job and the install stays pure-Python (Python 3.14 / Termux).
"""
from typing import Dict, Any, Optional, List

from .config import AppConfig, ProviderConfig, DEFAULT_PROVIDERS, get_api_key

__all__ = [
    "DEFAULT_PROVIDERS", "get_provider_list", "set_active_provider",
    "update_provider", "get_completion_config", "get_litellm_config",
]


def get_provider_list(config: AppConfig) -> List[Dict[str, Any]]:
    result = []
    for pid, pconf in config.providers.items():
        default = DEFAULT_PROVIDERS.get(pid, {})
        result.append({
            "id": pid,
            "label": default.get("label", pid),
            "base_url": pconf.base_url or default.get("base_url", ""),
            "model": pconf.model or default.get("model", ""),
            "has_key": bool(get_api_key(pid, config)),
            "is_active": pid == config.active_provider,
        })
    return result


def set_active_provider(provider_id: str, config: AppConfig) -> bool:
    if provider_id in config.providers:
        config.active_provider = provider_id
        return True
    return False


def update_provider(provider_id: str, base_url: str, model: str, config: AppConfig) -> bool:
    if provider_id not in config.providers:
        config.providers[provider_id] = ProviderConfig(api_key_ref=provider_id)
    config.providers[provider_id].base_url = base_url
    config.providers[provider_id].model = model
    return True


def get_completion_config(config: AppConfig, provider_id: Optional[str] = None) -> Dict[str, Any]:
    """Everything the HTTP client needs for one completion call."""
    pid = provider_id or config.active_provider
    provider = config.providers.get(pid)
    default = DEFAULT_PROVIDERS.get(pid, {})
    return {
        "provider": pid,
        "model": (provider.model if provider else "") or default.get("model", ""),
        "api_key": get_api_key(pid, config),
        "api_base": ((provider.base_url if provider else "") or default.get("base_url", "")).rstrip("/"),
    }


# Backwards-compatible alias (older imports)
def get_litellm_config(config: AppConfig, provider_id: Optional[str] = None) -> Dict[str, Any]:
    return get_completion_config(config, provider_id)
