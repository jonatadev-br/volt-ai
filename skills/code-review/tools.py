import os
import ast
import re
from pathlib import Path
from typing import Dict, Any, List

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

def review_code(path: str, focus: str = "") -> Dict[str, Any]:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"error": f"Path not found: {path}"}
    
    issues = []
    
    if p.is_file():
        issues.extend(review_file(p, focus))
    else:
        for ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml"):
            for f in p.rglob(f"*{ext}"):
                issues.extend(review_file(f, focus))
    
    issues.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 5))
    
    counts = {s: 0 for s in SEVERITY_ORDER}
    for i in issues:
        counts[i["severity"]] = counts.get(i["severity"], 0) + 1
    
    return {
        "issues": issues,
        "summary": {
            "total_files": len(set(i["file"] for i in issues)),
            "total_issues": len(issues),
            "by_severity": counts
        }
    }


def review_file(filepath: Path, focus: str) -> List[Dict]:
    issues = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
    except Exception:
        return issues
    
    rel_path = str(filepath)
    
    if filepath.suffix == ".py":
        issues.extend(review_python(filepath, content, lines, focus))
    elif filepath.suffix in (".js", ".ts", ".jsx", ".tsx"):
        issues.extend(review_js(filepath, content, lines, focus))
    
    issues.extend(review_general(filepath, content, lines, focus))
    
    return issues


def review_python(filepath: Path, content: str, lines: List[str], focus: str) -> List[Dict]:
    issues = []
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        issues.append({"file": str(filepath), "line": e.lineno or 1, "severity": "critical", "message": f"Syntax error: {e.msg}", "suggestion": "Fix syntax error"})
        return issues
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append({"file": str(filepath), "line": node.lineno, "severity": "high", "message": "Bare except: catches all exceptions", "suggestion": "Use 'except Exception:' or specific exception"})
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "eval":
                issues.append({"file": str(filepath), "line": node.lineno, "severity": "critical", "message": "eval() usage - code injection risk", "suggestion": "Use ast.literal_eval() or avoid eval"})
            if isinstance(node.func, ast.Attribute) and node.func.attr == "execute":
                src = ast.get_source_segment(content, node) or ""
                if "sql" in src.lower():
                    issues.append({"file": str(filepath), "line": node.lineno, "severity": "high", "message": "Possible SQL injection via execute()", "suggestion": "Use parameterized queries"})
    
    for i, line in enumerate(lines, 1):
        if re.search(r"password\s*=\s*[\"'][^\"']+[\"']", line, re.IGNORECASE):
            issues.append({"file": str(filepath), "line": i, "severity": "high", "message": "Hardcoded password", "suggestion": "Use environment variables or keyring"})
        if re.search(r"api[_-]?key\s*=\s*[\"'][^\"']+[\"']", line, re.IGNORECASE):
            issues.append({"file": str(filepath), "line": i, "severity": "high", "message": "Hardcoded API key", "suggestion": "Use environment variables"})
        if "TODO" in line or "FIXME" in line:
            issues.append({"file": str(filepath), "line": i, "severity": "low", "message": f"Comment: {line.strip()}", "suggestion": "Address or create issue"})
    
    return issues


def review_js(filepath: Path, content: str, lines: List[str], focus: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(lines, 1):
        if "eval(" in line:
            issues.append({"file": str(filepath), "line": i, "severity": "critical", "message": "eval() usage", "suggestion": "Avoid eval, use JSON.parse or safe alternatives"})
        if "innerHTML" in line and ("user" in line.lower() or "input" in line.lower() or "data" in line.lower()):
            issues.append({"file": str(filepath), "line": i, "severity": "high", "message": "Potential XSS via innerHTML", "suggestion": "Use textContent or sanitize input"})
        if "console.log" in line and "debug" not in focus:
            issues.append({"file": str(filepath), "line": i, "severity": "low", "message": "console.log in production code", "suggestion": "Remove or use proper logging"})
        if re.search(r"['\"]?[a-z_]+['\"]?\s*:\s*['\"][^'\"]{20,}['\"]", line) and ("key" in line.lower() or "secret" in line.lower() or "token" in line.lower()):
            issues.append({"file": str(filepath), "line": i, "severity": "high", "message": "Possible hardcoded secret", "suggestion": "Use environment variables"})
    return issues


def review_general(filepath: Path, content: str, lines: List[str], focus: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(lines, 1):
        if len(line) > 120:
            issues.append({"file": str(filepath), "line": i, "severity": "low", "message": f"Line too long ({len(line)} chars)", "suggestion": "Break into multiple lines"})
        if re.search(r"(?i)(password|secret|token|api[_-]?key)\s*[:=]\s*[\"'][^\"']{8,}[\"']", line):
            issues.append({"file": str(filepath), "line": i, "severity": "critical", "message": "Hardcoded credential", "suggestion": "Move to environment variable or keyring"})
    return issues


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "review_code",
            "description": "Review code files or directories for issues",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File or directory path"},
                    "focus": {"type": "string", "enum": ["security", "performance", "style", "bugs", ""], "description": "Focus area", "default": ""}
                },
                "required": ["path"]
            }
        }
    }
]