import pytest
import tempfile
import os
from pathlib import Path
from core.config import load_config, save_config, AppConfig, ProviderConfig
from core.tools import _validate_path, _check_blocklist, read_file, write_file, list_dir
from core.skills import discover_skills, Skill


def test_config_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["HOME"] = tmp
        config = AppConfig(
            active_provider="test",
            providers={"test": ProviderConfig(base_url="http://test", model="test-model", api_key_ref="test")},
        )
        save_config(config)
        loaded = load_config()
        assert loaded.active_provider == "test"
        assert "test" in loaded.providers


def test_blocklist():
    assert _check_blocklist("rm -rf /") == True
    assert _check_blocklist("rm -rf /*") == True
    assert _check_blocklist("dd if=/dev/zero") == True
    assert _check_blocklist("ls -la") == False
    assert _check_blocklist("echo hello") == False


def test_path_traversal():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        test_file = root / "test.txt"
        test_file.write_text("hello")
        
        # Valid path
        assert _validate_path(str(test_file)).exists()
        
        # Traversal attempt
        try:
            _validate_path("../../../etc/passwd")
            assert False, "Should have raised"
        except PermissionError:
            pass


def test_tools_fs():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["HOME"] = tmp
        from core.config import CONFIG_DIR
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # write
        res = write_file("test.txt", "content")
        assert res["success"]
        
        # read
        res = read_file("test.txt")
        assert res["content"] == "content"
        
        # list
        res = list_dir(".")
        assert any(item["name"] == "test.txt" for item in res["items"])


def test_skills_discovery():
    skills = discover_skills()
    assert "webdev" in skills
    assert "motion-animation" in skills
    assert "research" in skills
    assert "shell-assist" in skills
    assert "code-review" in skills
    
    for name, skill in skills.items():
        assert skill.manifest.get("name") == name
        assert "description" in skill.manifest
        assert "triggers" in skill.manifest


def test_skill_webdev_tools():
    skill = Skill(Path(__file__).parent / "skills" / "webdev")
    tools = skill.get_tools_schema()
    assert len(tools) == 1
    assert tools[0]["function"]["name"] == "scaffold_web"
    
    funcs = skill.get_tool_functions()
    assert "scaffold_web" in funcs


def test_skill_shell_assist():
    skill = Skill(Path(__file__).parent / "skills" / "shell-assist")
    tools = skill.get_tools_schema()
    names = [t["function"]["name"] for t in tools]
    assert "explain_command" in names
    assert "explain_and_confirm" in names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])