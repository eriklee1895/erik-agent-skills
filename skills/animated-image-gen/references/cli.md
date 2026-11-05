# CLI operations

Run with `uv run scripts/animated_image_gen.py` from this folder, or use its absolute path from the user's project. All package resources resolve relative to the installed script.

## Generation

`generate` accepts a prompt, prompt file, or a creative template with `--set name=value` slots. The agent selects the action and adapts a template when user constraints change its structure.

- `--poses` selects 2–24 source poses for animation. `--master-only` produces a single intermediate PNG for local animation.
- `--size WIDTHxHEIGHT` selects finished-frame dimensions. `--grid COLUMNSxROWS` can select layout. The planner sizes the PNG sheet within 921600–4624220 pixels and records any planned source upscaling.
- `--reference` is repeatable, with at most 10 static image references. Local files stay within 30 MB. Existing animations can be decoded with `encode`, or a still reference frame can be selected explicitly.
- `--transparent` uses an existing alpha-bearing reference when available, or a solid key background. `--key-color green|magenta|cyan` selects that background for generation and cleanup.
- `--cell-inset` can trim a measured cell-edge artifact. Check subject margins before using it.
- `--out-dir` is a fresh job directory. It contains `source.png`, complete RGBA `frames/` with their contact sheet and timeline, the animation and `job.json`.
- `--dry-run` reports a credential-free plan. The actual API request uses Pro, PNG, a prompt, size and optional references.

Inspect `source.png` and the contact sheet even when encoding succeeds. A grid can contain a wrong limb, unintended text or an inconsistent pose. For a targeted second call, use the source sheet as a reference and state the exact cell and change. Preserve approved frames in a separate working directory and replace only the corrected cell when appropriate, then `encode` that directory.

`--force` concerns replacement of an encoded local file. Generation always uses a fresh job directory, which preserves both completed and interrupted requests.

## Encode and inspect

```bash
uv run "$SKILL_DIR/scripts/animated_image_gen.py" encode \
  --input output/fox-blink/frames --out output/fox-blink/compatibility.gif \
  --duration 1.2

uv run "$SKILL_DIR/scripts/animated_image_gen.py" inspect \
  output/fox-blink/animation.webp
```

A directory input reads numerically ordered PNG filenames. Skill-generated master directories also contain `timeline.json`, preserving per-pose delays and total plays for local re-encoding. A sheet input also supplies `--grid` and `--poses`. An existing animated GIF or WebP retains its per-frame durations and total-play setting.

Timing overrides choose one of `--duration` in seconds, `--fps`, or `--delays` pointing to a JSON list of milliseconds. Source poses and playback timing are separate values. GIF timing is distributed in 10 ms units with cumulative rounding. WebP uses millisecond units. The inspector reports the actual decoded result, including merged duplicate frames.

`--plays 0` means infinite playback. A positive value is the total number of plays, with format-specific repeat fields handled by the encoder.

Delivery options are `--format auto|webp|gif`. Auto follows an explicit output extension, otherwise web selects WebP and chat/Notion select GIF as the initial compatibility policy. An explicit format wins. `--webp-mode auto|lossy|lossless`, `--quality 0..100`, and GIF `--colors 2..256` control encoding. `--resample nearest|lanczos|auto` selects resizing, with the pixel-flame template choosing nearest and a 64-color GIF palette. With `--max-bytes`, lossy WebP searches lower quality and GIF searches fewer palette colors. A failed size constraint leaves the source frames available for a local revision.

## Local regions and text

`--motion-region x,y,width,height` is normalized to 0–1 on the finished canvas. Its interior changes while a supplied `--static-image`, or the first frame, supplies the rest. Crop or pad a static image to the intended aspect before use. Choose the region after inspecting the full sequence, including the widest motion.

For an isolated character or effect with unwanted position drift, `--align base` registers the lower foreground band to its first-frame anchor. Use it when the base should stay fixed. Intended jumps and translations retain their original movement by leaving alignment at `none`. The helper requires transparency and checks for cropping. Local transformations preserve their finished RGBA frames and timeline for another export.

`--overlays captions.json` reads a list. Frame indices start at 0 and `end` is exclusive. Box coordinates use normalized x,y,width,height. `font_size` is in finished-canvas pixels.

```json
[
  {"text": "", "box": [0, 0, 1, 0.25], "fill": "#fff5df"},
  {"text": "先听我说", "start": 0, "end": 4,
   "box": [0.02, 0.03, 0.45, 0.16], "font_size": 16,
   "fill": "white", "border": "#93552f", "color": "#93552f"}
]
```

Text fit, font availability and required glyph coverage are validated. Set `--font` or `ANIMATED_IMAGE_FONT` for a specific font. The helper searches installed fonts on macOS, Linux and Windows. CJK text requires a readable CJK font. Generated images and master frames stay intact when local overlays are applied.

## Breathing and flow

`breathe --input master.png --region 0.3,0.4,0.4,0.3 --size 256x256 --out idle.webp` creates a small local deformation. The region should contain the chest outline while keeping the head and supporting objects stable. The helper retains input dimensions unless `--size` is supplied. `--frames` defaults to 12 and `--amplitude` to 1 percent of canvas height.

`flow --out process.webp --size 1280x720` renders the measured User→Agent→Tool→Agent→Result example. `--language zh` selects Chinese labels. An optional `--mascot` adds an alpha-bearing image. The diagram has fixed topology. For a different process, the agent can create accurate frames with the available drawing tools, then use `encode` for the common delivery checks.
