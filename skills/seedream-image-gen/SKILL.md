---
name: seedream-image-gen
description: >
  Use when creating or editing images with Volcengine Ark Seedream 5.5:
  posters, product photos, multilingual typography, reference fusion, precise
  local edits, transparent PNG assets, or native layers with rich-text OCR.
---

# Seedream 5.5

Use **`doubao-seedream-5-5-261028`** (`--model 5.5`). This is the only supported model. Use the bundled CLI with `uv run`; authentication is `ARK_API_KEY` from the environment or the calling directory's `.env`. Keep credentials outside the skill.

## Choose the operation

| User outcome | Operation |
|---|---|
| New artwork / poster / photograph | `generate --prompt …` |
| Change an existing picture | `edit --reference-image … --prompt …` |
| Isolated logo, product or sticker from text or ordinary RGB pictures | `generate` / `edit` with `--background transparent` |
| Move/reuse individual elements or recover text content and styles | `decompose --text-recognition --max-images …` |
| Independent variants / many jobs | `generate --n 1..4` / `generate-batch --input jobs.jsonl` |

One ordinary API request produces **one image**, even with several references. A sprite sheet is one image needing local slicing; it is not native multi-frame generation. 5.5 supports neither streaming, web search nor sequential/storyboard generation. The generic streaming documentation describes other models.

```bash
# Run from the skill directory, or use an absolute script path.
uv run scripts/seedream_image_gen.py generate --size 2K \
  --prompt '横版茶叶海报，大标题准确写“桂馥茶集”，小字“净含量：250克”。奶油白背景、深绿无衬线字体，右侧一杯热茶，布局疏朗。'

# Native text-to-RGBA: no input alpha image or decomposition needed.
uv run scripts/seedream_image_gen.py generate --background transparent --size 1.5K \
  --prompt '独立的青绿色陶瓷茶壶，完整壶嘴与把手，柔和半透明接触投影，主体之外完全透明，不要场景或文字。'

# Direct cutout from an ordinary RGB reference.
uv run scripts/seedream_image_gen.py edit --reference-image product.jpg \
  --background transparent --prompt '只提取红色马克杯，完整保留把手、颜色和材质，杯子以外完全透明。'

# Native layers plus structured OCR, not a picture of a layer diagram.
uv run scripts/seedream_image_gen.py decompose --reference-image poster.png \
  --max-images 20 --text-recognition --size auto --out-dir output/poster-layers
```

`--dry-run` previews without credentials or API calls. Generate/edit previews may save new `dry_run: true` metadata and marker previews; they preserve existing metadata even with `--force`. Batch/decompose previews do not save result metadata.

## Prompt and inspect

Choose from the [four focused prompt recipes](references/seedream55-workflows.md): exact text, multi-round edits, semantic layer splitting/classification, and transparent assets. Each includes its API switches and artifact checks.

Write subject/action/environment, then composition, material/light and intended use. Quote exact text and specify its position, hierarchy, font style and color. For multi-reference work, assign roles explicitly in upload order: “图1产品形状，图2配色，图3布局”. Up to **10 references** are supported, including transparent mode. Prompts work in Chinese, English and 14 other documented languages; keep to about 300 Chinese characters or 600 English words — over-long prompts drop elements.

For editing, describe **one intended change plus what must remain**. Feed the last accepted output into the next round. Prefer RGB input and `--background opaque` during long edit chains; the official guide recommends this for consistency. Check the edited target and protected areas after every round, retaining checkpoints. A low pixel difference alone can also mean the requested change failed. Cumulative exposure drift is real even when protected pixels look unchanged: re-anchor from the accepted master (resend it as an extra reference) every 10–15 rounds and hard-restart from the master instead of stacking corrective prompts; never transit chain intermediates through JPEG. See the [editing recipe and QC procedure](references/seedream55-workflows.md).

For fixed-layout artwork, explicitly retain original positions, font size, object scale and whitespace; a generic “keep everything else” can still trigger redesign. For precise location, put `<point>x y</point>` or `<bbox>left top right bottom</bbox>` in the prompt, normalized to **0–999**. Name the object as well as the coordinates. These guide generation rather than enforcing a hard mask. Visible annotations are an alternative: `--marker-rect '5%,6%,90%,25%'` uses **x,y,width,height**, draws a temporary marked copy, and asks the model to remove marks. Read [marker editing](references/marker-editing.md) for those options.

