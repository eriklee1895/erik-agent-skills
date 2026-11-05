# Model routing guide

Five curated models behind OpenRouter's dedicated Image API. Select by the
requested model, required controls, and reference workflow. Each model guide
owns its parameters, prompting methods, and verification limits.

## Decision matrix

| Requirement | Candidate | Basis |
|---|---|---|
| Several variants in one call | sunburst / flare | `--n` up to 10; other aliases return one |
| Transparent background | sunburst / flare | explicit background control |
| GPT text/layout or controlled edits | sunburst; flare for the speed tier | same controls; base and speed tiers, respectively |
| Ultra-wide/tall `8:1`, `1:8`, `4:1`, or 4K output setting | banana | supported ratios and resolution settings |
| Grok subject-led stills, reframing, or targeted edits | grok | independent 1K/2K and low/medium controls; up to three references |
| MAI compositions combining subject, product, scene and style | mai | up to five references; role/authority-based iterative editing |
| More than three references | mai (up to 5), banana (14), GPT (16) | Grok's endpoint accepts at most three |
| Image based on current facts | research, then chosen model | this CLI has no search/grounding control |
| Cost-constrained batch | compare current rates and request settings | no fixed cheapest model or stored price ranking |

Grok and MAI also generate images without references. Their rows identify useful
workflows, not capabilities exclusive to them or a ranking against other models.
For an ordinary request with no model preference or control requirement, use the
CLI default, sunburst. Honor an explicitly requested model when it can meet the
requirements; explain a required model change before generating.

## Match the controls to the deliverable

Sunburst and Flare share quality, variants, reference, and background controls.
Model selection and `--quality` are separate choices: Flare at `max` is still the
speed tier. Inspect copy and preserved details on either model.

Banana exposes 1K/2K/4K and extreme ratios. Start at 1K for a draft or large
headings; increase the resolution when the intended viewing size needs it. A
prior 4K/21:9 probe returned 6336×2688. This is an observed canvas, not evidence
of better detail, text accuracy, or the internal rendering method.

Grok exposes resolution and quality independently. Pin both for a controlled
comparison; leaving either absent uses the provider's default. Use its guide's
subject/material/light recipe for generation, and a focused change followed by
preservation instructions for edits and reframing.

MAI combines multiple visual sources without a quality or resolution flag on
this CLI. Assign each reference a role and choose which source governs framing,
identity, product details, and style. Reuse the approved base for the next edit.
The reference ceiling does not measure identity preservation or fusion quality.

## Quality and cost decisions

Check outputs against the actual brief: exact copy, counts, composition, face or
product details, and requested dimensions. A successful sample is evidence for
that sample; it does not establish a stable model ranking. When a quality choice
matters, compare candidates on the same brief, references, and delivery size.

For a budget estimate, consult current OpenRouter model/endpoint rates and state
the request assumptions: reference inputs, detail settings, output count, and
batch size. Use a range when token usage is unknown. Read actual `usage.cost`
from saved metadata and `batch-summary.json` after execution; missing usage is
unknown spend. Preflight/dry-run performs no generation and returns no quote.

## Prompting references

- [sunburst-flare-prompting.md](sunburst-flare-prompting.md): quoted copy,
  Change/Preserve edits, variants, and transparency.
- [banana-prompting.md](banana-prompting.md): text/layout, reference authority,
  stateless follow-ups, extreme formats, and endpoint boundaries.
- [grok-prompting.md](grok-prompting.md): subject/material/light structure,
  targeted edits, reframing, and independent detail settings.
- [mai-prompting.md](mai-prompting.md): multi-reference composition, source
  precedence, iterative edits, and grounding boundaries.

## Access path and sources

This CLI uses `/api/v1/images`. Native APIs and other gateways can expose
different values or extra controls; use the chosen guide's OpenRouter matrix.
The CLI does not retry or silently switch models. See [batch.md](batch.md) for
preflight, actual output paths, failure receipts, and controlled recovery.

- [OpenRouter Image API](https://openrouter.ai/docs/guides/overview/multimodal/image-generation)
- [OpenRouter image model descriptors](https://openrouter.ai/api/v1/images/models)
- [Sunburst](https://openrouter.ai/openai/gpt-image-2.5-sunburst),
  [Flare](https://openrouter.ai/openai/gpt-image-2.5-flare),
  [Banana](https://openrouter.ai/google/gemini-nano-banana-2.1),
  [Grok](https://openrouter.ai/x-ai/grok-imagine-image-2.0), and
  [MAI](https://openrouter.ai/microsoft/mai-image-2.6): current model information
  and rates.
