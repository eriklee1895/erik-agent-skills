---
name: gpt-image-api
description: Use when a user wants to generate, edit, or batch-create raster images through OpenAI's GPT Image 2.5 Image API, including reference-guided work, masks, exact in-image text, transparent backgrounds, compositing, variants, JSONL batches, or explicit model, quality, size, and output controls.
---

# GPT Image API

Generate and edit images with OpenAI's current GPT Image 2.5 Flare and Sunburst models through the Image API. Use the bundled CLI instead of writing one-off SDK scripts.

## Choose the mode

- `generate`: create an image from text only.
- `edit`: provide one to sixteen images when preserving, replacing, combining, extracting, or restyling existing visual content. The first image is the edit target when a mask is present.
- `generate-batch`: process distinct generation prompts from JSONL with bounded concurrency.

Read [generation.md](references/generation.md) for new images. Read [editing.md](references/editing.md) for any image input, including reference-guided creation. For a complex brief, also read [prompting.md](references/prompting.md).

## Choose the model

- Default to `gpt-image-2.5-flare` for everyday generation, drafts, variants, and ordinary edits.
- Use `gpt-image-2.5-sunburst` when quality or editing precision is the priority: identity and product preservation, dense layouts, difficult compositing, exact text, or final campaign assets.
- Use a dated `2026-09-08` snapshot when reproducibility matters.
- Keep `quality=auto` initially. Raise it only to solve an observed quality problem; use `xhigh` or `max` when the improvement justifies the additional latency and token use.

Read [model-selection.md](references/model-selection.md) before choosing between models or pinning a snapshot.

## Workflow

1. Collect the intended deliverable, prompt, exact text, dimensions, output path, and constraints.
2. For every input image, assign its role by index: edit target, identity reference, product reference, style reference, background, or compositing insert.
3. Write the prompt. The CLI sends it verbatim and never silently augments it.
4. Run `--dry-run` for complex, masked, transparent, high-resolution, or batch requests. Inspect the model, endpoint, prompt, input order, and outputs.
5. Run the request. Existing files are protected unless `--force` is explicit.
6. Inspect the actual result: subject, composition, text, identity/product details, unintended drift, and real alpha transparency when requested.
7. Iterate with one targeted change. Keep approved intermediate images.

## CLI

Run the bundled script with `uv run` from this skill directory. Its PEP 723 dependencies are installed in an isolated environment.

```bash
# Generate
uv run scripts/gpt_image_api.py generate \
  --prompt-file prompt.txt \
  --model flare \
  --size 1536x1024 \
  --quality high \
  --out output/gpt-image-api/hero.png

# Precise edit with two role-labeled inputs and a mask
uv run scripts/gpt_image_api.py edit \
  --image product.png --image-role "edit target" \
  --image person.png --image-role "identity reference" \
  --mask mask.png \
  --prompt-file edit-prompt.txt \
  --model sunburst \
  --size 1536x1024 \
  --out output/gpt-image-api/product-edit.png

# Stream two partial images plus the final image
uv run scripts/gpt_image_api.py generate \
  --prompt "A quiet winter river made of white feathers" \
  --stream --partial-images 2 \
  --out output/gpt-image-api/river.png

# Batch distinct prompts
uv run scripts/gpt_image_api.py generate-batch \
  --input prompts.jsonl \
  --out-dir output/gpt-image-api/batch \
  --concurrency 5
```

Use `--help` on the root command and each subcommand for the complete executable interface.

## Authentication and outputs

For a custom endpoint, set `CUSTOM_OPENAI_API_KEY` and `CUSTOM_OPENAI_BASE_URL` together; the CLI never pairs a standard OpenAI key with a custom host. Otherwise it uses `OPENAI_API_KEY` and optional `OPENAI_BASE_URL`. The same variables may be loaded from `.env` in the working directory. Credentials are never written to output.

Each final image receives a sibling `.json` containing the exact prompt, resolved model, requested and returned settings, input roles, mask path, elapsed time, attempts, request ID when available, and token usage when returned. Transparent output requires PNG or WebP and is rejected if the decoded result lacks transparent pixels.

## References

- [image-api.md](references/image-api.md): parameters, limits, streaming, responses, and errors.
- [model-selection.md](references/model-selection.md): Flare, Sunburst, quality, and snapshots.
- [generation.md](references/generation.md): generation, text, layouts, transparency, and variants.
- [editing.md](references/editing.md): precise edits, references, masks, compositing, and iterative work.
- [prompting.md](references/prompting.md): shared GPT Image 2.5 prompt construction.
- [sample-prompts.md](references/sample-prompts.md): compact production-ready examples.
- [community-practices.md](references/community-practices.md): evidence-labeled empirical practices.
- [official-links.md](references/official-links.md): canonical OpenAI documentation.
