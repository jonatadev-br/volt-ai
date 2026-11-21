# Skill: shell-assist

Explain shell commands before running them. Never execute destructive commands without double confirmation.

When user asks to run a command:
1. Explain what the command does in plain language
2. Identify risks (file deletion, system modification, network access)
3. Ask for confirmation
4. Use `run_shell_confirmed` tool only after explicit user approval

Destructive commands (blocked by default): rm -rf /, dd, mkfs, shutdown, reboot, fork bombs.