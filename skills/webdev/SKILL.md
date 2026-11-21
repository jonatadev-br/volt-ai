# Skill: webdev

You can scaffold complete HTML/CSS/JS projects. When user asks for a landing page, portfolio, blog, or website, use the `scaffold_web` tool.

## Tool: scaffold_web
Creates a project folder with index.html, style.css, app.js based on the kind.

Arguments:
- project_name (string): folder name to create
- kind (string): "landing" | "portfolio" | "blog"

Returns: { success, path, files[] }

After scaffolding, the tool opens the page in the default browser.