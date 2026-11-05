---
name: gpt-image-api
description: Use when a user wants GPT Image 2.6 Flare or Sunburst generation, native animated GIFs, SVG output, precise image edits, markup or masks, transparent assets, exact text, reference composition, or JSONL batches through an OpenAI-compatible Images API.
---

# GPT Image API

Create images, native GIF animations, and SVGs with GPT Image 2.6 using the bundled CLI. Inspect the decoded artifact; HTTP success does not establish visual quality or honored settings.

## Choose the mode

| Deliverable | Route |
| --- | --- |
| New still image, native GIF, or SVG | `generate` |
| Reference composition, preservation, mask, or markup edit | `edit`, with 1–16 raster inputs |
| Distinct generation prompts | `generate-batch`, JSONL |
| Reference → GIF through OFOX | `edit --experimental-gif-edit`; empirical provider extension |

Read [animated-gif.md](references/animated-gif.md) for GIF requests. The official OpenAI contract supports GIF and SVG generation only. OFOX GIF edits require explicit opt-in; other providers are rejected. Here, native GIF means a finished animation returned by the API. OpenAI's official demo describes generating a sprite sheet, automatically extracting its frames, and assembling the looping GIF.

## Choose the model and effort

- The agent chooses by the deliverable's fidelity, layout, and latency requirements. An explicit model choice always wins.
- Pass the resolved model explicitly: `gpt-image-2.6-flare` for everyday work and fast iteration; `gpt-image-2.6-sunburst` for demanding final assets or preservation.
- CLI aliases `flare` and `sunburst` resolve to the model IDs above. This guide and its prompt templates target these current models.
- Keep `quality=auto` initially. `complexity=low|medium|high` separately controls planning; omission uses the model default, currently high. More planning can increase latency and unwanted edits.
- Do not run both models for an ordinary request. Compare both only when the user explicitly requests a comparison or an evaluation requires it.

Read [model-selection.md](references/model-selection.md) for model routing, quality, and complexity.

## Workflow

1. Collect the deliverable, exact text, dimensions, destination, and constraints. Inspect reference images and assign each input a role.
2. Preserve a complete brief. For an incomplete brief, adapt one asset via [template-selection.md](references/template-selection.md); resolve placeholders and preserve creative latitude. The CLI sends prompts verbatim.
3. Dry-run complex, masked, markup, transparent, GIF, SVG, high-resolution, and batch requests. Inspect endpoint, model, fields, input order, and output paths.
4. Generate and inspect the actual result: text, identity, relationships, unintended drift, dimensions, format, and transparency. For GIFs, inspect every frame and play several cycles, including the seam.
5. Iterate with one targeted change and keep approved intermediates. Report output and metadata paths, model/provider, actual artifact settings, and remaining caveats.

## CLI

Set `SKILL_DIR` to this directory. Run from the user's project so `.env` and relative paths resolve:

```bash
uv run "$SKILL_DIR/scripts/gpt_image_api.py" generate \
  --model flare --prompt-file loop-prompt.txt --output-format gif \
  --size 512x512 --frame-count 9 --frame-duration-ms 200 \
  --complexity low --out output/gpt-image-api/loop.gif --dry-run
```

After reviewing the dry run, repeat without `--dry-run`. Native GIF/SVG requests reject streaming, compression, and downscaling. GIF controls are requested values: the sidecar records actual frames/timing and warns on mismatches. `--help` lists still-image, edit, streaming, batch, markup, and optional SVG author controls.

## Authentication and artifacts

Set `CUSTOM_OPENAI_API_KEY` and `CUSTOM_OPENAI_BASE_URL` together for a compatible provider; otherwise use `OPENAI_API_KEY` and optional `OPENAI_BASE_URL`. Working-directory `.env` is supported. Never copy credentials into prompts or outputs.

OFOX hosts `api.ofox.ai` and `api.ofox.io` namespace model IDs as `openai/gpt-image-2.6-flare` or `openai/gpt-image-2.6-sunburst`. Other hosts retain official IDs. Existing files are protected unless `--force` is explicit. Each output has a sibling JSON with prompt, canonical/wire model, provider, inputs, mask/markup, request/response settings, usage, timing, and actual artifact metadata. GIF and SVG bytes are preserved without raster conversion.

## References

- [image-api.md](references/image-api.md): parameters, format limits, errors, metadata.
- [generation.md](references/generation.md), [editing.md](references/editing.md), [prompting.md](references/prompting.md), [sample-prompts.md](references/sample-prompts.md): mode guidance and examples.
- [generation-core.md](assets/templates/generation-core.md), [editing-core.md](assets/templates/editing-core.md), [layout-and-text.md](assets/templates/layout-and-text.md), [characters-and-series.md](assets/templates/characters-and-series.md), [brand-product-and-space.md](assets/templates/brand-product-and-space.md): optional brief structures.
- [community-practices.md](references/community-practices.md): GIF experiments and provider observations.
- [official-links.md](references/official-links.md): current OpenAI documentation.
