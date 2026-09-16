# GPT Image 2.5 live scorecard

Copy this table into the dated eval-run directory after the outputs are generated.
Score each axis from 0 (failed) to 4 (excellent). Use the same reviewer and criteria
for the Flare/Sunburst pair before comparing model-level results. Text precision and
recall fields use `PASS/FAIL/N/A`.

| Case | Model | Instruction | Composition | Rendering | Identity / preservation | Artifact | Text precision | Text recall | Total / 20 | Critical failure | Notes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |
| natural-editorial | flare |  |  |  |  |  |  | N/A |  |  |  |
| natural-editorial | sunburst |  |  |  |  |  |  | N/A |  |  |  |
| product-hero | flare |  |  |  |  |  |  |  |  |  |  |
| product-hero | sunburst |  |  |  |  |  |  |  |  |  |  |
| exact-text-poster | flare |  |  |  |  |  |  |  |  |  |  |
| exact-text-poster | sunburst |  |  |  |  |  |  |  |  |  |  |
| ui-concept | flare |  |  |  |  |  |  |  |  |  |  |
| ui-concept | sunburst |  |  |  |  |  |  |  |  |  |  |
| retrieval-infographic | flare |  |  |  |  |  |  |  |  |  |  |
| retrieval-infographic | sunburst |  |  |  |  |  |  |  |  |  |  |
| transparent-sphere | flare |  |  |  |  |  |  | N/A |  |  |  |
| transparent-sphere | sunburst |  |  |  |  |  |  | N/A |  |  |  |
| character-sheet | flare |  |  |  |  |  |  | N/A |  |  |  |
| character-sheet | sunburst |  |  |  |  |  |  | N/A |  |  |  |
| article-distributed-systems | flare |  |  |  |  |  |  | N/A |  |  |  |
| article-distributed-systems | sunburst |  |  |  |  |  |  | N/A |  |  |  |

## Decision notes

- Mark `Critical failure` for missing required text, fake transparency, broken diagram
  logic, unusable anatomy, target-region failure, or material identity drift.
- The numeric total is Instruction, Composition, Rendering, Identity/preservation, and
  Artifact: 0–4 each, /20. For text-sensitive cases, record separate
  **Text precision** and **Text recall** as `PASS`, `FAIL`, or `N/A`.
- A case passes at 16/20 or higher with no critical failure; text-sensitive cases also
  require both precision and recall to be `PASS` as a critical gate.
- Record median and slowest elapsed time, usage totals, retry count, and any API refusal
  separately from the visual score.
- Select a model per workflow. Do not average away a critical failure or claim one model
  universally wins.
