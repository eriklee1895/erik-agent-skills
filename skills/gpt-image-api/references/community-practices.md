# Community practices and evidence status

Community material is empirical guidance, not an OpenAI API contract. Provider-specific fields and model names must not be copied into `scripts/gpt_image_api.py`.

Community patterns are absorbed in two layers: this file preserves evidence and
confidence; the optional assets under `assets/templates/` make only stable structural
parts reusable. Selection and adaptation rules live in
[template-selection.md](template-selection.md). Do not copy prompt-farm wording,
reconstructed hidden prompts, creator-name imitation, or provider-specific API fields
into template assets.

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

## Local 2.5 evidence

The 2026-09-16 paired run covered 16 generation jobs, one edit-source generation, and
10 edits against one configured custom endpoint. All 27 calls succeeded with no retry.
The UI pair both produced extra readable copy despite an allowlist; Flare's retrieval
infographic added explanatory sentences while Sunburst kept the five requested labels.
Both transparent spheres passed decoded Alpha validation, and all ten edit calls were
visually usable. These observations justify regression checks, not universal model
claims; the full scorecard is [here](../evals/live/results/2026-09-16-run-01.md).

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
