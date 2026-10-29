---
name: seedream-image-gen
description: >
  Generate and edit images with ByteDance Seedream 5.0 Pro and Flash through
  Volcengine Ark: text-to-image, Chinese/English typography, single/multi-reference
  generation, coordinate or marker edits, outpainting, transparent-layer editing,
  and native image decomposition into a base plus transparent PNG layers.
  Use for posters, covers, product imagery, illustrations, character references,
  exact-size image assets, local edits, and editable layer extraction.
---

# Seedream 5.0 Pro / Flash

One Python CLI and one Ark Images API for both models. **Always use Pro when the user has not specified a model.** Switch to Flash only when the user explicitly chooses it or authorizes replacing Pro with a faster/lower-cost model. A draft, UGC, batch or style request by itself does not change this default.

## Choose a model and operation

| Model | ID / alias | Routing |
|---|---|---|
| Pro | `doubao-seedream-5-0-pro-260628` / `pro` | Default for demanding final artwork and the established Pro recipes. `standard` or `fast` prompt optimization. |
| Flash | `doubao-seedream-5-0-flash-260915` / `flash` | Explicit opt-in for lower-cost/latency-sensitive work. `standard` optimization only. See [Flash guidance](references/flash-quickref.md). |

Both support text, one reference or up to ten references, coordinate/marker interaction, alpha-image editing and native layer decomposition. Ordinary requests return one image. Neither model supports sequential/storyboard generation, web search or streaming.

Only Pro and Flash are supported. Retired Lite aliases and IDs fail before an API call rather than selecting a paid replacement.

## Quick workflow

Run commands from this skill folder, or use absolute script paths. Authentication is `ARK_API_KEY` from the environment or the calling directory's `.env`; credentials stay outside the skill.

```bash
# Default Pro, 2K, PNG, no watermark
uv run scripts/seedream_image_gen.py generate \
  --prompt '横版科技海报，标题准确写“新绿计划”，奶油白背景、青绿色几何图形、黑色无衬线大字，布局疏朗。'

# Flash, exact small destination size: generate at a valid size, then downscale
uv run scripts/seedream_image_gen.py generate --model flash --size 1500x600 \
  --prompt '青绿色陶瓷咖啡壶位于画面右侧，暖米色桌面，柔和窗光，左侧大面积干净留白，不要文字、品牌或人物。'
```

`--dry-run` previews requests without credentials or API calls. It may save marker previews and new `dry_run: true` metadata; existing metadata is preserved even with `--force`. Batch previews do not save result metadata.

## Size and format

Both models accept `1K`, `1.5K`, `2K`, or explicit `WIDTHxHEIGHT`. Their native explicit-size range is **921,600–4,624,220 total pixels**, aspect ratio **1:16–16:1**. Presets use the prompt's aspect description; use explicit pixels for exact platform requirements.

| Shortcut | Both models' target |
|---|---|
| `--square` | 1024×1024 |
| `--wide` / `--wechat-header` | 1792×1024 |
| `--portrait` | 1536×2048 |
| `--landscape` | 2048×1152 |
| `--phone` / `--stories` / `--wechat` | 1152×2048 |

Below-floor explicit targets are generated larger, with an approximately matching aspect ratio, then LANCZOS-downscaled locally. For example, `1500x600` → API `1520x608` → final `1500x600`; metadata records the requested target. `--no-auto-upscale` restores rejection. Above-cap or invalid-aspect requests are rejected. There is no 3K/4K preset on either supported model.

Use **2K for demanding typography** and inspect the actual text. **1.5K** shares the 1K pricing tier. Presets do not promise exact pixels for an arbitrary prompt. Output is PNG by default, or JPEG with `--output-format jpeg` (`jpg` is an alias).

## Write the prompt

Start with **subject/action/environment**, then the purpose, composition, lighting and style. Quote exact text, specify its hierarchy and location, and keep descriptions concise (official recommendation: roughly ≤300 Chinese characters or ≤600 English words). Enumerate details only when they matter; repeated style adjectives do not add control.

For edits, identify the target, state the change, and name what must remain. For multiple references, assign each role explicitly: shape from image 1, palette from image 2, layout from image 3. The supplied reference order defines 图1/图2/图3.

Write content constraints directly in the prompt, such as “blank unprinted pages” or “keep the title; remove the label on the cup.” Inspect the result for unwanted text or objects.

Start with [measured prompt recipes](references/benchmark-prompt-recipes.md) for edits, typography, cover layouts and infographics. See [prompt engineering](references/prompt-engineering.md) for more examples; historical Pro ratings do not establish Flash quality.

## Local editing: coordinates or visible markers

The official coordinate protocol writes spatial intent **inside the prompt**, not in a separate JSON `bbox` or `mask` field:

- `<point>x y</point>` selects a point.
- `<bbox>left top right bottom</bbox>` selects a box.
- Coordinates are normalized to **0–999**, relative to each referenced image. Convert image-relative pixels with `round(value / extent * 1000)` and clamp to 0–999. A displayed canvas may need its pan/zoom removed first.

