# Historical prompt provenance and evaluation evidence

These records describe GPT Image 2.5 source material and past evaluations. Production guidance is maintained in the current model references and templates. Use this archive when tracing a source or reproducing a historical evaluation.

## Earlier prompting sources

| Practice | Source | Official overlap | Local evaluation | Benefit | Tradeoff |
| --- | --- | --- | --- | --- | --- |
| Open with the deliverable and decide dimensions before framing | [Runware prompting guide](https://runware.ai/docs/models/openai-gpt-image-2-5-flare/guides/prompting) | Consistent with OpenAI's intended-use and composition guidance | Not yet benchmarked | Gives the model a concrete layout target | Can overconstrain exploratory ideation |
| Use exact numeric counts and positions relative to named objects | [Runware prompting guide](https://runware.ai/docs/models/openai-gpt-image-2-5-flare/guides/prompting) | Consistent with explicit composition guidance | Not yet benchmarked | More inspectable than “several” or pixel coordinates | Counts and positions still require visual QA |
| Name medium, material, lighting, and optical behavior instead of vague style adjectives | [Runware prompting guide](https://runware.ai/docs/models/openai-gpt-image-2-5-flare/guides/prompting) | Consistent with OpenAI's visible-detail guidance | Not yet benchmarked | Produces actionable visual constraints | Camera terms are cues, not physical guarantees |
| Write edits as one change followed by a longer preservation list | [Runware editing guide](https://runware.ai/docs/models/openai-gpt-image-2-5-flare/guides/editing-images) | Directly overlaps OpenAI's change-versus-preserve guidance | One bounded Sunburst check changed only badge color while preserving text and alpha; broader quality remains unverified | Reduces ambiguous edit scope | Long lists can conflict if not curated |
| Keep intermediates; compare accumulated drift with the original; consolidate settled edits | [Runware iterative-editing guide](https://runware.ai/docs/models/openai-gpt-image-2-5-flare/guides/iterative-editing) | Consistent with one-change-at-a-time iteration | Not yet benchmarked | Preserves approval checkpoints and exposes texture drift | Consolidation costs an extra render |
| Keep exclusions short and role-label references | [Community reconstruction analysis](https://cybercorsairs.com/someone-reverse-engineered-278-hidden-prompts/) | Reference roles overlap official guidance; short-exclusion claim is community-only | Not yet benchmarked | Reduces vague reference use and prompt clutter | Source prompts are reconstructions, not OpenAI originals |
| Attach source status and per-template visual QA | [Community 2.5 template pack](https://github.com/wuyoscar/GPT-Image2-Skill/blob/main/skills/gpt-image/references/templates-gpt-image-2.5.md) | Visual inspection and preservation checks overlap official guidance | Structure reviewed; templates not reproduced locally | Makes empirical material auditable and prevents prompt constraints from being mistaken for guarantees | Source model and local verification vary by template |
| Route by deliverable category, then load one template | [Community industrial template library](https://github.com/freestylefly/awesome-gpt-image-2/blob/main/docs/templates.md) | Intended use and artifact type overlap official deliverable-first guidance | Taxonomy reviewed; individual prompts not imported or benchmarked | Improves retrieval across brand, space, series, publishing, and technical work | Large reverse-engineered libraries contain stale, verbose, or model-specific material |


## Earlier local evaluations

Historical material below remains **GPT Image 2.5** evidence. No old score, latency, or template trial is promoted to a 2.6 benchmark.

## Local 2.5 evidence

The 2026-09-16 paired run covered 16 generation jobs, one edit-source generation, and
10 edits against one configured custom endpoint. All 27 calls succeeded with no retry.
The UI pair both produced extra readable copy despite an allowlist; Flare's retrieval
infographic added explanatory sentences while Sunburst kept the five requested labels.
Both transparent spheres passed decoded Alpha validation, and all ten edit calls were
visually usable. These observations justify regression checks, not universal model
claims; the full scorecard is [here](../live/results/2026-09-16-run-01.md).

The follow-up allowlist run removed the unapproved explanatory copy from both
infographics and reduced UI copy to placeholders, but both UI outputs repeated the
allowlisted labels in multiple regions. Treat global occurrence count and repeated
navigation labels as a separate regression dimension.

The v3 global-count run removed repeated labels from the UI layouts, but introduced a
precision/recall tradeoff: Flare rendered the structural numerals but omitted all five
required word labels; Sunburst rendered the five word labels and allowed numerals
without explanatory copy. Required UI copy should therefore be typeset deterministically
after the model supplies the visual layout. Keep v2 and v3 as separate evidence; do not
call the stronger wording a universal fix.

For UI specifically:

- UI: Flare omitted `VENDORS`, `SPECIALS`, and `PROFILE` in v3.
- UI: Sunburst omitted `PROFILE`.

For the infographic, Flare precision passed but recall failed; Sunburst passed both.
Keep UI and infographic results as separate categories.

The 2026-09-21 article-driven live check used the two community posts
[赛博踱步](https://mp.weixin.qq.com/s/9dy4JoyqZFHuAWO9utISpA) and
[远见明察](https://mp.weixin.qq.com/s/Dwbow-EPAmz1y640HJdLcg) as hypothesis sources,
not as API contracts. It produced 12 accepted outputs plus one transient batch failure
that succeeded when the failed item was retried. The controlled edit pair tested a one-line
minimal-delta instruction against the structured `Change / Preserve / Avoid` form on the
same lamp-move task with both models. Both forms made the intended local edit and plausible
relighting; the structured form was not visibly superior in this small sample, and latency
was not monotonic, so do not mandate long prompts for obvious local edits.

The same run produced coherent 3×3 multi-camera continuity sheets with Flare and Sunburst,
usable 4×4 sixteen-pose action sheets with both models, a readable Sunburst visual abstract,
and a readable Flare executive-summary concept without obvious extra copy. A conservative
Sunburst restoration improved a 512×341 derivative, but the result remains generative rather
than lossless restoration. These outputs support optional scaffolds for minimal-delta edits,
baseline locking, restoration, multi-camera continuity, and source-grounded one-page summaries;
they do not establish universal identity, frame, typography, or restoration guarantees.

The first six-job batch had one connection failure and later completed the failed item
separately. Keep transient retry evidence separate from visual quality, and inspect every
panel or text string before treating a contact sheet or summary as production-ready.

Adopt the structural parts that improve clarity. Do not claim that a community pattern improves GPT Image 2.5 until representative live comparisons show it.

## Historical 2.5 paired observation (2026-09-16)

This run used GPT Image 2.5; it does not measure 2.6. One run against the configured custom endpoint compared eight identical generation
prompts and five identical edit prompts per model. Flare's paired-generation median
was about 78s versus Sunburst's 102s; its paired-edit median was about 22s versus
Sunburst's 26s. Both models passed the tested product, text-edit, identity, weather,
Mask, and outpaint calls. This is a workload observation, not a model guarantee:
repeat the comparison after changing the provider, SDK, snapshot, prompt, size, or
quality. Use the lowest-latency model only when it meets the same acceptance bar for the workflow.


## Template source notes

### brand-product-and-space

Source file [brand-product-and-space.md](../../assets/templates/brand-product-and-space.md).

**Evidence/status:** Community brand-touchpoint pattern rewritten as a reference-guided 2.5 composition template; not a substitute for a deterministic brand guideline.

### characters-and-series

Source file [characters-and-series.md](../../assets/templates/characters-and-series.md).

**Evidence/status:** Source-attributed community adaptation from a [GPT Image 2.5 pose-sheet workflow](https://github.com/wuyoscar/GPT-Image2-Skill/blob/main/skills/gpt-image/references/templates-gpt-image-2.5.md); the structure is useful but not locally benchmarked across actions.

**Evidence/status:** Two local GPT Image 2.5 runs produced coherent 3×3 sheets with both
models; this remains a continuity heuristic, not a guarantee for every cast or scene.

**Evidence/status:** Official multi-turn character-consistency pattern from the [GPT Image 2.5 guide](https://developers.openai.com/api/docs/guides/image-prompting).

### editing-core

Source file [editing-core.md](../../assets/templates/editing-core.md).

**Evidence/status:** Official single-change pattern from the [GPT Image 2.5 editing examples](https://developers.openai.com/api/docs/guides/image-prompting), reinforced by community preservation workflows.

**Evidence/status:** Official identity insertion/preservation pattern from the [GPT Image 2.5 guide](https://developers.openai.com/api/docs/guides/image-prompting).

**Evidence/status:** Official one-condition iterative-edit pattern from the [GPT Image 2.5 guide](https://developers.openai.com/api/docs/guides/image-prompting).

### generation-core

Source file [generation-core.md](../../assets/templates/generation-core.md).

**Evidence/status:** Adapted from the [official GPT Image 2.5 prompting guide](https://developers.openai.com/api/docs/guides/image-prompting); structure locally reviewed, not a quality guarantee.

**Evidence/status:** Original 2.5-oriented scaffold informed by OpenAI's deliverable-first and concrete-visual-language guidance; not benchmarked as a fixed style.

### layout-and-text

Source file [layout-and-text.md](../../assets/templates/layout-and-text.md).

**Evidence/status:** Official exact-text pattern plus a source-attributed community [poster adaptation](https://github.com/wuyoscar/GPT-Image2-Skill/blob/main/skills/gpt-image/references/templates-gpt-image-2.5.md).

**Evidence/status:** Selective structural adaptation from the community [industrial template library](https://github.com/freestylefly/awesome-gpt-image-2/blob/main/docs/templates.md); requires 2.5 visual evaluation.

**Evidence/status:** Official productivity-visual pattern from the [GPT Image 2.5 guide](https://developers.openai.com/api/docs/guides/image-prompting); deterministic charting remains preferable for exact data graphics.

**Evidence/status:** Two local GPT Image 2.5 checks produced usable visual-abstract and
executive-summary concepts; text-heavy success is sample evidence, not a guarantee.

## Model IDs used by historical callers

The CLI accepts explicit `gpt-image-2.5-flare`, `gpt-image-2.5-sunburst`, and their `2026-09-08` snapshots. Historical JSONL files retain their effective model IDs.

- [Flare model reference](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare)
- [Sunburst model reference](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst)
