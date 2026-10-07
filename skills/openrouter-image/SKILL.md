---
name: openrouter-image
description: "Generate and edit raster images through OpenRouter with GPT Image 2.5 Sunburst/Flare or Gemini 3.1 Flash (Nano Banana 2). Use for OpenRouter image requests: photos, posters, text-heavy layouts, product shots, illustrations, reference-guided edits or composites, variants, and JSONL batches. Especially relevant when the user names OpenRouter, Sunburst, Flare, or Nano Banana, or wants one API key across these models. Includes model-specific parameter validation, dry-run previews, and per-call cost records."
---

# openrouter-image

Generate and edit images through OpenRouter's unified image API, using three
curated top models:

| Alias | Model | Best at |
|---|---|---|
| `sunburst` | openai/gpt-image-2.5-sunburst | precise text, dense layouts, final assets, transparency |
| `flare` | openai/gpt-image-2.5-flare | fast everyday generation, drafts, variants |
| `banana` | google/gemini-3.1-flash-image | Nano Banana 2: multi-reference edits, strong grounding, ultra-wide, up to 4K |

Read the references when picking a model or briefing a specific one:

- [references/model-routing.md](references/model-routing.md) — decision matrix,
  how the three behave, failure modes, and how this skill's access path relates
  to the other image skills.
- [references/sunburst-flare-prompting.md](references/sunburst-flare-prompting.md)
  — how to brief the two GPT Image 2.5 models (text allowlists, Change/Preserve
  edits, references, variants, transparency).
- [references/banana-prompting.md](references/banana-prompting.md) — how to
  brief Nano Banana 2 (multi-image fusion, conversational edits, 4K/ultra-wide).

This skill is self-contained: everything needed to brief the three models is
inside it, no other skill is required.

## Workflow

1. Classify the request: new image (`generate`), edit/composite existing images
   (`edit`), or many jobs from a file (`batch`).
2. Pick the model: precise/final → sunburst; fast/draft → flare; multi-reference
   edit or ultra-wide → banana.
3. Use the parameters that match the model's dialect (the CLI rejects mismatches):
   GPT models take `--quality` + `--n` + `--background`; banana takes
   `--resolution`, n=1, no transparency.
4. For complex requests, run `--dry-run` first and inspect the exact JSON body.
5. Run the script with `python3` (standard library only, no install needed).
6. Return the saved images and report cost from sibling `.json` metadata or the
   batch summary. Review text, identity, or other content when the brief needs it.

Ratio and resolution are **best effort**: send the selected supported values and
accept the provider's output dimensions. The CLI does not crop, resize, reject,
or regenerate an image because its pixels differ from the requested ratio.

The examples run from this skill's directory. From another directory, use the
full path to `scripts/openrouter_image.py`; reference and prompt-file paths still
resolve from the current working directory.

Authentication: `OPENROUTER_API_KEY` in the environment or a `.env` file.

## Examples

```bash
# Sunburst: text-heavy poster at high quality
python3 scripts/openrouter_image.py generate \
  --model sunburst \
  --prompt "竖版科技发布会海报，主标题“智能体时代”，副标题“2026 开发者大会”，大字清晰排版" \
  --aspect 3:4 --quality high \
  --out output/poster.png

# Flare: fast everyday image (flare + quality max for max detail on the fast tier)
python3 scripts/openrouter_image.py generate \
  --model flare \
  --prompt "A cozy alpine cabin at dawn, mist over the lake, warm light" \
  --aspect 16:9 --quality high \
  --out output/cabin.png

# Banana (Nano Banana 2): 4K ultra-wide, resolution dialect
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

When editing, number the images in the prompt ("image 1 …, image 2 …") and state
explicitly what must be preserved — this is what keeps identity, text, and
unchanged regions from drifting.

## Batch from JSONL

```bash
# Validate every job and inspect normalized requests without API calls or output files
python3 scripts/openrouter_image.py batch \
  --input prompts.jsonl --out-dir output/batch --dry-run

