---
name: gpt-image-api
description: Use when a user wants to generate, edit, or batch-create raster images through OpenAI's GPT Image 2.5 Image API, including reference-guided work, masks, exact in-image text, transparent backgrounds, compositing, variants, JSONL batches, or explicit model, quality, size, and output controls.
---

# GPT Image API

Generate and edit images with OpenAI's GPT Image 2.5 Flare and Sunburst models through the Image API. Use the CLI instead of writing SDK scripts.

## Choose the mode

- `generate`: create an image from text only.
- `edit`: provide one to sixteen images when preserving, replacing, combining, extracting, or restyling existing visual content. The first image is the edit target when a mask is present.
- `generate-batch`: process distinct generation prompts from JSONL with bounded concurrency.

Read [generation.md](references/generation.md) for new images and [editing.md](references/editing.md) for image inputs. For complex briefs, also read [prompting.md](references/prompting.md). Complete briefs skip templates; incomplete briefs may load one matching asset via [template-selection.md](references/template-selection.md).

## Choose the model

- When the user does not name a model, the agent chooses by quality, fidelity, layout,
  and latency requirements.
- An explicit model choice always wins.
- Default to `gpt-image-2.5-flare` for everyday generation, drafts, variants, and ordinary edits.
- Use `gpt-image-2.5-sunburst` when quality or editing precision is the priority: identity and product preservation, dense layouts, difficult compositing, exact text, or final campaign assets.
- Use a dated `2026-09-08` snapshot when reproducibility matters.
- Keep `quality=auto` initially. Raise it only to solve an observed quality problem; use `xhigh` or `max` when the improvement justifies the additional latency and token use.
- Do not run both models for an ordinary request. Compare both only when the user
  explicitly requests a comparison or the evaluation requires it.

Read [model-selection.md](references/model-selection.md) before choosing between models or pinning a snapshot.

## Workflow

1. Collect the deliverable, prompt, exact text, dimensions, output path, and constraints.
2. Inspect inputs and assign each role by index: edit target, identity, product, style, background, or compositing insert.
3. Shape the final prompt. Preserve a complete brief; when an incomplete brief needs structural help, adapt one template without stacking templates or constraining unspecified creative choices. Resolve every placeholder. The CLI sends the result verbatim and never silently augments it.
4. Run `--dry-run` for complex, masked, transparent, high-resolution, or batch requests. Inspect the model, endpoint, prompt, input order, and outputs.
5. Run the request. Existing files are protected unless `--force` is explicit.
6. Inspect the actual result: subject, composition, text, identity/product details, unintended drift, and real alpha transparency when requested.
7. Iterate with one targeted change. Keep approved intermediate images.
8. Report the saved image and metadata paths, model, provider, and any unresolved visual caveat.

## CLI

Keep the working directory at the user's project so `.env` and relative output paths resolve there. Set `SKILL_DIR` to this installed skill directory, then invoke its bundled script with `uv run`; PEP 723 dependencies are installed in an isolated environment.

```bash
# Generate
uv run "$SKILL_DIR/scripts/gpt_image_api.py" generate \
  --prompt-file prompt.txt \
  --model flare \
  --size 1536x1024 \
  --quality high \
  --out output/gpt-image-api/hero.png

# Precise edit with two role-labeled inputs and a mask
uv run "$SKILL_DIR/scripts/gpt_image_api.py" edit \
  --image product.png --image-role "edit target" \
  --image person.png --image-role "identity reference" \
  --mask mask.png \
  --prompt-file edit-prompt.txt \
  --model sunburst \
  --size 1536x1024 \
  --out output/gpt-image-api/product-edit.png

# Stream two partial images plus the final image
uv run "$SKILL_DIR/scripts/gpt_image_api.py" generate \
  --prompt "A quiet winter river made of white feathers" \
  --stream --partial-images 2 \
  --out output/gpt-image-api/river.png

# Batch distinct prompts
uv run "$SKILL_DIR/scripts/gpt_image_api.py" generate-batch \
  --input prompts.jsonl \
  --out-dir output/gpt-image-api/batch \
  --concurrency 5
```

Use `--help` on the root command and each subcommand for the complete executable interface.

## Authentication and outputs

For a custom endpoint, set `CUSTOM_OPENAI_API_KEY` and `CUSTOM_OPENAI_BASE_URL` together; the CLI never pairs a standard OpenAI key with a custom host. Otherwise it uses `OPENAI_API_KEY` and optional `OPENAI_BASE_URL`. The same variables may be loaded from `.env` in the working directory. Credentials are never written to output.

All providers use the current OpenAI Images API. OFOX base URLs (`api.ofox.ai` and the earlier `api.ofox.io`) automatically namespace the two wire model IDs as `openai/gpt-image-2.5-flare` and `openai/gpt-image-2.5-sunburst`. Other providers keep the unprefixed official model IDs. No endpoint or request-shape branch is introduced.

Each final image receives a sibling `.json` containing the exact prompt, canonical and provider-facing model IDs, requested and returned settings, input roles, mask path, elapsed time, attempts, request ID when available, and token usage when returned. Buffered requests print a heartbeat about every 15 seconds. Batches accept at most 500 jobs and print progress plus a final summary. Transparent output requires PNG or WebP and is rejected if the decoded result lacks transparent pixels.

## References

- [image-api.md](references/image-api.md): parameters, limits, streaming, responses, and errors.
- [model-selection.md](references/model-selection.md): Flare, Sunburst, quality, and snapshots.
- [generation.md](references/generation.md): generation, text, layouts, transparency, and variants.
- [editing.md](references/editing.md): precise edits, references, masks, compositing, and iterative work.
- [prompting.md](references/prompting.md): shared GPT Image 2.5 prompt construction.
- [template-selection.md](references/template-selection.md): when to skip, select, and adapt template assets without limiting creative latitude.
- [sample-prompts.md](references/sample-prompts.md): compact production-ready examples.
- [generation-core.md](assets/templates/generation-core.md): photos, editorial illustrations, transparent assets, historical scenes, and game assets.
- [editing-core.md](assets/templates/editing-core.md): bounded edits, references, identity, products, environments, and iterative repair.
- [layout-and-text.md](assets/templates/layout-and-text.md): posters, diagrams, UI concepts, slides, and publication layouts.
- [characters-and-series.md](assets/templates/characters-and-series.md): character sheets, pose grids, recurring characters, storyboards, and collectibles.
- [brand-product-and-space.md](assets/templates/brand-product-and-space.md): product, brand, campaign, architecture, and development-board briefs.
- [community-practices.md](references/community-practices.md): evidence-labeled empirical practices.
- [official-links.md](references/official-links.md): canonical OpenAI documentation.