Inspect exact strings, small text, dates, prices and units at full size and at intended display size. Alpha-channel presence does not establish realistic glass transparency; inspect the asset over light and dark backgrounds. Read [5.5 workflow recipes and community evidence](references/seedream55-workflows.md) for transparency, fusion, local edits and text replacement.

## Size, format and background

Native generation accepts `1K`, `1.5K`, `2K` or explicit `WIDTHxHEIGHT`: **921,600–4,624,220 total pixels**, aspect **1:16–16:1**. There is no native 3K/4K preset in the Ark 5.5 contract. For detailed typography, start at 2K and verify the result; presets use the prompt to determine aspect and do not guarantee arbitrary exact dimensions.

Shortcuts: `--square` 1024×1024; `--wide` / `--wechat-header` 1792×1024; `--portrait` 1536×2048; `--landscape` 2048×1152; `--phone` / `--stories` / `--wechat` 1152×2048. Small explicit targets are generated at a valid larger size then LANCZOS-downscaled; `--no-auto-upscale` rejects them instead.

PNG is the CLI default; `--output-format jpeg` is available. **Transparent requires PNG.** `--background auto` lets 5.5 choose based on the prompt; the CLI deliberately defaults to `opaque` for predictable ordinary artwork and editing. Set `transparent` explicitly for assets. 5.5 transparent inputs need no alpha channel and can be text-only or up to ten references.

## Layers and editable text

`decompose` requires **one PNG/JPEG**, ≤30 MB, 262,144–36,000,000 pixels, aspect at most 16:1. Size is `auto`, `1K`, `1.5K` or `2K`, without explicit pixels. `--max-images 2..100` limits **total outputs including the base**, not an exact requested layer count; the API default is 30. A higher limit can permit finer splitting and reserves more IPM before actual output is known.

The CLI immediately downloads the base and foreground PNGs and writes `layers.json`, preserving native crop dimensions, z-index, bounding boxes, names/descriptions, returned background type and full `text_recognition`. Crop positions and OCR line boxes use the **output base's** coordinate system; resize each crop to its bbox before placement. Do not stretch every layer to the full canvas.

For layer selection, combine the preview with returned names/descriptions; there is no documented native layer-type enum, and missing OCR does not mean a layer contains no text. OCR is opt-in and applies to regular text layers. It returns plain text, line boxes and runs with approximate font/color/style. Fonts are matches, not exact font files; unsupported or uncertain matches can be `unknown`. Artistic/handwritten text and nontext layers may have no OCR. Returned images are raster layers, not PSD text objects. For deterministic copy changes, omit the original text layer and typeset the replacement locally using an available font and its line bbox; inspect line wrapping and fit. Read [layer/OCR contract and reconstruction](references/transparent-layers.md) before composing or changing text.

## Options and failures

Common flags: `--out`, `--out-dir`, `--prompt-file`, `--watermark`, `--timeout`, `--force`, repeatable `--reference-image`, and `--safety-identifier` (hashed ASCII end-user id, ≤64 chars, sent to the platform but never written to local metadata). `edit --outpaint left:400` pads a local opaque canvas; unless you pass an explicit `--size`, the CLI requests the padded dimensions when they fit the native pixel contract, otherwise it warns and falls back to tier sizing — see [API/outpainting](references/api-reference.md#outpainting). Batch JSONL accepts prompt strings or objects with generation options (including per-job `safety_identifier`); `--concurrency` controls independent jobs. Decomposition uses its separate command.

The CLI accepts only the supported 5.5 model ID and aliases. Other models, including old Pro/Flash aliases and custom IDs, fail before an API request; no silent remapping or fallback is performed. Prompt optimization supports `standard` only. Historical model comparisons remain evaluation evidence, not current usage recipes.

Explicit 429/5xx responses have bounded retries. Unknown transport outcomes stop with `OutcomeUnknown`; do not resubmit a possibly billed request automatically. Failed downloads retry downloads without regenerating. Metadata records model, prompt, sizes, usage and timing, with no credentials or signed response URLs. Layer outputs can incur several output-image charges. See [API contract](references/api-reference.md) and [measured 5.5 benchmark](evals/seedream55-benchmark.md); historical Pro/Flash ratings do not establish 5.5 quality.
