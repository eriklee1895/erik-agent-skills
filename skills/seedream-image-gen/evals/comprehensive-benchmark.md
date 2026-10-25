# Pro / Flash prompt benchmark — 2026-10-25

**120 intentional requests succeeded, producing 128 images.** The main study covers eighteen cases with two samples per standard model, plus Pro-fast on four cases: eighty requests. Five controlled follow-ups add forty requests. Every planned request and output is retained in [the redacted results](comprehensive-results.json); no unknown/failed requests were discarded or automatically resubmitted.

Pro remains the default for every unspecified model request. A faster result or a particular style does not authorize switching models. Flash requires explicit selection or explicit authorization to trade quality for speed/cost. This is a user preference, not a conclusion inferred from this small benchmark.

## Method and interpretation

- Dated model IDs: Pro `doubao-seedream-5-0-pro-260628`, Flash `doubao-seedream-5-0-flash-260915`; official Beijing Images API.
- Fixed synthetic references, prompts, size, PNG output, no watermark and no undocumented quality-negative default within each comparison. Pro's existing runtime negative default is unchanged; this controlled study does not establish its effectiveness.
- Six local workers, fixed shuffled order, with an initial four-request smoke slice. No provider seed, fixed-IPM scheduler or automatic model fallback. Every case has a durable pre-send journal and at most one generation submission.
- Four explicit case-specific criteria, scored 0=missed, 1=partial, 2=met. A strict pass means all four are met. Visual-quality notes are descriptive. Contact sheets hide model labels during review; the same agent designed and judged the study, so this is not independent human blind evaluation. Subjective camera-angle/font-weight/placement judgments are not a universal quality score.
- Every output was inspected. Local macOS Vision OCR provided an auxiliary transcription for the eighty main and twenty-four initial A/B requests; visual reading determined text judgments. The published result does not treat OCR as a quality judge.
- Two samples per case/configuration measure only these examples. They do not establish a population ranking, latency SLA, hard pixel mask or reliable failure probability. The main samples use 1.5K/2K and two explicit delivery sizes; 1K quality, real-photo identity consistency and long story sequences were not tested.

## Main study

The table gives API median seconds and strict rubric passes out of two samples. The native decomposition case has three outputs per request. A partial pass may be a useful picture with one missed layout/style requirement.

| Case | Pro standard: seconds; passes | Flash standard: seconds; passes | Pro fast: seconds; passes |
|---|---:|---:|---:|
| Chinese poster | 52.48; 2/2 | 15.53; 2/2 | 27.59; 2/2 |
| Mixed Chinese/English cards | 45.83; 2/2 | 12.14; 2/2 | — |
| Product photography | 36.24; 2/2 | 15.11; 2/2 | 27.50; 2/2 |
| Portrait, two hands and one cup | 38.86; 2/2 | 14.92; 2/2 | — |
| Editorial book-page ocean | 39.58; 2/2 | 11.92; 1/2 | — |
| Hand-drawn technology | 44.47; 0/2 | 11.62; 2/2 | — |
| Chinese ink wash | 48.89; 2/2 | 12.55; 2/2 | — |
| Isometric 3D icon | 49.90; 2/2 | 10.00; 0/2 | — |
| Coordinate recoloring | 25.02; 2/2 | 10.02; 2/2 | 21.75; 2/2 |
| Filled-marker recoloring | 26.89; 2/2 | 9.66; 0/2 | — |
| Replace NOVA with 星野 | 34.37; 0/2 | 14.59; 2/2 | — |
| Remove vase and add lemon | 43.21; 2/2 | 8.94; 1/2 | — |
| Shape/palette reference fusion | 38.47; 2/2 | 8.79; 2/2 | 21.61; 2/2 |
| Robot identity in a new action | 68.49; 1/2 | 10.66; 1/2 | — |
| Alpha editing | 53.16; 2/2 | 13.22; 2/2 | — |
| Layer extraction/recomposition | 36.44; 2/2 | 20.88; 2/2 | — |
| 1500×600 banner with 60% clear area | 18.91; 0/2 | 9.23; 0/2 | — |
| Portrait infographic | 43.74; 2/2 | 11.77; 2/2 | — |

Across the eighteen-task standard sets, API medians were **41.655s Pro** and **11.7465s Flash**. Strict passes were 29/36 and 27/36. These aggregates combine different tasks and subjective requirements; a two-picture difference is not evidence of general model superiority.

For the **same four tasks** available in every mode, with eight requests per configuration, medians were **36.238s Pro standard, 24.7335s Pro fast and 12.3575s Flash**. Pro-fast's 8/8 rubric passes apply only to these tasks. Its eight-task-sample median must not be compared directly with the full eighteen-task sets.

### What failed despite HTTP success

- Flash kept large pink marker fill in both main marker samples. Pro cleaned the markers in both. The subsequent controlled fill/outline test below did not reproduce this failure in its new filled controls.
- All title replacements spelled 星野 correctly and removed NOVA. Both Pro replacements used lighter lettering than requested, causing partial font-weight grades rather than a text-spelling failure.
- Both Flash 3D icons were nearly frontal instead of clearly isometric. Both Pro hand-drawn samples partially missed the paper-feeding/one-leaf action; one also added glowing eyes. These are different instruction misses, not proof that either model cannot draw the style.
- All robot variants kept the five distinguishing identity cues, while one failed to depict a convincing watering action and another put the plant in the ground instead of a pot. Identity and action fidelity need separate checks.
- One book-page illustration added visible pseudo-print despite a no-text instruction. All four main banners allowed the product into the requested sixty-percent clear area; one added a hard white panel at the left.

