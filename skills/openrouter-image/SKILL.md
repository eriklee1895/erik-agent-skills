---
name: openrouter-image
description: "Use when generating or editing raster images through OpenRouter with GPT Image 2.6 Sunburst/Flare, Nano Banana 2.1, Grok Imagine Image 2.0, or MAI-Image-2.6: photos, posters, text-heavy layouts, product shots, illustrations, reference composites, variants, or JSONL batches. Also use to check whether OpenRouter exposes a requested GPT Image 2.6 GIF or SVG feature. Excludes code-native diagrams and deterministic layout."
---

# openrouter-image

Generate and edit images through OpenRouter's unified image API, using five
curated models:

| Alias | Model | Use for |
|---|---|---|
| `sunburst` | openai/gpt-image-2.6-sunburst | GPT detail tier; text/layout, reference edits, variants, transparency |
| `flare` | openai/gpt-image-2.6-flare | GPT speed tier; drafts, variants, transparency |
| `banana` | google/gemini-nano-banana-2.1 | ultra-wide/tall, large canvases, routine reference edits, 1K–4K |
| `grok` | x-ai/grok-imagine-image-2.0 | subject-led generation, local edits and reframing; separate resolution/quality controls, 3 refs |
| `mai` | microsoft/mai-image-2.6 | combine composition, subject, product and style references; iterative edits, up to 5 refs |

OpenRouter's GPT 2.6 endpoints currently expose **PNG, JPEG, and WebP stills**.
Their model descriptions mention native animated GIF, SVG, and markup editing,
but the definitive endpoint descriptors do not expose those controls. A live
GIF request returned HTTP 400 on 2026-11-05. For native GIF/SVG requirements,
explain this route limitation and use a supported native API only when the
user's requested access path allows it. Do not replace a GIF request with a
static image or claim that prompted motion creates an animation.

Use the table for routine selection. Read only the references relevant to the job:

- [references/model-routing.md](references/model-routing.md) — when comparing
  precision, speed, format, or cost tradeoffs.
- [references/sunburst-flare-prompting.md](references/sunburst-flare-prompting.md)
  — GPT text/layout, reference edits, variants, and transparent assets.
- [references/banana-prompting.md](references/banana-prompting.md) — Banana
  text/layout, reference roles, follow-up edits, extreme ratios, and API limits.
- [references/grok-prompting.md](references/grok-prompting.md) — Grok subject,
  material and light descriptions, targeted edits, reframing, and API controls.
- [references/mai-prompting.md](references/mai-prompting.md) — MAI multi-reference
  roles, composition authority, iterative edits, and access-path limits.
- [references/batch.md](references/batch.md) — JSONL preflight, output collisions,
  failure summaries, and controlled retries; read before running a batch.

For demanding copy, composites, or edits, read the chosen model's guide before
briefing it. These guides are self-contained.

## Workflow

1. Classify the request: new image (`generate`), edit/composite existing images
   (`edit`), or many jobs from a file (`batch`).
2. Honor a specified model. Otherwise route by required controls: variants or
   transparency → sunburst/flare; extreme ratios or 4K → banana; Grok generation
   or reframing with separate detail controls → grok; MAI reference composition
   or iterative edits → mai. For ordinary work without a model preference or
   format constraint, use the default sunburst. These are capability-based
   starting points; compare outputs for the actual brief when quality decides.
3. Use the parameters that match the model's declaration (the CLI rejects
   mismatches): GPT models take `--quality` + `--n` + `--background`; banana
   takes `--resolution` with n=1; grok supports independent `--resolution` and
   `--quality` controls with n=1; mai has no detail control, n=1. The model guides
   specify defaults and omissions. GPT models also take `--complexity`
   (`low/medium/high`, planning before rendering) and GPT models expose
   `--output-format png/jpeg/webp`. Compression requires explicit JPEG/WebP;
   transparent backgrounds require PNG/WebP.
4. For complex requests, run `--dry-run` first and inspect the exact JSON body.
5. Run the script with `python3` (standard library only, no install needed).
6. Inspect the saved image and its sibling `.json` metadata: exact copy, counts,
   preserved details, returned dimensions, and actual `usage.cost`. Use the
   recorded output paths; the saved suffix follows the returned image bytes.
   `response.images[].media_type` preserves the server's format label when
   supplied, while byte detection determines the saved extension.

For a cost-sensitive request, check current OpenRouter rates and the relevant
reference/detail settings before estimating spend. Use actual `usage.cost` for
completed calls; no alias is selected as a permanently cheapest option. Dry-run
validates request structure and does not estimate charges.

Ratio/resolution are best effort. Accept provider dimensions; this CLI does
not crop, resize, or regenerate on a pixel mismatch. Apply exact sizing only
when the user requires it. Examples run from the skill directory; elsewhere
use the script's full path. Input paths resolve from the working directory.

Authentication: `OPENROUTER_API_KEY` in the environment or a `.env` file.

The Image API calls are stateless and this CLI exposes no thinking, search, or
explicit mask control. Supply verified facts and reference images explicitly.
Banana starts at `1K`; large poster headings can work at 1K. Use `2K` for finer
copy/detail and consult its guide for examples and measured tradeoffs.

## Examples

