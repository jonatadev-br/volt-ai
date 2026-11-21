import os
import webbrowser
from pathlib import Path
from typing import Dict, Any

TEMPLATES = {
    "landing": {
        "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{PROJECT_NAME}}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header class="hero">
        <nav class="nav">
            <div class="logo">{{PROJECT_NAME}}</div>
            <ul class="nav-links">
                <li><a href="#features">Features</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </nav>
        <div class="hero-content">
            <h1>Welcome to {{PROJECT_NAME}}</h1>
            <p class="tagline">A modern landing page built with zyvo-clone</p>
            <a href="#contact" class="btn-primary">Get Started</a>
        </div>
    </header>
    <section id="features" class="features">
        <h2>Features</h2>
        <div class="feature-grid">
            <div class="feature-card">
                <h3>Fast</h3>
                <p>Optimized for performance</p>
            </div>
            <div class="feature-card">
                <h3>Responsive</h3>
                <p>Works on all devices</p>
            </div>
            <div class="feature-card">
                <h3>Clean Code</h3>
                <p>Vanilla HTML/CSS/JS</p>
            </div>
        </div>
    </section>
    <section id="about" class="about">
        <h2>About</h2>
        <p>This project was scaffolded by zyvo-clone's webdev skill.</p>
    </section>
    <section id="contact" class="contact">
        <h2>Contact</h2>
        <form id="contact-form">
            <input type="email" placeholder="Email" required>
            <textarea placeholder="Message" required></textarea>
            <button type="submit" class="btn-primary">Send</button>
        </form>
    </section>
    <footer class="footer">
        <p>&copy; 2024 {{PROJECT_NAME}}. Built with zyvo-clone.</p>
    </footer>
    <script src="app.js"></script>
</body>
</html>""",
        "style.css": """* { box-sizing: border-box; margin: 0; padding: 0; }
:root { --bg: #0d1117; --fg: #e6edf3; --muted: #8b949e; --accent: #58a6ff; --card: #161b22; --border: #30363d; }
body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--fg); line-height: 1.6; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.nav { display: flex; justify-content: space-between; align-items: center; padding: 1rem 2rem; background: rgba(13,17,23,0.9); backdrop-filter: blur(10px); position: sticky; top: 0; z-index: 100; border-bottom: 1px solid var(--border); }
.logo { font-weight: 700; font-size: 1.25rem; color: var(--accent); }
.nav-links { display: flex; gap: 1.5rem; list-style: none; }
.hero { min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 4rem 2rem; background: linear-gradient(180deg, var(--bg) 0%, #161b22 100%); }
.hero-content h1 { font-size: clamp(2.5rem, 5vw, 4rem); margin-bottom: 1rem; background: linear-gradient(90deg, var(--fg), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.tagline { font-size: 1.25rem; color: var(--muted); margin-bottom: 2rem; max-width: 600px; }
.btn-primary { display: inline-block; padding: 0.875rem 2rem; background: var(--accent); color: var(--bg); border: none; border-radius: 6px; font-weight: 600; cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(88,166,255,0.3); }
section { padding: 4rem 2rem; max-width: 1000px; margin: 0 auto; }
h2 { font-size: 2rem; margin-bottom: 2rem; text-align: center; }
.feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; }
.feature-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 2rem; transition: transform 0.2s, border-color 0.2s; }
.feature-card:hover { transform: translateY(-4px); border-color: var(--accent); }
.feature-card h3 { margin-bottom: 0.5rem; }
.feature-card p { color: var(--muted); }
.about p { text-align: center; color: var(--muted); max-width: 600px; margin: 0 auto; }
.contact form { display: flex; flex-direction: column; gap: 1rem; max-width: 500px; margin: 0 auto; }
.contact input, .contact textarea { padding: 1rem; background: var(--card); border: 1px solid var(--border); border-radius: 6px; color: var(--fg); font-family: inherit; }
.contact input:focus, .contact textarea:focus { outline: none; border-color: var(--accent); }
.footer { text-align: center; padding: 2rem; color: var(--muted); border-top: 1px solid var(--border); }
@media (max-width: 600px) { .nav-links { display: none; } }""",
        "app.js": """document.getElementById('contact-form').addEventListener('submit', e => {
    e.preventDefault();
    alert('Form submitted! (Demo only)');
    e.target.reset();
});

document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
        e.preventDefault();
        document.querySelector(a.getAttribute('href')).scrollIntoView({ behavior: 'smooth' });
    });
});"""
    },
    "portfolio": {
        "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{PROJECT_NAME}} - Portfolio</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header class="header">
        <div class="container">
            <h1>{{PROJECT_NAME}}</h1>
            <p class="subtitle">Developer · Designer · Creator</p>
        </div>
    </header>
    <nav class="nav">
        <div class="container">
            <a href="#projects">Projects</a>
            <a href="#skills">Skills</a>
            <a href="#contact">Contact</a>
        </div>
    </nav>
    <main>
        <section id="projects" class="section">
            <div class="container">
                <h2>Projects</h2>
                <div class="project-grid" id="projects-grid"></div>
            </div>
        </section>
        <section id="skills" class="section">
            <div class="container">
                <h2>Skills</h2>
                <div class="skills-cloud" id="skills-cloud"></div>
            </div>
        </section>
        <section id="contact" class="section">
            <div class="container">
                <h2>Contact</h2>
                <p>Get in touch: <a href="mailto:hello@example.com">hello@example.com</a></p>
            </div>
        </section>
    </main>
    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 {{PROJECT_NAME}}</p>
        </div>
    </footer>
    <script src="app.js"></script>
</body>
</html>""",
        "style.css": """* { box-sizing: border-box; margin: 0; padding: 0; }
:root { --bg: #ffffff; --fg: #1a1a2e; --muted: #64748b; --accent: #3b82f6; --card: #f8fafc; --border: #e2e8f0; }
@media (prefers-color-scheme: dark) { :root { --bg: #0f172a; --fg: #f1f5f9; --muted: #94a3b8; --accent: #60a5fa; --card: #1e293b; --border: #334155; } }
body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--fg); line-height: 1.6; }
.container { max-width: 1000px; margin: 0 auto; padding: 0 1.5rem; }
.header { padding: 4rem 0; text-align: center; background: linear-gradient(180deg, var(--bg) 0%, var(--card) 100%); border-bottom: 1px solid var(--border); }
.header h1 { font-size: clamp(2.5rem, 5vw, 4rem); margin-bottom: 0.5rem; }
.subtitle { font-size: 1.25rem; color: var(--muted); }
.nav { padding: 1rem 0; border-bottom: 1px solid var(--border); position: sticky; top: 0; background: var(--bg); z-index: 100; }
.nav .container { display: flex; justify-content: center; gap: 2rem; }
.nav a { color: var(--muted); font-weight: 500; transition: color 0.15s; }
.nav a:hover { color: var(--accent); }
.section { padding: 3rem 0; }
h2 { font-size: 1.75rem; margin-bottom: 2rem; }
.project-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
.project-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; transition: transform 0.2s, box-shadow 0.2s; }
.project-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.1); }
.project-card img { width: 100%; height: 180px; object-fit: cover; background: var(--border); }
.project-card .content { padding: 1.5rem; }
.project-card h3 { margin-bottom: 0.5rem; }
.project-card p { color: var(--muted); font-size: 0.9rem; margin-bottom: 1rem; }
.project-card .tags { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.project-card .tag { background: var(--accent); color: white; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75rem; }
.skills-cloud { display: flex; flex-wrap: wrap; gap: 0.75rem; }
.skill-badge { background: var(--card); border: 1px solid var(--border); padding: 0.5rem 1rem; border-radius: 999px; font-size: 0.9rem; }
.footer { padding: 2rem 0; text-align: center; color: var(--muted); border-top: 1px solid var(--border); }""",
        "app.js": """const projects = [
    { title: "Project One", desc: "A cool web application", tags: ["React", "Node.js"], image: "" },
    { title: "Project Two", desc: "Mobile app with Flutter", tags: ["Flutter", "Dart"], image: "" },
    { title: "Project Three", desc: "Data visualization dashboard", tags: ["Python", "D3.js"], image: "" }
];
const skills = ["JavaScript", "TypeScript", "React", "Node.js", "Python", "Docker", "AWS", "PostgreSQL", "Git", "CI/CD"];

const grid = document.getElementById('projects-grid');
projects.forEach(p => {
    const card = document.createElement('article');
    card.className = 'project-card';
    card.innerHTML = `<div class="content"><h3>${p.title}</h3><p>${p.desc}</p><div class="tags">${p.tags.map(t => `<span class="tag">${t}</span>`).join('')}</div></div>`;
    grid.appendChild(card);
});

const cloud = document.getElementById('skills-cloud');
skills.forEach(s => {
    const badge = document.createElement('span');
    badge.className = 'skill-badge';
    badge.textContent = s;
    cloud.appendChild(badge);
});"""
    },
    "blog": {
        "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{PROJECT_NAME}} - Blog</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header class="header">
        <div class="container">
            <h1>{{PROJECT_NAME}}</h1>
            <p class="tagline">Thoughts, tutorials, and experiments</p>
        </div>
    </header>
    <main class="container">
        <section class="posts" id="posts"></section>
        <nav class="pagination" id="pagination"></nav>
    </main>
    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 {{PROJECT_NAME}}. Powered by zyvo-clone.</p>
        </div>
    </footer>
    <script src="app.js"></script>
</body>
</html>""",
        "style.css": """* { box-sizing: border-box; margin: 0; padding: 0; }
:root { --bg: #fafafa; --fg: #1a1a2e; --muted: #64748b; --accent: #3b82f6; --card: #ffffff; --border: #e2e8f0; }
@media (prefers-color-scheme: dark) { :root { --bg: #0f172a; --fg: #f1f5f9; --muted: #94a3b8; --accent: #60a5fa; --card: #1e293b; --border: #334155; } }
body { font-family: Georgia, serif; background: var(--bg); color: var(--fg); line-height: 1.7; }
.container { max-width: 800px; margin: 0 auto; padding: 0 1.5rem; }
.header { padding: 3rem 0; text-align: center; border-bottom: 1px solid var(--border); }
.header h1 { font-size: clamp(2rem, 4vw, 3rem); margin-bottom: 0.5rem; }
.tagline { color: var(--muted); }
.posts { padding: 2rem 0; }
.post { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 2rem; margin-bottom: 1.5rem; transition: box-shadow 0.2s; }
.post:hover { box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
.post h2 { font-size: 1.5rem; margin-bottom: 0.75rem; }
.post h2 a { color: inherit; }
.post h2 a:hover { color: var(--accent); }
.post-meta { color: var(--muted); font-size: 0.9rem; margin-bottom: 1rem; }
.post-excerpt { color: var(--fg); }
.read-more { display: inline-block; margin-top: 1rem; color: var(--accent); font-weight: 500; }
.pagination { display: flex; justify-content: center; gap: 0.5rem; padding: 2rem 0; }
.pagination a, .pagination span { padding: 0.5rem 1rem; border: 1px solid var(--border); border-radius: 6px; color: var(--fg); }
.pagination .current { background: var(--accent); border-color: var(--accent); color: white; }
.footer { padding: 2rem 0; text-align: center; color: var(--muted); border-top: 1px solid var(--border); }""",
        "app.js": """const posts = [
    { title: "Getting Started with zyvo-clone", date: "2024-01-15", excerpt: "Learn how to build desktop AI agents with Python..." },
    { title: "Building Skills for zyvo-clone", date: "2024-01-20", excerpt: "Extend your agent with custom skills and tools..." },
    { title: "Deploying Your First Project", date: "2024-01-25", excerpt: "From localhost to production with PyInstaller..." }
];

const container = document.getElementById('posts');
posts.forEach(p => {
    const article = document.createElement('article');
    article.className = 'post';
    article.innerHTML = `<h2><a href="#">${p.title}</a></h2><div class="post-meta">${p.date}</div><p class="post-excerpt">${p.excerpt}</p><a href="#" class="read-more">Read more →</a>`;
    container.appendChild(article);
});"""
    }
}


def scaffold_web(project_name: str, kind: str) -> Dict[str, Any]:
    if kind not in TEMPLATES:
        return {"error": f"Unknown kind: {kind}. Choose: {list(TEMPLATES.keys())}"}

    base = Path.cwd() / project_name
    if base.exists():
        return {"error": f"Directory {project_name} already exists"}

    base.mkdir(parents=True)
    files = []
    for fname, content in TEMPLATES[kind].items():
        fpath = base / fname
        fpath.write_text(content.replace("{{PROJECT_NAME}}", project_name), encoding="utf-8")
        files.append(str(fpath))

    index = base / "index.html"
    if index.exists():
        webbrowser.open(index.as_uri())

    return {"success": True, "path": str(base), "files": files}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "scaffold_web",
            "description": "Scaffold a web project (landing page, portfolio, blog)",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Folder name for the project"},
                    "kind": {"type": "string", "enum": ["landing", "portfolio", "blog"], "description": "Project type"}
                },
                "required": ["project_name", "kind"]
            }
        }
    }
]