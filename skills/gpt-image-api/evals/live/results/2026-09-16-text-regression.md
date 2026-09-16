# GPT Image 2.5 text-constraint regression runs

These runs test progressively stronger text constraints against the same custom
endpoint. Outputs remain in ignored local directories under `output/gpt-image-api/`.

## Results

| Run | Prompt change | Result |
| --- | --- | --- |
| v1 (`eval-run-20260916-01`) | Short labels plus no extra text | Both UI models added extra readable copy; Flare infographic added explanatory sentences. |
| v2 (`eval-run-20260916-02`) | Explicit allowlist; other fields become blank/unlabeled placeholders | Both infographics removed explanatory copy; both UI models still repeated allowlisted labels across header, sections, and navigation. |
| v3 (`eval-run-20260916-03`) | Global occurrence count; no repeated labels; icon-only navigation; structural numerals explicitly allowed | Flare precision PASS / recall FAIL: it rendered the structural numerals but omitted all five word labels. Sunburst precision PASS / recall PASS: it rendered the five word labels and allowed numerals without explanatory copy. |

UI: Flare omitted `VENDORS`, `SPECIALS`, and `PROFILE`.
UI: Sunburst omitted `PROFILE`.
Infographic v3: Flare precision PASS / recall FAIL; Sunburst precision PASS / recall PASS.

## Reusable guidance

- An allowlist controls what text is permitted but does not guarantee occurrence count.
- A global “exactly once” rule can suppress duplicates while also causing required labels
  to disappear.
- For UI or graphics where text completeness is non-negotiable, generate the visual
  layout with icon-only or placeholder regions, then add approved copy in a deterministic
  design/typesetting step.
- Keep both precision (no unapproved text) and recall (all required strings present) in
  the scorecard. A successful API response is not a text-quality pass.

## Evidence

- v1 outputs and baseline scorecard: `output/gpt-image-api/eval-run-20260916-01/` and [`2026-09-16-run-01.md`](2026-09-16-run-01.md)
- v2 outputs: `output/gpt-image-api/eval-run-20260916-02/regression/`
- v3 outputs: `output/gpt-image-api/eval-run-20260916-03/regression/`
- Source prompts: [`regression-text-matrix.jsonl`](../regression-text-matrix.jsonl) and [`regression-text-matrix-v3.jsonl`](../regression-text-matrix-v3.jsonl)
