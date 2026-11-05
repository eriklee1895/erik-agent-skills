# GPT Image 2.6 live evaluation plan

This evaluation exercises the bundled CLI against the configured OpenAI-compatible
endpoint. It is intentionally separate from `evals/evals.json`: that file describes
agent behavior, while this plan records observable model and artifact quality.

The September matrices and reports are historical **2.5** evidence. Their shorthand IDs are now written as the original effective undated `gpt-image-2.5-flare` / `gpt-image-2.5-sunburst` names so moving CLI aliases cannot silently switch a replay to 2.6. This preserves the historical model family; undated aliases still do not guarantee snapshot reproducibility. `generation-matrix-26.jsonl` is a separate current-generation copy; `native-gif-matrix-26.jsonl` adds native animation coverage. Keep run artifacts and credentials outside the published skill.

## 2.6 native-format checks

Run only the cases required by the user's task; a prepared matrix is not a reason to repeat paid successful calls.

1. Dry-run the GIF matrix with the current configured provider. Verify `output_format=gif`, exact 2.6 model/wire ID, frame fields, per-frame size, complexity, unique output paths, and `network_call=false`.
2. Generate a short mascot loop, a product microloop, a transparent loop, and a label-sensitive loop as needed. Record real container, dimensions, frame count, per-frame timing, cycle duration, unique frames, loop metadata, alpha across frames, latency, and usage. Separate requested fields from decoded facts.
3. Play several cycles, inspect the seam, and check identity, text, contacts, fixed background, and flicker. A loop flag or a successful HTTP status does not satisfy the visual gate.
4. Compare one lower/higher complexity pair with all other settings fixed only when that comparison is authorized. Quality and complexity remain independent axes.
5. For reference GIFs, use the explicitly enabled OFOX extension and record the provider. Other providers and the official OpenAI edit contract do not gain support from this observation.
6. For markup, construct at least two plausible targets and a left/right annotation A/B while keeping text identical. A single-object edit cannot prove the layer controlled spatial targeting. The local OFOX A/B failed; retain that uncertainty.
7. For SVG, use `n=1`, no stream/compression/downscale, and decode UTF-8 XML. Verify static vector structure and inspect rendering. If the provider requires `svg.model`, select a confirmed author model explicitly; record separate `svg_usage`. The local OFOX route returned a missing-`svg.model` error even with a confirmed author supplied; SVG remained blocked there. Selector flags implement the documented request, not a verified OFOX workaround.
8. Confirm invalid combinations fail before paid calls: frame fields on PNG, GIF/SVG streaming/compression/downscale, official GIF edit, markup+mask, invalid markup geometry/alpha, and 2.6-only fields on legacy pins.

Current provider observations are documented in [animated-gif.md](../references/animated-gif.md) and [community-practices.md](../references/community-practices.md). Do not copy account-specific receipts, access URLs, or generated media into the published source.

## Historical raster evaluation procedure

The sections below preserve the 2.5 baseline method. To measure 2.6, select `generation-matrix-26.jsonl` explicitly and keep that run's result separate.

## Goals

1. Verify Flare and Sunburst accept the same current Image API request contract.
2. Compare quality, instruction following, latency, usage, and failure behavior on
   representative generation and edit workloads.
3. Check native transparency, exact text, reference roles, mask boundaries, output
   metadata, and non-destructive file handling.
4. Produce evidence that supports workflow-specific model selection, not a universal
   winner claim.

## Controls

- Use the configured `CUSTOM_OPENAI_API_KEY` and `CUSTOM_OPENAI_BASE_URL`; never print
  either value. The CLI loads them from the process environment or the project `.env`.
- Keep prompt, input images, size, quality, background, and output format identical for
  Flare/Sunburst pairs. Only `model` changes.
- Use one request per distinct prompt. Use `n` only for variants of the same prompt.
- Start with `quality=medium` for ordinary cases and `high` for text/layout cases.
  Do not silently upgrade quality after a miss; record the miss and run a targeted
  follow-up only when needed.
- Save every output and sibling metadata under a dated `output/gpt-image-api/eval-run-*`
  directory. The output directory is ignored by Git.

## Generation matrix

