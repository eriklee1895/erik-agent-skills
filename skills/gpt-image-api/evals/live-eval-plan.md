# GPT Image 2.5 live evaluation plan

This evaluation exercises the bundled CLI against the configured OpenAI-compatible
endpoint. It is intentionally separate from `evals/evals.json`: that file describes
agent behavior, while this plan records observable model and artifact quality.

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

The first command is the paid-call gate. Confirm `network_call=false`, 16 jobs, correct
wire model IDs, and no existing output collisions before running the second command.

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

Score every output from 0–4 on each axis:

- **Instruction following:** requested subject/action and exclusions.
- **Composition/layout:** framing, hierarchy, counts, relationships, and usable space.
- **Rendering quality:** materials, lighting, anatomy, texture, and coherence.
- **Text/identity/preservation:** exact text where applicable; identity/product and
  non-target regions for edits.
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
