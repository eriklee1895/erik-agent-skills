---
name: live-avatar-3d
description: Use when turning a character image into an interactive 3D browser avatar with orbit, gestures, or optional microphone-driven mouth movement; not for static art or video.
---

# Live Avatar 3D

Produce a no-build HTML page with volumetric Three.js geometry; never use a flat image plane as the model.

## Workflow

1. Ask for an image if absent. Choose a non-overwriting output path.
2. For single-view input, create one GPT Image 2.5 Sunburst turnaround with the bundled helper. Skip if enough angles exist. Treat hidden details as inference; never auto-retry.
3. Copy `assets/avatar-template.html`; replace its sample name and `buildCharacter()` with geometry grounded in the original. Read [modeling-guide.md](references/modeling-guide.md).
4. Keep orbit/zoom, front/profile view, gestures, pause, and optional microphone mouth motion. Mic starts only on click; never record, upload, or play audio.
5. Serve over localhost. Verify canvas, views, controls, responsive layout, reduced motion, and browser errors with [runtime-checks.md](references/runtime-checks.md). State when browser verification is unavailable.

The helper sends the selected image to the configured GPT Image API. If credentials are missing, stop; do not switch providers. Deliver the HTML path and any retained turnaround path.
