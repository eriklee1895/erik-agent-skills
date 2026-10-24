# Pro / Flash first-hand benchmark — 2026-10-24

**16 intentional API requests, all successful; 20 output images.** This checks the new integration and provides small-sample workflow guidance. It is not a general image-quality leaderboard or a latency SLA.

## Method

Requests used the official Beijing Ark Images endpoint and the requested dated Pro/Flash model IDs. Four core tasks were run once each under Pro standard, Pro fast and Flash standard. Two additional paired tasks checked alpha editing and decomposition. References are fixed synthetic fixtures; prompts, fixture hashes, actual request fields, image hashes, dimensions, alpha measurements and timings are in [the redacted results](flash-benchmark-results.json). The [runner](benchmark.py) recreates the fixture/manifest and requires `--execute` for paid calls.

Benchmark concurrency was two. Every case has a durable pre-send journal; existing cases are never automatically resubmitted. Generation was attempted once per case; downloads retain their separate retry. Pro's undocumented quality-negative default was disabled to keep core prompts comparable. No IPM-based scheduler, automatic model fallback, or provider `seed` parameter was used.

Only the first two cases ran in the initial smoke pair. The remaining invocation skipped them and completed the other fourteen. There were no failed/unknown requests to exclude from the timing table.

## Latency

API time measures request/response time; end-to-end also includes local validation, download, resizing and saving. Each table cell is **one observation**, not a mean over repeated identical requests.

| Task | Pro standard | Pro fast | Flash standard |
|---|---:|---:|---:|
| Chinese typography, 2K | 78.28 s | 125.08 s | 16.48 s |
| Product banner, final 1500×600 | 25.99 s | 13.17 s | 8.76 s |
| Coordinate edit, 1.5K | 26.00 s | 26.61 s | 8.65 s |
| Two-reference fusion, 1.5K | 67.35 s | 24.76 s | 11.28 s |
| **Core median, n=4 distinct tasks** | **46.67 s** | **25.69 s** | **10.02 s** |
| Alpha-image edit, 1.5K | 61.48 s | not tested | 13.15 s |
| Decomposition, 1.5K | 48.46 s | not tested | 21.89 s |

Core end-to-end medians were 47.14 s, 26.22 s and 10.54 s respectively. Flash was faster in each matched core observation here. `fast` is not a per-request speed guarantee: Pro fast was slower on the text case and essentially tied/slower on coordinate editing. The sample is too small to attribute those variations to a model property, queueing or other service effects.

## Output inspection

- **Chinese text:** all three outputs visibly contain the correct headline “新绿计划”, subtitle and three short labels. The Pro-fast sample repeats the three labels in both headers and footers, adding text beyond the requested layout. Short-label success does not establish dense-table or long-body-text reliability.
- **Product banner:** all final files are exactly 1500×600, after native generation at 1520×608. Each follows the teal product/right-side composition with open space and no visible text/people. The Pro-fast sample interprets the product as a dripper/carafe variant; object design still needs review.
- **Coordinate edit:** all three recolor the selected red cup to blue while retaining the NOVA title and right-hand object. Mean absolute RGB error outside the selected box, versus the resized synthetic reference, was 3.115/255 (Pro standard), 3.779/255 (Pro fast), 2.614/255 (Flash). This describes one fixture and does not imply a hard pixel mask or a general quality ranking.
- **Multi-reference fusion:** all three retain a recognizable cup from image 1 and apply the teal/cream palette from image 2, without the other fixture object or title. Fine material/identity consistency in complex photos was not tested.
- **Alpha editing:** both outputs are actual RGBA PNGs at 1536×1536, with alpha extrema 0–255. Fully transparent pixels occupy 68.472% (Pro) and 68.464% (Flash). Visual inspection confirms orange recoloring and retention of the cup/handle silhouette. Checkerboards in inspection sheets are a local visualization, not baked into the generated files.
- **Native layers:** each response returns one RGB PNG base plus two RGBA PNG foregrounds: the selected cup and NOVA title. The base retains the other object. z-index, names and both bbox forms survive saving. Foreground sizes differ from the base and from their display boxes; using each returned absolute bbox reconstructs a visually close result. RGB MAE versus the resized input was 3.589/255 (Pro) and 4.403/255 (Flash), so reconstruction is not pixel-identical recovery.

Example crop/display distinction: Flash's cup PNG is 1165×998, while its returned output-base box is `[194,600,828,1142]`, a 634×542 display region. Placing the crop without resizing it to that box would be wrong.

## Guidance incorporated into the skill

1. Flash is a practical low-latency/cost option for these short-text, product, coordinate, reference and layer workflows; do not import the old Lite text/marker limitations into it.
2. Keep Pro as the existing default and use actual final-art requirements to choose. Neither a model name nor four examples establishes universal quality superiority.
3. Expose Pro fast explicitly, validate Flash standard-only, and avoid promising that fast is always faster.
4. Use 1.5K as a useful intermediate tier; use 2K for demanding text/detail and exact WxH for delivery pixels.
5. Treat transparent editing and decomposition as documented API operations with their own input constraints, not as text-only transparency or a generic multi-image generation mode.
6. Preserve native crop sizes, encodings and position metadata; reconstruct against the returned base, not blindly against the input image.

## Cost and reproducibility

Applying the official [2026-10-24 public prices](https://www.volcengine.com/docs/ark/model-pricing) to these twenty outputs and extra Pro reference inputs gives an estimate of **CNY4.75**. This is a list-price calculation, not a verified account invoice. Flash is CNY0.12/output; Pro normal and layer outputs use different tiers. Every decomposition layer contributes an output charge.

Prepare without calling the API:

```bash
uv run evals/benchmark.py --out-dir /tmp/seedream-study
```

Execute only when intentionally authorized to spend on the manifest cases:

```bash
uv run evals/benchmark.py --out-dir /tmp/seedream-study --execute --concurrency 2
```

Use a new directory for a new intentional run. Reusing this directory skips existing journals, including unknown outcomes; it is not a retry command. Set ARK_API_KEY in the environment or the calling directory's .env. Generated images/private execution files stay outside Git; the tracked summary contains portable synthetic prompts, hashes and measurements, not credentials, expiring URLs, account identifiers or machine-local paths.
