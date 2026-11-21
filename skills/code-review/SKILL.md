# Skill: code-review

Review code files or directories for bugs, security issues, style, and improvements. Use the `review_code` tool.

## Tool: review_code
Analyzes a file or directory and returns structured review with severity levels.

Arguments:
- path (string): File or directory path to review
- focus (string): Optional focus area (security, performance, style, bugs)

Returns: { issues: [{file, line, severity, message, suggestion}], summary }