`generation-matrix.jsonl` contains eight prompts, each repeated for Flare and Sunburst:

| Case | Primary acceptance checks |
| --- | --- |
| Natural editorial photo | anatomy, material realism, natural light, no staged polish |
| Product hero | product geometry, label spelling, material, negative space |
| Exact-text poster | every required string, count, hierarchy, no extra text |
| UI concept | practical hierarchy, readable short labels, no browser chrome |
| Technical infographic | nodes, arrows, count, reading order, factual labels |
| Transparent asset | genuine alpha, clean edges, preserved holes/reflections |
| Character consistency sheet | view count, identity, outfit, proportions, scale |
| Article illustration | thesis/visual metaphor, hierarchy, editorial usability |

The UI and infographic cases use an explicit readable-text allowlist. Any additional
legible copy is a critical failure even when the requested labels are correct.

`regression-text-matrix.jsonl` repeats those two cases with the strengthened allowlist
wording after the first run's extra-copy failures. Compare its outputs against the
original matrix; do not silently replace the original evidence.

`regression-text-matrix-v3.jsonl` adds a global occurrence count and forbids repeating
allowlisted labels in navigation, section headers, cards, footers, or badges. Keep all
three generations as separate evidence when judging whether the wording helped.

Run:

```bash
RUN_DIR="output/gpt-image-api/eval-run-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR/generation"
uv run "$SKILL_DIR/scripts/gpt_image_api.py" generate-batch \
  --input "$SKILL_DIR/evals/live/generation-matrix.jsonl" \
  --out-dir "$RUN_DIR/generation" \
  --concurrency 2 \
  --max-attempts 3 \
  --timeout 300 \
  --dry-run
uv run "$SKILL_DIR/scripts/gpt_image_api.py" generate-batch \
  --input "$SKILL_DIR/evals/live/generation-matrix.jsonl" \
  --out-dir "$RUN_DIR/generation" \
  --concurrency 2 \
  --max-attempts 3 \
  --timeout 300
```

Inspect the first command's `network_call=false`, 16 jobs and wire model IDs before
running the second command. Batch dry-run validates structure and duplicate destinations.
Live execution additionally checks existing image and sidecar paths before creating the
API client.

## Edit matrix

After generation, create a clean base scene and identity reference with two additional
single-image generations. Run these same edit prompts against both models:

1. precise object removal or replacement with no scene drift;
2. exact label/text replacement with unchanged non-target copy;
3. identity-preserving person insertion with role-labeled references;
4. lighting/weather-only change;
5. mask-guided local edit with a same-dimension PNG mask;
6. outpaint to a wider canvas while preserving the original region.

For each edit, record input paths and roles, requested change, preserved invariants,
output dimensions, and visual QA. Do not treat a successful HTTP response as a quality
pass.

## Scoring rubric

Score the five numeric axes from 0–4:

- **Instruction following:** requested subject/action and exclusions.
- **Composition/layout:** framing, hierarchy, counts, relationships, and usable space.
- **Rendering quality:** materials, lighting, anatomy, texture, and coherence.
- **Identity/preservation:** identity/product fidelity and non-target regions for edits.
- **Text precision / recall:** for text-sensitive cases, record separate PASS/FAIL/N/A
  gates for no unapproved/repeated text and all required strings with their global counts;
  these are critical gates, not numeric axes.
- **Artifact correctness:** format, dimensions, alpha, output path, metadata, request ID,
  and usage.

Generation passes at `>=16/20` with no critical failure (missing required text, fake
transparency, broken diagram logic, or unusable anatomy). Edits use the same threshold,
but any target-region failure or material identity drift is critical. Report per-case
scores, median and slowest elapsed time, usage totals, retry count, and qualitative notes.

## Interpretation

- Prefer the lowest-cost/latency model that passes the workflow's acceptance threshold.
- A Sunburst win on a precision edit does not establish a generation-wide win.
- A Flare latency win matters only if the output still passes the same acceptance bar.
- Prompt changes, input changes, quality changes, and model changes must not be mixed in
  one comparison.
- Keep failed outputs and metadata when diagnosing; do not delete evidence or rerun the
  full matrix with `--force`.
