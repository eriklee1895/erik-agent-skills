# GPT Image 2.5 live scorecard

Copy this table into the dated eval-run directory after the outputs are generated.
Score each axis from 0 (failed) to 4 (excellent). Use the same reviewer and criteria
for the Flare/Sunburst pair before comparing model-level results.

| Case | Model | Instruction | Composition | Rendering | Text / identity / preservation | Artifact | Total / 20 | Critical failure | Notes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| natural-editorial | flare |  |  |  |  |  |  |  |  |
| natural-editorial | sunburst |  |  |  |  |  |  |  |  |
| product-hero | flare |  |  |  |  |  |  |  |  |
| product-hero | sunburst |  |  |  |  |  |  |  |  |
| exact-text-poster | flare |  |  |  |  |  |  |  |  |
| exact-text-poster | sunburst |  |  |  |  |  |  |  |  |
| ui-concept | flare |  |  |  |  |  |  |  |  |
| ui-concept | sunburst |  |  |  |  |  |  |  |  |
| retrieval-infographic | flare |  |  |  |  |  |  |  |  |
| retrieval-infographic | sunburst |  |  |  |  |  |  |  |  |
| transparent-sphere | flare |  |  |  |  |  |  |  |  |
| transparent-sphere | sunburst |  |  |  |  |  |  |  |  |
| character-sheet | flare |  |  |  |  |  |  |  |  |
| character-sheet | sunburst |  |  |  |  |  |  |  |  |
| article-distributed-systems | flare |  |  |  |  |  |  |  |  |
| article-distributed-systems | sunburst |  |  |  |  |  |  |  |  |

## Decision notes

- Mark `Critical failure` for missing required text, fake transparency, broken diagram
  logic, unusable anatomy, target-region failure, or material identity drift.
- A case passes at 16/20 or higher with no critical failure.
- Record median and slowest elapsed time, usage totals, retry count, and any API refusal
  separately from the visual score.
- Select a model per workflow. Do not average away a critical failure or claim one model
  universally wins.
