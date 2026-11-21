import litellm
from typing import Dict, Any, Optional, List
from .config import AppConfig, get_api_key

DEFAULT_PROVIDERS = {
    "nvidia_nim": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "meta/llama-3.3-70b-instruct",
        "label": "NVIDIA NIM",
        "prefix": "nvidia_nim"
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "label": "OpenAI",
        "prefix": "openai"
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "model": "claude-3-5-sonnet-20241022",
        "label": "Anthropic (via LiteLLM)",
        "prefix": "anthropic"
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
        "label": "Groq",
        "prefix": "openai"
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "meta-llama/llama-3.3-70b-instruct",
        "label": "OpenRouter",
        "prefix": "openai"
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "model": "llama3.1:70b",
        "label": "Ollama (local)",
        "prefix": "openai"
    },
    "openai_compatible": {
        "base_url": "",
        "model": "",
        "label": "OpenAI-Compatible (custom)",
        "prefix": "openai"
    }
}


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
            "is_active": pid == config.active_provider
        })
    return result


def set_active_provider(provider_id: str, config: AppConfig) -> bool:
    if provider_id in config.providers:
        config.active_provider = provider_id
        return True
    return False


def update_provider(provider_id: str, base_url: str, model: str, config: AppConfig) -> bool:
    if provider_id not in config.providers:
        config.providers[provider_id] = type(config.providers[provider_id])()
    config.providers[provider_id].base_url = base_url
    config.providers[provider_id].model = model
    return True


def get_litellm_config(config: AppConfig, provider_id: Optional[str] = None) -> Dict[str, Any]:
    pid = provider_id or config.active_provider
    provider = config.providers.get(pid)
    default = DEFAULT_PROVIDERS.get(pid, {})
    api_key = get_api_key(pid, config)
    prefix = default.get("prefix", "openai")
    if pid == "anthropic":
        prefix = "anthropic"
    elif pid == "ollama":
        prefix = "ollama"
    return {
        "model": provider.model or default.get("model", ""),
        "api_key": api_key,
        "api_base": provider.base_url or default.get("base_url", ""),
        "custom_llm_provider": prefix
    }