```bash
# Sunburst: text-heavy poster at high quality
python3 scripts/openrouter_image.py generate \
  --model sunburst \
  --prompt "竖版科技发布会海报，主标题“智能体时代”，副标题“2026 开发者大会”，大字清晰排版" \
  --aspect 3:4 --quality high \
  --out output/poster.png

# Flare: high-quality still with less planning and explicit WebP encoding
python3 scripts/openrouter_image.py generate \
  --model flare \
  --prompt "A cozy alpine cabin at dawn, mist over the lake, warm light" \
  --aspect 16:9 --quality high --complexity low --output-format webp \
  --out output/cabin.webp

# Banana (Nano Banana 2.1): 4K ultra-wide, resolution dialect
python3 scripts/openrouter_image.py generate \
  --model banana \
  --prompt "A wide cinematic market street at golden hour, rich detail" \
  --aspect 21:9 --resolution 4K \
  --out output/market.png

# Grok Imagine 2.0: stylized 2K illustration
python3 scripts/openrouter_image.py generate \
  --model grok \
  --prompt "精致日漫插画头像，紫发设计师，发光蝴蝶，柔和侧光" \
  --aspect 1:1 --resolution 2K --quality medium \
  --out output/avatar.png

# MAI-Image-2.6: product composition with an explicit setting
python3 scripts/openrouter_image.py generate \
  --model mai \
  --prompt "极简陶瓷杯产品图，奶油白背景，柔和侧光" \
  --aspect 1:1 \
  --out output/cup.png
```

## Editing

Provide one or more reference images with repeated `--image`. The CLI limits the
count per model (16 for GPT, 14 for banana, 5 for MAI, 3 for Grok) and embeds
them as `input_references`.

```bash
# Keep a product exactly as-is, change only the background (sunburst)
python3 scripts/openrouter_image.py edit \
  --model sunburst \
  --image product.png \
  --prompt "仅把背景换成暖色日落渐变，产品本体与边缘完全保持不变。" \
  --quality high --aspect 1:1 \
  --out output/product-newbg.png

# Composite two references with banana
python3 scripts/openrouter_image.py edit \
  --model banana \
  --image person.png --image location.png \
  --prompt "Image 1 is the person, image 2 is the location. Place the same person naturally in that location, matching the light direction." \
  --resolution 2K --aspect 3:4 \
  --out output/person-in-location.png
```

Number references in their `--image` order, assign each a role, and name concrete
preserved details. For follow-ups, pass the approved base again. The model guides
cover source authority and drift recovery; generative edits do not guarantee
unchanged pixels.

## Batch from JSONL

```bash
python3 scripts/openrouter_image.py batch \
  --input prompts.jsonl --out-dir output/batch --dry-run

python3 scripts/openrouter_image.py batch \
  --input prompts.jsonl --out-dir output/batch
```

Each line is one job:

```json
{"name":"poster", "model":"sunburst", "prompt":"…", "aspect_ratio":"3:4", "quality":"high"}
{"name":"wide-scene", "model":"banana", "prompt":"…", "aspect_ratio":"21:9", "resolution":"4K"}
```

Supported job fields: `name`, `model` (alias or full id), `prompt`,
`aspect_ratio`, `quality` / `resolution` (per model), `n`, `background`,
`images` (reference paths), `output_compression`, `output_format`, `complexity`.
The last two fields follow the model restrictions above. Results and a
`batch-summary.json` land in the output directory. Jobs run sequentially.
Legacy `aspect` is accepted; if both ratio keys are present, they must match.
The full batch is validated before paid calls; unsupported fields are rejected.
The summary checkpoints actual paths/cost after each attempt; a failed job makes
execution exit nonzero. Read [batch execution and recovery](references/batch.md)
for collision rules, dry-run limits, and retrying selected jobs.

## Quick parameter reference

| | sunburst / flare | banana | grok | mai |
|---|---|---|---|---|
| Detail | `--quality` auto→max | `--resolution` 1K/2K/4K | `--resolution` 1K/2K + `--quality` low/medium | none |
| Planning | `--complexity` low/medium/high | none | none | none |
| Encoding | `--output-format` png/jpeg/webp | provider default | provider default | provider default |
| Variants | `--n` up to 10 | n = 1 | n = 1 | n = 1 |
| References | up to 16 | up to 14 | **up to 3** | up to 5 |
| Transparency | `--background transparent` | unsupported | unsupported | unsupported |
| Ratios | incl. 21:9 | incl. 8:1, 4:1 | incl. 20:9 | 1:1/4:3/3:4/16:9/9:16/3:2/2:3 |

Resolution labels are provider settings, not fixed dimensions or evidence of
native rendering detail. Inspect actual sizes; each model guide records any
observed dimensions separately from supported controls.

The CLI checks each model's declared parameters, ratios, detail values, output
counts, and reference ceilings before calling. For example, banana with
`--quality`, mai with `--n 2`, or grok with a fourth `--image` fails with an
explanatory message.

## Notes

- `--out` supplies the destination stem; GPT encoding is selected separately
  with `--output-format`. Banana
  returned JPEG in the live probes; the CLI saves `.jpg` when JPEG bytes arrive,
  even if `--out` ends in `.png`, and preserves the returned bytes. Reference
  MIME types are also detected from bytes, including older mislabeled files.
- The returned `.json` records `usage.cost` per call — check it for spend.
- Error codes: 402 out of credit, 404 unknown model / no provider, 429 rate
  limited or upstream quota exhausted, 502 upstream failure. A quota/billing
  429 needs upstream resolution; inspect usage rather than assuming a failed
  request was unbilled. The CLI does not retry or silently switch models.
- Streaming (SSE) is supported by the two GPT models but not yet exposed by this
  CLI; buffered generation is the default.
