import yaml
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional
from .config import load_config

SKILLS_DIR = Path(__file__).parent.parent / "skills"


class Skill:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.manifest: Dict = {}
        self.skill_md: str = ""
        self.tools_module = None
        self._load()

    def _load(self):
        manifest_file = self.path / "manifest.yaml"
        if manifest_file.exists():
            with open(manifest_file) as f:
                self.manifest = yaml.safe_load(f) or {}
        skill_md_file = self.path / "SKILL.md"
        if skill_md_file.exists():
            self.skill_md = skill_md_file.read_text(encoding="utf-8")
        tools_file = self.path / "tools.py"
        if tools_file.exists():
            spec = importlib.util.spec_from_file_location(f"skill_{self.name}_tools", tools_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.tools_module = module

    def get_tools_schema(self) -> List[Dict]:
        if not self.tools_module or not hasattr(self.tools_module, "TOOLS"):
            return []
        return self.tools_module.TOOLS

    def get_tool_functions(self) -> Dict:
        if not self.tools_module:
            return {}
        funcs = {}
        for tool in self.get_tools_schema():
            name = tool["function"]["name"]
            if hasattr(self.tools_module, name):
                funcs[name] = getattr(self.tools_module, name)
        return funcs

    def matches_trigger(self, text: str) -> bool:
        triggers = self.manifest.get("triggers", [])
        text_lower = text.lower()
        return any(t.lower() in text_lower for t in triggers)


def discover_skills() -> Dict[str, Skill]:
    skills = {}
    if not SKILLS_DIR.exists():
        return skills
    for item in SKILLS_DIR.iterdir():
        if item.is_dir() and (item / "manifest.yaml").exists():
            skills[item.name] = Skill(item)
    return skills


def get_enabled_skills(config) -> Dict[str, Skill]:
    all_skills = discover_skills()
    enabled = config.skills.enabled if hasattr(config, 'skills') else []
    return {k: v for k, v in all_skills.items() if k in enabled}


def build_system_prompt(skills: Dict[str, Skill], agents_md: str = "") -> str:
    base = """You are zyvo-clone, a desktop AI agent with tool access.
You can read/write files, run shell commands, fetch URLs, and use skills.
Be concise, practical, and deliver working results."""
    parts = [base]
    if agents_md:
        parts.append(f"\n--- PROJECT MEMORY (AGENTS.md) ---\n{agents_md}")
    for skill in skills.values():
        if skill.skill_md:
            parts.append(f"\n--- SKILL: {skill.name} ---\n{skill.skill_md}")
    return "\n".join(parts)


def get_all_tools(skills: Dict[str, Skill]) -> List[Dict]:
    from .tools import NATIVE_TOOLS
    tools = NATIVE_TOOLS.copy()
    for skill in skills.values():
        tools.extend(skill.get_tools_schema())
    return tools


def get_all_tool_functions(skills: Dict[str, Skill]) -> Dict:
    from .tools import TOOL_FUNCTIONS
    funcs = TOOL_FUNCTIONS.copy()
    for skill in skills.values():
        funcs.update(skill.get_tool_functions())
    return funcs