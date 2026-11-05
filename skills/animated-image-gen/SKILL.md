---
name: animated-image-gen
description: Use when creating animated WebP or GIF assets, including reaction stickers, character loops, photo reactions, product micro-motion, captioned comic scenes, fixed-layout process illustrations, or converting existing image frames and animations.
---

# Animated Image Gen

Create animated **WebP and GIF** with Seedream 5.0 Pro and the bundled Python CLI. WebP is the primary web delivery. Keep complete RGBA PNG frames as masters and inspect the actual animation before delivery.

## Resolve the brief

Infer purpose, subject, action, style and delivery from the request. Honor explicit dimensions, timing, text, format and file-size constraints. Choose reasonable visual details when the brief leaves room.

- Stickers default to **256×256**. Avatars and state assets may use 128 or 256 pixels. Photo scenes and technical diagrams follow their display context, with larger text and canvas where needed.
- Start with 6–9 source poses for a simple action and 12–16 for a short scene. Read [template selection](references/templates.md) for measured recipes and their conditions.
- Describe sequential acting beats, identity anchors, camera and subject scale. Plan captions separately when exact text matters.
- The image model is **`doubao-seedream-5-0-pro-260628`**. The API generates a PNG sheet or master pose. Frame counts, timing and delivery formats belong to this local workflow.

## Execute

Resolve `SKILL_DIR` to this installed folder. Run from the user's project so relative files and its `.env` resolve there. `uv` supplies the inline Python dependencies. Generation uses `ARK_API_KEY` from the environment or calling directory's `.env`. Local encoding and composition work without credentials.

```bash
uv run "$SKILL_DIR/scripts/animated_image_gen.py" generate \
  --prompt '一只橙红狐狸，深蓝围巾，扁平贴纸画风，原地眨眼一次再睁开。固定镜头、体型、位置和配饰，首尾自然衔接。' \
  --transparent --size 256x256 --duration 1.2 \
  --out-dir output/fox-blink --dry-run
```

Review the plan, then repeat without `--dry-run`. Ordinary tasks use one paid model operation. After inspecting a concrete fault, a second targeted operation may repair it. Count reference edits and native layer operations in the same budget. An explicit user batch or budget changes the allowance.

| Need | Entry point |
| --- | --- |
| New generated animation or a reference-conditioned sheet | `generate` |
| PNG frames, an existing sheet, GIF or WebP | `encode` |
| Actual dimensions, delays, plays, unique frames and alpha | `inspect` |
| Recipe names and parameterized briefs | `templates` |
| Bounded breathing from a still pose | `breathe` |
| Measured fixed four-node tool-call diagram | `flow` |

Use `--reference` for identity inputs. An alpha-bearing reference with `--transparent` is tiled into an editing sheet. Other transparent requests use a separated key background, followed by local cleanup. Choose a key color outside the subject palette and inspect the edges.

For a breathing recipe, `generate --template sleepy-idle` produces a master pose. Inspect it, select the chest outline, then run `breathe`. A `master_ready` result is an intermediate step. For precise diagrams, keep labels and geometry fixed and animate the data path locally. Actual software demonstrations use supplied screenshots or frames.

Detailed switches, local regions, caption schema and repair steps are in [the CLI guide](references/cli.md). `--help` lists commands. [Format and destination guidance](references/formats-and-platforms.md) covers lossy/lossless choice and platform verification.

## Inspect and deliver

Read `job.json`, the RGBA frames and contact sheet. Check the entire acting sequence, identity, moving limb, object contact, crop, caption legibility, static regions and final-to-first transition. Play several cycles at the intended display size. Technical file checks and visual acceptance are separate.

`encode` preserves existing animation timing and total plays unless explicitly overridden. Repeated frames may merge while retaining their duration. `--plays 0` selects infinite playback. A byte limit is checked before publishing the encoded file, with dimensions preserved.

Generation jobs use fresh directories, preserving source and unknown outcomes. Transport failures stop with `OutcomeUnknown`. Download retries reuse the returned asset. Existing outputs are protected, and local re-encoding can continue from saved frames.

Deliver the actual WebP/GIF and its metadata path, actual dimensions and cycle duration, source versus decoded frame counts, repeat behavior, and any unmet visual or destination requirement. Notion's file-type support and preservation of animation in a target page are checked separately.

[Release validation](evals/release-validation.json) records the tested installation, real model calls and local regression coverage.
