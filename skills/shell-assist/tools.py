from typing import Dict, Any, List

BLOCKLIST = [
    "rm -rf /", "rm -rf /*", "dd if=", "mkfs", "shutdown", "reboot",
    ":(){ :|:& };:", "fork", "> /dev/sda", "chmod 777 /", "chown -R"
]

def explain_command(cmd: str) -> Dict[str, Any]:
    parts = cmd.strip().split()
    if not parts:
        return {"explanation": "Empty command", "risk": "none", "blocked": False}
    
    base = parts[0]
    explanations = {
        "ls": "List directory contents",
        "cd": "Change directory",
        "mkdir": "Create directory",
        "rm": "Remove files/directories",
        "cp": "Copy files",
        "mv": "Move/rename files",
        "cat": "Display file content",
        "grep": "Search text patterns",
        "find": "Find files",
        "git": "Git version control",
        "npm": "Node package manager",
        "pip": "Python package installer",
        "python": "Run Python script",
        "docker": "Container management",
        "curl": "Transfer data from URL",
        "wget": "Download files",
        "ssh": "Secure shell connection",
        "scp": "Secure copy",
        "tar": "Archive files",
        "zip": "Compress files",
        "chmod": "Change permissions",
        "chown": "Change ownership",
        "sudo": "Run as superuser",
        "systemctl": "System service control",
        "apt": "Package manager (Debian/Ubuntu)",
        "brew": "Package manager (macOS)",
    }
    
    explanation = explanations.get(base, f"Execute: {base}")
    if len(parts) > 1:
        explanation += f" with args: {' '.join(parts[1:])}"
    
    risk = "low"
    blocked = False
    for blocked_cmd in BLOCKLIST:
        if blocked_cmd in cmd:
            risk = "critical"
            blocked = True
            explanation += f" ⚠️ BLOCKED: Contains '{blocked_cmd}'"
            break
    
    if base in ("rm", "dd", "mkfs", "shutdown", "reboot", "sudo", "chmod", "chown") and not blocked:
        risk = "high"
        explanation += " ⚠️ High risk: modifies system/files"
    
    return {"explanation": explanation, "risk": risk, "blocked": blocked}


def explain_and_confirm(cmd: str, cwd: str = ".") -> Dict[str, Any]:
    analysis = explain_command(cmd)
    if analysis["blocked"]:
        return {"error": f"Command blocked: {analysis['explanation']}", "needs_confirmation": False}
    
    return {
        "explanation": analysis["explanation"],
        "risk": analysis["risk"],
        "needs_confirmation": analysis["risk"] in ("high", "critical"),
        "command": cmd,
        "cwd": cwd
    }


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "explain_command",
            "description": "Explain what a shell command does and its risk level",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string", "description": "Command to explain"}
                },
                "required": ["cmd"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explain_and_confirm",
            "description": "Explain command and request confirmation before execution",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string", "description": "Command to explain and potentially run"},
                    "cwd": {"type": "string", "description": "Working directory", "default": "."}
                },
                "required": ["cmd"]
            }
        }
    }
]