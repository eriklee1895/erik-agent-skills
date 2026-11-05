# Image generation workflow

Use `generate` when no image input is needed. When an existing image must control the subject, identity, product, style, layout, or background, use `edit` and assign roles to the inputs.

## Production sequence

1. Decide the delivery slot and dimensions before composing the prompt.
2. Name the deliverable and audience.
3. Describe the subject, action, environment, composition, style/medium, lighting, materials, and only consequential exclusions.
4. Set the model and quality separately from the prompt.
5. Dry-run the request, generate, and evaluate the decoded image. For animated output, follow [animated-gif.md](animated-gif.md); for SVG selection and restrictions, read [image-api.md](image-api.md).

## Composition

State object counts, relative positions, crop, viewpoint, depth, and required negative space. Prefer relationships such as “the callout below the center diagram” to pixel coordinates. Large multi-section images should name each region and its content hierarchy.

The requested aspect ratio changes composition rather than merely cropping one latent image. Write framing for the chosen size.

## Text and information graphics

- Quote exact copy and specify how many times it appears.
- Keep labels short and hierarchy explicit.
- Define title, subtitle, body, callouts, and reading order.
- For diagrams, state required nodes and relationships; verify both labels and logic.
- Use higher quality only after a lower setting fails legibility or layout criteria.
- Finish copy-critical layouts in a deterministic design tool when exact typography is mandatory.

### Strict readable-text allowlist

For UI, infographics, slides, and other text-sensitive images, write an explicit
allowlist: only the quoted strings may be legible. State that every other field must
be blank, unlabeled, or a non-readable placeholder shape; do not let the model invent
card descriptions, prices, captions, button labels, or explanatory sentences. Treat
any unapproved readable string as a critical visual failure and inspect the complete
image, not only the requested labels.

When occurrence counts matter, state the count globally for the entire canvas, not only
per region. Explicitly forbid repeating an allowlisted label in navigation, section
headers, cards, footers, or badges; use icon-only or unlabeled shapes for repeated UI
affordances.

## Transparent assets

Set `background=transparent`, use PNG or WebP, and explicitly request a clean isolated subject with real alpha. For cutouts, specify crisp edges, no halos, preserved semi-transparent materials, no checkerboard, and no invented shadow unless wanted. Inspect hair, glass, reflections, and edge pixels. A simple opaque-edged subject passing Alpha validation does not establish that hair, glass, or soft shadows will pass.

## Variants and batches

Use `n` for variants of one prompt. Use `generate-batch` for distinct prompts. Batch JSONL accepts either a prompt string or an object:

```json
{"prompt":"A cobalt running shoe packshot","size":"1024x1024","quality":"medium"}
{"prompt":"A winter campaign banner","model":"sunburst","size":"2048x1152","out":"winter-banner.png"}
```

Per-job fields: `prompt`, `model`, `n`, `size`, `quality`, `complexity`, `background`, `output_format`, `output_compression`, `moderation`, `frame_count`, `frame_duration_ms`, `svg_model`, `svg_reasoning`, and relative `out`. Frame controls are GIF-only; SVG author fields are SVG-only. Unknown fields and duplicate output paths are rejected.

Dry-run validates JSONL fields, model controls, and duplicate destinations and prints the planned requests. It does not inspect existing destination files. Live execution additionally checks every final image and sibling metadata path before creating the API client. After a partial failure, create a failed-only JSONL for the retry; do not use `--force` on the original full batch unless replacing successful outputs is intentional. Save the command's JSON summary as a run log when failed-job auditing matters.

For example, a native GIF batch job is `{"prompt":"A panda waves once, then returns to its first pose. Locked camera, stable background.","model":"flare","output_format":"gif","size":"512x512","frame_count":9,"frame_duration_ms":200,"complexity":"low","out":"panda.gif"}`. Actual container metadata and request mismatches are recorded per output.
