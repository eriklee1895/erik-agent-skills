# GPT Image 2.6 model selection

Select the model before tuning quality or rewriting the prompt. Keep the same prompt, inputs, size, and format during comparisons.

## Models

| Goal | Model | Notes |
| --- | --- | --- |
| Fast, high-quality everyday work | `gpt-image-2.6-flare` | Default for generation, drafts, variants, batches, and ordinary edits. |
| Maximum quality or editing precision | `gpt-image-2.6-sunburst` | Use for demanding final assets, identity/product preservation, difficult layouts, and precise edits. |

CLI shorthands `flare` and `sunburst` resolve to the models above. Metadata records the resolved model ID.

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
3. For an authorized comparison, keep quality and complexity equal; change only the model.
4. Check the whole result, not just aesthetics: text, relationships, reference fidelity, unwanted edits, transparency, response time, and accepted-image cost.
5. When an authorized evaluation shows Flare meets the same bar, prefer it for that workflow. An ordinary request does not authorize an automatic second-model comparison.

## Quality

Both models accept `auto`, `low`, `medium`, `high`, `xhigh`, and `max`.

- `auto`: initial default when no measured target exists.
- `low`: drafts and rapid composition checks.
- `medium`: routine assets and early edit evaluation.
- `high`: final assets, small text, structured layouts, or preservation-sensitive work.
- `xhigh` / `max`: use only after a lower tier fails a defined acceptance criterion.

The same quality label does not guarantee the same output quality, latency, or token consumption across models. Equal token rates also do not imply equal cost per image; record response usage.

## Complexity is a separate axis

`low`, `medium`, and `high` control planning before rendering; omission uses the model's configured default, currently high. `quality` controls rendering. Do not map one automatically onto the other. Low complexity can suit focused edits and simple loops; higher complexity can help dense text and object relationships, but can also increase latency and unwanted changes. These are task-dependent starting points, not acceptance guarantees. Adjusting complexity has no separate fee according to the official guide; total usage still depends on the request.

For GIFs, choose the model for identity, readability, and usable motion, then measure actual frames and latency. A returned 512px nine-frame OFOX example is evidence for that route, not a universal GIF size, fixed duration, or guaranteed frame-control behavior. See [animated-gif.md](animated-gif.md).
