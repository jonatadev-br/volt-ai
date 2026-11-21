"""Unit tests — run with: pytest -q  (pytest is a dev-only dependency)."""
import tempfile
from pathlib import Path

import pytest

import core.config as cfg
from core.config import AppConfig, ProviderConfig, load_config, save_config
from core.tools import _validate_path, _check_blocklist, read_file, write_file, list_dir
from core.skills import discover_skills, Skill


@pytest.fixture
def temp_home(monkeypatch):
    tmp = Path(tempfile.mkdtemp(prefix="volt-test-"))
    monkeypatch.setattr(cfg, "CONFIG_DIR", tmp)
    monkeypatch.setattr(cfg, "CONFIG_FILE", tmp / "config.yaml")
    monkeypatch.setattr(cfg, "KEYS_FILE", tmp / "keys.json")
    monkeypatch.setattr(cfg, "_keyring_state", False)  # force file backend
    return tmp


def test_config_roundtrip(temp_home):
    config = AppConfig(
        active_provider="test",
        providers={"test": ProviderConfig(base_url="http://test", model="m", api_key_ref="test")},
    )
    save_config(config)
    loaded = load_config()
    assert loaded.active_provider == "test"
    assert loaded.providers["test"].model == "m"


def test_fresh_config_seeds_providers(temp_home):
    loaded = load_config()
    assert "nvidia_nim" in loaded.providers
    assert "openrouter" in loaded.providers
    assert loaded.skills.enabled, "fresh install should enable shipped skills"


def test_api_key_file_backend(temp_home):
    config = load_config()
    assert cfg.set_api_key("nvidia_nim", "sk-test", config) is True
    assert cfg.get_api_key("nvidia_nim", config) == "sk-test"
    assert cfg.KEYS_FILE.stat().st_mode & 0o777 == 0o600
    assert cfg.delete_api_key("nvidia_nim", config) is True
    assert cfg.get_api_key("nvidia_nim", config) is None


def test_blocklist():
    assert _check_blocklist("rm -rf /") is True
    assert _check_blocklist("dd if=/dev/zero") is True
    assert _check_blocklist("ls -la") is False
    assert _check_blocklist("echo hello") is False


def test_path_traversal(temp_home):
    root = temp_home
    (root / "test.txt").write_text("hello")
    config = load_config()
    config.safety.fs_root = str(root)
    save_config(config)

    assert _validate_path(str(root / "test.txt")).exists()
    with pytest.raises(PermissionError):
        _validate_path("/etc/passwd")


def test_tools_fs(temp_home):
    config = load_config()
    config.safety.fs_root = str(temp_home)
    save_config(config)

    assert write_file(str(temp_home / "test.txt"), "content")["success"]
    assert read_file(str(temp_home / "test.txt"))["content"] == "content"
    listing = list_dir(str(temp_home))
    assert any(i["name"] == "test.txt" for i in listing["items"])


def test_skills_discovery():
    skills = discover_skills()
    for name in ("webdev", "motion-animation", "research", "shell-assist", "code-review"):
        assert name in skills, f"missing skill {name}"
    for name, skill in skills.items():
        assert skill.manifest.get("name") == name
        assert "description" in skill.manifest


def test_skill_webdev_tools():
    skill = Skill(Path(__file__).parent / "skills" / "webdev")
    tools = skill.get_tools_schema()
    assert tools[0]["function"]["name"] == "scaffold_web"
    assert "scaffold_web" in skill.get_tool_functions()


def test_skill_shell_assist():
    skill = Skill(Path(__file__).parent / "skills" / "shell-assist")
    names = [t["function"]["name"] for t in skill.get_tools_schema()]
    assert "explain_command" in names
    assert "explain_and_confirm" in names
