import webbrowser
from pathlib import Path
from typing import Dict, Any
import uuid

BASE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/TextPlugin.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { min-height: 100vh; display: flex; flex-direction: column; background: #0d1117; color: #e6edf3; font-family: system-ui, sans-serif; overflow: hidden; }
        .canvas { flex: 1; display: flex; align-items: center; justify-content: center; position: relative; }
        .controls { padding: 1rem; display: flex; gap: 0.5rem; justify-content: center; background: #161b22; border-top: 1px solid #30363d; }
        button { padding: 0.5rem 1rem; background: #58a6ff; color: #0d1117; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; }
        button:hover { background: #79b8ff; }
        .title { position: absolute; top: 1rem; left: 50%; transform: translateX(-50%); font-size: 0.9rem; color: #8b949e; pointer-events: none; }
    </style>
</head>
<body>
    <div class="title">{{TITLE}}</div>
    <div class="canvas" id="canvas"></div>
    <div class="controls">
        <button id="restart">Restart</button>
        <button id="pause">Pause</button>
        <button id="record">Record Hint</button>
    </div>
    <script>
        {{ANIMATION_JS}}
        document.getElementById('restart').onclick = () => { if (window.anim) { window.anim.restart(); } };
        document.getElementById('pause').onclick = () => { if (window.anim) { window.anim.paused(!window.anim.paused()); } };
        document.getElementById('record').onclick = () => alert('Use OBS or browser DevTools "Capture screenshot" to record. Set canvas size as needed.');
    </script>
</body>
</html>"""

ANIMATION_PRESETS = {
    "logo_reveal": """
const canvas = document.getElementById('canvas');
const logo = document.createElement('div');
logo.textContent = 'ZYVO';
logo.style.cssText = 'font-size: 6rem; font-weight: 800; letter-spacing: -0.05em; background: linear-gradient(90deg, #58a6ff, #3fb950); -webkit-background-clip: text; -webkit-text-fill-color: transparent; opacity: 0;';
canvas.appendChild(logo);

const particles = [];
for (let i = 0; i < 50; i++) {
    const p = document.createElement('div');
    p.style.cssText = 'position: absolute; width: 6px; height: 6px; border-radius: 50%; background: #58a6ff; pointer-events: none;';
    canvas.appendChild(p);
    particles.push(p);
}

window.anim = gsap.timeline({ defaults: { ease: 'power3.out' } })
    .fromTo(logo, { scale: 0.5, opacity: 0 }, { scale: 1, opacity: 1, duration: 1 })
    .to(particles, {
        x: () => gsap.utils.random(-300, 300),
        y: () => gsap.utils.random(-200, 200),
        opacity: 0,
        scale: 0,
        duration: 1.5,
        stagger: 0.02,
        ease: 'power2.out'
    }, '-=0.5');
""",
    "text_scramble": """
const canvas = document.getElementById('canvas');
const text = document.createElement('div');
text.style.cssText = 'font-size: 3rem; font-weight: 600; text-align: center; max-width: 800px;';
canvas.appendChild(text);

const phrases = ['zyvo-clone', 'AI Agent', 'Desktop App', 'Python + GSAP', 'Build Fast'];
let i = 0;

window.anim = gsap.timeline({ repeat: -1, repeatDelay: 1 })
    .to(text, { duration: 0.5, opacity: 0, ease: 'power2.in' })
    .call(() => { text.textContent = phrases[i]; i = (i + 1) % phrases.length; })
    .to(text, { duration: 0.5, opacity: 1, ease: 'power2.out' });
""",
    "card_flip": """
const canvas = document.getElementById('canvas');
canvas.style.perspective = '1000px';

const cards = [];
const colors = ['#58a6ff', '#3fb950', '#f85149', '#d2a8ff', '#ffa657'];

for (let i = 0; i < 5; i++) {
    const card = document.createElement('div');
    card.style.cssText = 'width: 200px; height: 280px; position: absolute; transform-style: preserve-3d; cursor: pointer;';
    card.innerHTML = `
        <div class="face front" style="background: ${colors[i]}; display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: 700;">Card ${i+1}</div>
        <div class="face back" style="background: #161b22; color: #e6edf3; display: flex; align-items: center; justify-content: center; padding: 1rem; text-align: center; backface-visibility: hidden; transform: rotateY(180deg);">Back content ${i+1}</div>
    `;
    const faces = card.querySelectorAll('.face');
    faces.forEach(f => {
        f.style.cssText = 'position: absolute; width: 100%; height: 100%; border-radius: 12px; backface-visibility: hidden;';
    });
    canvas.appendChild(card);
    cards.push(card);
}

gsap.set(cards, { rotationY: -90, x: (i) => (i - 2) * 220 });

window.anim = gsap.timeline({ repeat: -1, yoyo: true, repeatDelay: 1 })
    .to(cards, { rotationY: 0, duration: 0.8, stagger: 0.1, ease: 'back.out(1.7)' })
    .to(cards, { rotationY: 90, duration: 0.8, stagger: 0.1, ease: 'back.in(1.7)' }, '+=1');
""",
    "particle_field": """
const canvas = document.getElementById('canvas');
canvas.style.position = 'relative';
canvas.style.width = '100%';
canvas.style.height = '100%';

const particles = [];
for (let i = 0; i < 100; i++) {
    const p = document.createElement('div');
    const size = Math.random() * 4 + 2;
    p.style.cssText = `position: absolute; width: ${size}px; height: ${size}px; border-radius: 50%; background: ${['#58a6ff','#3fb950','#f85149','#d2a8ff'][Math.floor(Math.random()*4)]}; opacity: ${Math.random()*0.5+0.3}; pointer-events: none;`;
    canvas.appendChild(p);
    particles.push({ el: p, x: Math.random() * window.innerWidth, y: Math.random() * window.innerHeight, vx: (Math.random()-0.5)*0.5, vy: (Math.random()-0.5)*0.5 });
}

function animate() {
    particles.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = window.innerWidth;
        if (p.x > window.innerWidth) p.x = 0;
        if (p.y < 0) p.y = window.innerHeight;
        if (p.y > window.innerHeight) p.y = 0;
        p.el.style.transform = `translate(${p.x}px, ${p.y}px)`;
    });
    requestAnimationFrame(animate);
}
animate();

window.anim = { paused: () => false, restart: () => {} };
""",
    "morphing_shapes": """
const canvas = document.getElementById('canvas');
const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
svg.setAttribute('viewBox', '0 0 400 400');
svg.style.width = '300px';
svg.style.height = '300px';
canvas.appendChild(svg);

const paths = [
    'M200,50 L350,200 L200,350 L50,200 Z',  // diamond
    'M50,200 Q200,50 350,200 Q200,350 50,200 Z',  // rounded
    'M200,50 L350,350 L50,350 Z',  // triangle
    'M50,50 L350,50 L350,350 L50,350 Z'  // square
];

const shape = document.createElementNS('http://www.w3.org/2000/svg', 'path');
shape.setAttribute('d', paths[0]);
shape.setAttribute('fill', 'url(#grad)');
svg.appendChild(shape);

const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
const grad = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
grad.setAttribute('id', 'grad');
grad.setAttribute('x1', '0%'); grad.setAttribute('y1', '0%');
grad.setAttribute('x2', '100%'); grad.setAttribute('y2', '100%');
grad.innerHTML = '<stop offset="0%" stop-color="#58a6ff"/><stop offset="100%" stop-color="#d2a8ff"/>';
defs.appendChild(grad);
svg.appendChild(defs);

let idx = 0;
window.anim = gsap.timeline({ repeat: -1 })
    .to(shape, { attr: { d: paths[1] }, duration: 1, ease: 'power2.inOut' })
    .to(shape, { attr: { d: paths[2] }, duration: 1, ease: 'power2.inOut' })
    .to(shape, { attr: { d: paths[3] }, duration: 1, ease: 'power2.inOut' })
    .to(shape, { attr: { d: paths[0] }, duration: 1, ease: 'power2.inOut' });
"""
}


def make_animation(brief: str) -> Dict[str, Any]:
    brief_lower = brief.lower()
    preset = "logo_reveal"
    for key in ANIMATION_PRESETS:
        if key.replace("_", " ") in brief_lower:
            preset = key
            break

    js = ANIMATION_PRESETS[preset]
    html = BASE_TEMPLATE.replace("{{TITLE}}", f"Animation: {brief}").replace("{{ANIMATION_JS}}", js)

    fname = f"animation_{uuid.uuid4().hex[:8]}.html"
    fpath = Path.cwd() / fname
    fpath.write_text(html, encoding="utf-8")

    webbrowser.open(fpath.as_uri())

    return {"success": True, "path": str(fpath), "html": html}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "make_animation",
            "description": "Generate an HTML+GSAP animation for recording",
            "parameters": {
                "type": "object",
                "properties": {
                    "brief": {"type": "string", "description": "Description of the animation (e.g., 'logo reveal', 'text scramble', 'card flip', 'particle field', 'morphing shapes')"}
                },
                "required": ["brief"]
            }
        }
    }
]