# Execute after inspecting the preview
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
`batch-summary.json` land in the output directory.
`output_compression` is GPT-only and must be an integer from 0 to 100.
It is ignored for PNG output; it controls JPEG/WebP compression when those
formats are returned by the provider.

Use `aspect_ratio` in JSONL. Legacy `aspect` remains accepted; if both keys are
present, their values must match. The `generate` / `edit` CLI flag is still
`--aspect`.

`prompt` is required and must be a non-empty string. Defaults apply only when a
field is omitted: model=`sunburst`, aspect_ratio=`1:1`, n=1, GPT quality=`auto`,
banana resolution=`1K`, images=[]; unnamed outputs use `job-000`, etc., based on
the physical zero-based row. Explicit nulls, empty strings, invalid types or
model values, dialect mismatches, and unknown fields (including typos) are
errors. `images` must be a list of reference path strings; paths resolve from
the current working directory, as they do for `--image`. Blank lines and lines
starting with `#` are ignored.

`name` is a filename stem, not a path: no `/`, `\`, NUL, `.` or `..` names.
Output names must not collide within a batch (case-insensitive), including
numbered variants, metadata, and the reserved `batch-summary.json`.
For n>1, previews list `name-1.png`, `name-2.png`, etc. Providers may return fewer
than n images; one returned image uses `name.png`, and the summary records the
actual saved paths. Existing files at chosen targets are replaced after a
complete write; use a fresh output directory to keep older runs.

The entire batch is parsed, validated, and its references loaded before the
first API call. An invalid row reports its physical **1-based line number** and
stops the batch before any API calls or output writes. `--dry-run` performs the
same preflight and prints JSON with each job's line, name, model alias, normalized
request, and expected output paths. Existing directories at file targets and
file parents are rejected before execution. Preflight cannot predict provider
failures or later filesystem changes.

Batch execution is sequential. `batch-summary.json` is replaced atomically
after each attempted job, before the next API call. Each entry includes `name`,
`line`, `model`, `status`, actual `outputs`, `cost`, and `elapsed_seconds`; failures
also have `error_type`. `cost: null` means no cost was reported, not zero spend.
HTTP, network, and malformed-response errors are recorded and later jobs can
continue. A local save failure stops the batch to avoid more paid calls; the
summary contains only attempted jobs and retains any saved paths and known cost.
Execution exits 0 when all jobs succeed and 1 if any job fails.

Requests are attempted once, with no automatic retries. Before retrying, inspect
the summary and saved metadata and create a JSONL containing only the jobs you
want to retry. A timeout alone does not establish the final server outcome;
check OpenRouter's activity records when cost is unknown. Response checks cover
the JSON/data/base64 structure, not visual quality or pixel dimensions.

Offline regression tests (standard library only):

```bash
python3 -m unittest discover -s skills/openrouter-image/tests -v
```

## Quick parameter reference

| | sunburst / flare | banana |
|---|---|---|
| Detail | `--quality` auto/low/medium/high/xhigh/max | `--resolution` 512/1K/2K/4K |
| Variants | `--n` up to 10 | n = 1 |
| References | up to 16 | up to 14 |
| Transparency | `--background transparent` | unsupported |
| Ratios | incl. 21:9 | incl. 8:1, 4:1 |

Every mismatch (e.g. `--quality` on banana, `--n 3` on banana, a ratio the model
doesn't support) is caught with an explanatory message before the API call.

## Notes

- The returned `.json` records `usage.cost` per call — check it for spend.
- Error codes: 402 out of credit, 404 unknown model / no provider, 429 rate
  limited, 502 upstream failure. OpenRouter documents failed generations as
  unbilled; a local save failure after receiving an image is a different outcome
  and can retain a reported cost. See the [Image API documentation](https://openrouter.ai/docs/guides/overview/multimodal/image-generation).
- Streaming (SSE) is supported by the two GPT models but not yet exposed by this
  CLI; buffered generation is the default.
