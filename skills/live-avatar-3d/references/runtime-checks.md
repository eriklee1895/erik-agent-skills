# Generation and runtime checks

## Create the view sheet

The bundled helper uses one GPT Image 2.5 Sunburst edit request and saves a PNG
plus a JSON metadata file. Character notes should list only features observed in
the source image.

```bash
uv run --script "$SKILL_DIR/scripts/generate_turnaround.py" \
  --image "$REFERENCE_IMAGE" \
  --out "$OUTPUT_DIR/turnaround.png" \
  --prompt "mint body, amber leaf antennae, navy eyes, coral cheek spots, cream scarf, brown boots"
```

Run the same command with `--dry-run` first when checking paths and parameters.
The helper never retries a model call automatically. If it fails or produces an
unusable sheet, report that result and ask before making another paid request.

The helper reads `OPENAI_API_KEY` and optional `OPENAI_BASE_URL`, or the paired
`CUSTOM_OPENAI_API_KEY` and `CUSTOM_OPENAI_BASE_URL`, from the environment or the
working directory's `.env`. It does not print credential values. Set those
variables outside chat; do not paste keys into prompts.

The edit request sends the selected source image to the configured image API.
Only use the image the user selected for this avatar task. The generated HTML
does not need the source image or turnaround sheet to run.

## Three.js loading

The starter HTML uses an import map so `three` and `three/addons/` resolve from
the same pinned Three.js release. `OrbitControls` imports `three` by its bare
module name; importing the addon from a CDN without the matching import map can
leave the page with visible controls and a blank stage. Keep the core and addon
URLs on the same version. See the [Three.js OrbitControls documentation](https://threejs.org/docs/pages/OrbitControls.html).

The single HTML file loads Three.js from a CDN and therefore needs network
access. It has no build step or application backend. For offline delivery,
bundle the matching Three.js files locally and update the import map.

## Verify the rendered page

Serve the output over localhost and check the page in a real browser. A `200`
response does not prove that WebGL initialized. Confirm all of the following:

- one visible canvas exists and the avatar is visible in front, three-quarter,
  and profile views
- drag orbit, scroll or pinch zoom, front/profile toggle, and gesture buttons
  respond without console errors
- pause/resume works, buttons are keyboard reachable, and focus is visible
- at 375 px and desktop width there is no horizontal overflow or cropped face
- `prefers-reduced-motion` stops automatic movement while manual controls work
- the microphone starts only after a click, updates the mouth from the analyser,
  and stops cleanly when stopped, hidden, or unloaded

Do not grant microphone permission just to complete browser verification. If the
user has not authorized microphone access for this test, verify the off state
and inspect the local-only code path without accepting a permission prompt. The
page must not use `MediaRecorder`, upload audio, play captured audio, or connect
the microphone source to the audio destination.
