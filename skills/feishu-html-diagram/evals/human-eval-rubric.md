# Human evaluation rubric

Use this rubric after the artifact has reached the evidence stage being assessed. A local browser review can score local-render quality; it cannot establish Feishu client experience. For `feishu-experience-valid`, a human must evaluate the actual rendered block in each promised Feishu surface and record Web, desktop, or both.

Score each dimension from 1 to 5. The descriptions below anchor the score; assess the visual's reader-facing outcome, not adherence to a template, named library, prose style, or evaluator preference.

| Dimension | 1 — unacceptable | 3 — adequate | 5 — excellent |
| --- | --- | --- | --- |
| Comprehension speed | The main claim, entities, or relationships cannot be understood without explanation or prolonged decoding. | A reader can identify the main claim and key relationships with modest effort. | The main claim and the most important relationships are apparent at a glance; hierarchy guides the reader naturally. |
| Professional visual quality | Layout, typography, connectors, spacing, colour, or contrast look unfinished or undermine trust. | Layout is consistent and legible, with minor roughness that does not obscure meaning. | Deliberate hierarchy, spacing, type, contrast, and visual restraint make the visual report-ready. |
| Semantic motion | When motion is present or necessary, it is decorative, distracting, inaccessible, uncontrollable, or absent despite being needed to explain the claim. | Present motion mostly represents a relevant flow or transition, does not prevent reading, and has applicable pause/reset behaviour. An intentionally static diagram is understandable without motion. | Motion precisely reveals state, sequence, or causality, remains restrained, respects reduced-motion needs, and has clear applicable pause/resume/reset controls; or the diagram is intentionally static because motion would not improve understanding. |
| Interaction discoverability | When interaction is present or necessary, it is hidden, confusing, inaccessible, stuck, or required to reveal core content. | Present interaction has visible affordances and can return to the initial state; the default carries the essential message. An intentionally non-interactive diagram needs no controls. | Interaction is obvious, keyboard-operable where relevant, clearly communicates state, and adds useful progressive disclosure without burdening the default view; or the diagram is intentionally non-interactive because controls would not improve the complete default view. |
| Default-zoom readability | At normal document reading width, text or relationships are clipped, overlapping, too small, or require zoom/scroll to understand the core. | The core remains readable at default zoom and expected document width, with non-critical density trade-offs. | Core content is immediately readable at default zoom and remains coherent at a narrower document width without relying on a desktop-wide canvas. |
| Integration with the surrounding document | The block feels detached from the document, repeats or contradicts context, or lacks an accessible reader-facing purpose. | The block has a clear purpose and fits the surrounding section with understandable framing. | The block advances the document's specific argument, uses a useful description/alt text, and feels intentionally composed for document reading rather than transplanted from an app. |

## Blocking failures

Any of the following blocks acceptance regardless of the average score:

- Clipping or overlap that hides core content at the assessed document width or default state.
- A console error during the assessed local or client interaction path.
- Unusable interaction when interaction is present or required: a control is undiscoverable, cannot be operated as intended, cannot return to an understandable initial state, or traps the reader away from core content.
- Missing core content after an optional dependency fails, including an external script, font, image, data source, or library.
- A score below 3 on any dimension.

Record the failure, surface, viewport/document width where relevant, and evidence observed. Do not average away a blocking failure.

## Evidence statement to attach to the scorecard

Record the highest evidence state separately from the quality scores:

- `contract-valid`: structural and safety checks only.
- `local-render-valid`: locally rendered and exercised at the exact recorded normal and narrower widths.
- `feishu-write-valid`: authorized write, fetch-back, target placement, and recovered artifact match verified.
- `feishu-experience-valid`: human evaluation completed in the actual promised Feishu Web and/or desktop surface; name every evaluated and untested surface.

Neither an XML writer response nor a local browser score is evidence of Feishu client rendering. If only local evidence exists, report the local score and leave Feishu client evaluation as remaining work.

## Scorecard

| Item | Record |
| --- | --- |
| Artifact and reader-facing purpose | |
| Evaluator and date | |
| Evaluated surface(s) and exact tested width(s) | |
| Highest evidence state | |
| Comprehension speed (1–5) | |
| Professional visual quality (1–5) | |
| Semantic motion (1–5) | |
| Interaction discoverability (1–5) | |
| Default-zoom readability (1–5) | |
| Integration with surrounding document (1–5) | |
| Blocking failures observed | |
| Untested client, dependency, interaction, or human-evaluation items | |
| Final result | Accept only if no blocker is present and every dimension is 3 or higher. |
