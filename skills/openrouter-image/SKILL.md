---
name: openrouter-image
description: "Use when generating or editing raster images through OpenRouter with GPT Image 2.5 Sunburst/Flare or Nano Banana 2.1: photos, posters, text-heavy layouts, product shots, illustrations, reference composites, variants, or JSONL batches. Especially relevant when the user names OpenRouter, Nano Banana, Sunburst/Flare, or wants one API key for these models. Excludes SVG, code-native diagrams, and deterministic layout."
---

# openrouter-image

Generate and edit images through OpenRouter's unified image API, using three
curated models:

| Alias | Model | Use for |
|---|---|---|
| `sunburst` | openai/gpt-image-2.5-sunburst | precise text, dense layouts, final assets, transparency |
| `flare` | openai/gpt-image-2.5-flare | fast everyday generation, drafts, variants |
| `banana` | google/gemini-nano-banana-2.1 | ultra-wide/tall, large canvases, routine reference edits, 1K–4K |

Use the table for routine selection. Read only the references relevant to the job:

- [references/model-routing.md](references/model-routing.md) — when comparing
  precision, speed, format, or cost tradeoffs.
- [references/sunburst-flare-prompting.md](references/sunburst-flare-prompting.md)
  — GPT text/layout, reference edits, variants, and transparent assets.
- [references/banana-prompting.md](references/banana-prompting.md) — Banana
  text/layout, reference roles, follow-up edits, extreme ratios, and API limits.

- [references/batch.md](references/batch.md) — JSONL preflight, output collisions,
  failure summaries, and controlled retries; read before running a batch.

For demanding copy, composites, or edits, read the chosen model's guide before
briefing it. These guides are self-contained.

## Workflow

1. Classify the request: new image (`generate`), edit/composite existing images
   (`edit`), or many jobs from a file (`batch`).
2. Honor a specified model. Otherwise: strict copy/identity/layout → sunburst;
   fast everyday generation → flare; extreme ratios, large canvases, or routine
   reference recontextualization → banana. Reference count alone does not rank
   edit quality; compare actual outputs when preservation is critical.
3. Use the parameters that match the model's dialect (the CLI rejects mismatches):
   GPT models take `--quality` + `--n` + `--background`; banana takes
   `--resolution`, n=1, no transparency.
4. For complex requests, run `--dry-run` first and inspect the exact JSON body.
5. Run the script with `python3` (standard library only, no install needed).
6. Inspect the saved image and its sibling `.json` metadata: exact copy, counts,
   preserved details, returned dimensions, and actual `usage.cost`. Use the
   recorded output paths; the saved suffix follows the returned image bytes.

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

# Flare: fast everyday image at high quality
python3 scripts/openrouter_image.py generate \
  --model flare \
  --prompt "A cozy alpine cabin at dawn, mist over the lake, warm light" \
  --aspect 16:9 --quality high \
  --out output/cabin.png

# Banana (Nano Banana 2.1): 4K ultra-wide, resolution dialect
python3 scripts/openrouter_image.py generate \
  --model banana \
  --prompt "A wide cinematic market street at golden hour, rich detail" \
  --aspect 21:9 --resolution 4K \
  --out output/market.png
```

## Editing

Provide one or more reference images with repeated `--image`. The CLI limits the
count per model (16 for GPT, 14 for banana) and embeds them as
`input_references`.

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
`aspect_ratio`, `quality` / `resolution` (per dialect), `n`, `background`,
`images` (reference paths), `output_compression`. Results and a
`batch-summary.json` land in the output directory. Jobs run sequentially.
Legacy `aspect` is accepted; if both ratio keys are present, they must match.
The full batch is validated before paid calls; unsupported fields are rejected.
The summary checkpoints actual paths/cost after each attempt; a failed job makes
execution exit nonzero. Read [batch execution and recovery](references/batch.md)
for collision rules, dry-run limits, and retrying selected jobs.

## Quick parameter reference

| | sunburst / flare | banana |
|---|---|---|
| Detail | `--quality` auto/low/medium/high/xhigh/max | `--resolution` 1K/2K/4K |
| Variants | `--n` up to 10 | n = 1 |
| References | up to 16 | up to 14 |
| Transparency | `--background transparent` | unsupported |
| Ratios | incl. 21:9 | incl. 8:1, 4:1 |

The CLI checks model/dialect combinations, ratios, quality/resolution values,
output counts, and reference ceilings before calling. For example, banana with
`--quality`, `--n 3`, or `--resolution 512` fails with an explanatory message.

## Notes

- `--out` supplies the destination stem, not an output-format request. Banana
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
