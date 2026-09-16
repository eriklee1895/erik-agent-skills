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

Adopt the structural parts that improve clarity. Do not claim that a community pattern improves GPT Image 2.5 until representative live comparisons show it.