```bash
uv run scripts/seedream_image_gen.py edit --model flash \
  --reference-image objects.png \
  --prompt '把图1 <bbox>100 350 550 780</bbox> 中左侧红色杯子改为深蓝色，杯子形状、右侧花瓶和背景保持不变。'
```

When several subjects share the box, also name the intended subject. You may give a second box for an object that must remain unchanged. Spatial instructions guide the model; they do not provide a hard pixel mask.

The existing visible-marker workflow is still available:

```bash
uv run scripts/seedream_image_gen.py edit --reference-image poster.png \
  --marker-rect '5%,6%,90%,25%' \
  --prompt '把红框内标题改成“新绿计划”，保持字体、对齐和其他内容，移除彩色标记。'
```

`--marker-rect` uses **x,y,width,height**, in pixels or percentages, and draws a temporary annotated copy. Repeat rectangles/colors for multiple targets. See [marker edits](references/marker-editing.md) and the [visual protocol guide](references/marker-edit-protocol.md).

## Transparent images

`background=transparent` **edits one existing alpha-bearing image**. It requires exactly one reference and PNG output. It is not a text-only transparent-background switch, and ordinary JPEG input cannot preserve alpha.

```bash
uv run scripts/seedream_image_gen.py edit --model flash \
  --reference-image layer-001.png --background transparent --output-format png \
  --prompt '把杯子改成橙黄色，保持轮廓、把手和透明背景，不增加文字。'
```

To isolate an object from an opaque picture, use decomposition first, then edit its returned PNG layer. Local inputs are validated before calling the API; URL inputs remain subject to server validation. See [transparency and layers](references/transparent-layers.md).

## Native layer decomposition

```bash
uv run scripts/seedream_image_gen.py decompose --model flash \
  --reference-image poster.png --size auto --out-dir output/layers
```

Input must be one PNG/JPEG, 262,144–36,000,000 pixels and ≤30MB. An optional `--prompt` selects elements without guaranteeing a layer count. Layer size accepts only `auto`, `1K`, `1.5K`, `2K`, not explicit pixels.

Results contain **one base plus up to sixteen foreground layers**. `--output-format` controls the base; foreground layers are always PNG. The CLI downloads all assets immediately and saves `base.png`/`base.jpg`, `layer-001.png` … and `layers.json`. It preserves each cropped image's native dimensions, `z_index`, `bounding_box`, name and description. It does not resize every crop to the canvas size or store expiring signed URLs.

Recompose using the returned base's coordinate system and each layer's bounding box. See [the layer manifest and reconstruction recipe](references/transparent-layers.md) for placement and coordinate conventions.

## Batch and common options

```bash
uv run scripts/seedream_image_gen.py generate-batch --input jobs.jsonl --concurrency 3
```

Each JSONL line is a prompt string or an object. Per-job fields include `prompt`, `model`, `size`, `output_format`, `background`, size shortcuts, `watermark`, `optimize_prompt`, `no_auto_upscale`, `reference_image` (list), marker options, outpaint options and `timeout`. Batch jobs generate one image each; decomposition is its own command.

`--concurrency` sets parallel batch requests. `--n 1..4` creates independent variants in `generate`.

`--seed N` (`-1`..`2147483647`) is near-reproducible only with prompt optimization mode `standard`; `fast` mode is not reproducible. With `--n`, each take uses `seed+i`.

Other common options: `--reference-image` (repeatable), `--out`, `--out-dir`, `--watermark`, `--timeout`, `--force`, `--prompt-file`. Outpainting remains available through `edit --outpaint left:400` and the [existing protocol](references/api-reference.md#outpainting).

## Errors, retries and output

Explicit 429/5xx responses use the existing bounded backoff and numeric `retry-after` handling. 400/401/403 are not retried. A transport failure after submission reports **OutcomeUnknown** and stops: do not automatically resubmit a possibly paid request. Image-download failures retry the download; exhausted downloads never regenerate the image.

Normal outputs have a sibling JSON metadata file with model, prompt, target/API sizes, elapsed time and usage. Layer output has its own manifest. URL results expire after 24 hours, so the CLI downloads immediately. Generation defaults to no watermark even though the API's default is true.

## Further guidance

- [API contract, current sources and pricing](references/api-reference.md)
- [Flash selection and migration](references/flash-quickref.md)
- [Transparency, layer manifest and reconstruction](references/transparent-layers.md)
- [Measured Pro/Flash benchmark](evals/flash-benchmark.md)
- [Comprehensive benchmark and controlled prompt comparisons](evals/comprehensive-benchmark.md)
- [Historical Pro observations](references/pro-observations.md)
- [Style presets](references/styles/): text posters/effects, Chinese aesthetics, photography, editorial infographics, character IP, hand-drawn editorials and visual narratives. Presets with only Pro evidence say so; do not automatically transfer their scores to Flash.