## Controlled prompt comparisons

Each variant/model has two independent samples. Except for marker opacity, these compare recipe bundles or equivalent-language descriptions, not isolated causal effects of a single phrase.

| Question | Observation | Guidance justified by this sample |
|---|---|---|
| Minimal recolor vs coordinate + preservation recipe, 8 requests | All eight changed the cup correctly and retained the other objects. Mean outside-box RGB error was Pro 2.977/255 minimal vs 3.695 explicit; Flash 2.156 vs 2.139. | Simple unambiguous edits can be concise. Use coordinates and preservation clauses to express scope/ambiguity; do not promise lower pixel drift from longer wording. |
| Chinese vs English operations for a Chinese title, 8 requests | Both languages produced the exact 星野 and removed NOVA in all eight. Pro font-weight misses occurred in both languages. | Use the clearest operation language and quote exact payload. English is neither mandatory nor a cure for typography/style fidelity. |
| Concise infographic vs extended camera/CSS/position recipe, 8 requests | All eight had correct title/data, four-card order and translucent cards. Three Flash outputs had small dark titles over dark foliage. | Concise semantic instructions already produce this effect. Camera/CSS strings are optional style descriptions, not required renderer controls; inspect title contrast regardless of prompt length. |
| Marker alpha 80 vs outline alpha 0, 8 requests | **All eight were clean**, including both new Flash filled controls. Outline also worked in both models. | Preserve the original failures and the non-reproduction. Outline is a tested alternative, not demonstrated universally superior. Coordinates avoid injecting visible marks when they are unnecessary. |
| Original banner vs continuous-scene/right35% recipe, 8 requests | All eight were continuous photos with no hard white panel. The revised recipe moved the kettle farther right; Flash's two revised images visually met the clear-area criterion, Pro's two were close but still intruded slightly. | Specify continuous background, complete product footprint and no panels; strict pixel-safe areas still require layout inspection or deterministic composition. |

Banner placement grades are visual estimates. A color-component diagnostic sometimes selected window/background regions or missed a thin gooseneck; those diagnostic boxes were excluded from published measurements and were not treated as an object detector.

## Native outputs and geometry

All four alpha edits returned RGBA PNGs with real fully transparent pixels. Thresholded alpha-silhouette IoU against resized fixtures ranged **0.99585–0.99873**. This fixture result is not a promise about hair, glass or intricate real-object edges.

All four decompositions returned one base and two foregrounds: cup/handle/SUN together and NOVA separately. Other foliage/vase/table remained in the base. Every crop kept its native size and bbox/z-index metadata; resizing to the returned bbox gave RGB recomposition MAE **4.576–4.854/255** against the resized fixture. Shadows could occur in the extracted element and the base; edge/inpainting decisions still need inspection. This is generated reconstruction, not pixel-identical recovery.

## Changes incorporated into the skill

See [the measured prompt recipes](../references/benchmark-prompt-recipes.md). The prompt entry now states Pro's default policy, offers concise edits with explicit scope when needed, removes blanket English-only/Chinese-only operation claims, distinguishes successful spelling from font/layout fidelity, gives an optional outline-marker recipe with its mixed evidence, and adds a continuous-scene banner recipe without a pixel-exact guarantee. Historical camera/CSS/font conventions are scoped to their recipes instead of imposed as general API requirements.

## Cost and reproduction

Official [2026-10-25 pricing](https://www.volcengine.com/docs/ark/model-pricing), applied to actual output dimensions/counts and extra Pro references, estimates **CNY33.98**: main CNY23.18, prompt A/B CNY7.44, marker CNY1.68 and banner CNY1.68. This is not a verified account invoice. The user removed the monetary ceiling; sample expansion stopped after the registered questions had useful evidence.

From the skill directory, prepare without spending:

```bash
uv run evals/benchmark.py --suite comprehensive --out-dir /tmp/seedream-main
uv run evals/benchmark.py --suite prompt-ab --out-dir /tmp/seedream-prompts
uv run evals/benchmark.py --suite marker-ab --out-dir /tmp/seedream-markers
uv run evals/benchmark.py --suite banner-ab --out-dir /tmp/seedream-banners
```

Add `--execute --concurrency 6` only for an intentionally authorized new run. Reusing a directory skips every existing journal, including unknown outcomes. Fixture hashes are verified; existing evidence is never overwritten by preparation. Authentication uses the normal environment/calling-directory `.env`, outside the repository.

```bash
uv run evals/analyze_benchmark.py /tmp/seedream-main /tmp/seedream-prompts \
  /tmp/seedream-markers /tmp/seedream-banners --export /tmp/public-results.json
```

The analyzer creates geometry metrics and anonymous sheets. Human/agent rubric entries are a separate `reviewed-results.json`; export preserves missing reviews rather than inventing scores. Reproduce the portable synthetic references and task definitions from [the suite](comprehensive_suite.py). Images/private journals stay outside Git; the tracked result stores explicit request fields, prompt/fixture/image hashes, native layer metadata and per-sample judgments without credentials, input data URLs, expiring output URLs or personal paths.
