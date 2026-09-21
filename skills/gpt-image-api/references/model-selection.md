# GPT Image 2.5 model selection

Select the model before tuning quality or rewriting the prompt. Keep the same prompt, inputs, size, and format during comparisons.

## Models

| Goal | Model | Notes |
| --- | --- | --- |
| Fast, high-quality everyday work | `gpt-image-2.5-flare` | Default for generation, drafts, variants, batches, and ordinary edits. |
| Maximum quality or editing precision | `gpt-image-2.5-sunburst` | Use for demanding final assets, identity/product preservation, difficult layouts, and precise edits. |
| Reproducible Flare behavior | `gpt-image-2.5-flare-2026-09-08` | Pin for benchmarks, regression tests, and repeatable production runs. |
| Reproducible Sunburst behavior | `gpt-image-2.5-sunburst-2026-09-08` | Pin for quality-sensitive regression tests and production runs. |

CLI shorthands `flare` and `sunburst` resolve to the undated aliases. Metadata always records the resolved model ID.

## Ownership and overrides

The agent owns the default: when the user explicitly names a model, honor that
choice; otherwise choose from the deliverable's quality, fidelity, layout, and
latency requirements. Do not run both models for an ordinary request. Compare both
only when the user explicitly requests a comparison or an evaluation requires it.
The CLI default is Flare as a fallback; after making a routing decision, pass the
resolved model explicitly so the CLI cannot replace a quality-sensitive choice.

## Selection procedure

1. Start with Flare when speed matters or the request is routine.
2. Start with Sunburst when a missed instruction, changed identity, warped product, or layout error would invalidate the result.
3. Test with one explicit quality shared by both models.
4. Check the whole result, not just aesthetics: text, relationships, reference fidelity, unwanted edits, transparency, response time, and accepted-image cost.
5. If Sunburst passes, test Flare with the same request. Keep Sunburst only when its quality advantage is necessary.

## Local paired observation (2026-09-16)

One run against the configured custom endpoint compared eight identical generation
prompts and five identical edit prompts per model. Flare's paired-generation median
was about 78s versus Sunburst's 102s; its paired-edit median was about 22s versus
Sunburst's 26s. Both models passed the tested product, text-edit, identity, weather,
Mask, and outpaint calls. This is a workload observation, not a model guarantee:
repeat the comparison after changing the provider, SDK, snapshot, prompt, size, or
quality. Use the lowest-latency model only when it meets the same acceptance bar for the workflow.

## Quality

Both models accept `auto`, `low`, `medium`, `high`, `xhigh`, and `max`.

- `auto`: initial default when no measured target exists.
- `low`: drafts and rapid composition checks.
- `medium`: routine assets and early edit evaluation.
- `high`: final assets, small text, structured layouts, or preservation-sensitive work.
- `xhigh` / `max`: use only after a lower tier fails a defined acceptance criterion.

The same quality label does not guarantee the same output quality, latency, or token consumption across models. Equal token rates also do not imply equal cost per image; record response usage.
