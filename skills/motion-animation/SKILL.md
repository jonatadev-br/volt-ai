# Skill: motion-animation

Generate ready-to-record HTML animations using GSAP (via CDN). Use the `make_animation` tool when user wants animations, transitions, or motion graphics.

## Tool: make_animation
Creates an HTML file with GSAP animation based on a brief description.

Arguments:
- brief (string): Description of the animation (e.g., "logo reveal with particles", "text scramble effect", "card flip carousel")

Returns: { success, path, html }

The output is a standalone HTML file that opens in browser for recording.