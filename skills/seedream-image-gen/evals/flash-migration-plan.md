# Seedream Pro / Flash migration and benchmark plan

## Outcome and scope

Retire Lite from the published skill and support `doubao-seedream-5-0-flash-260915` alongside the default `doubao-seedream-5-0-pro-260628`. Keep one Images API request/download path. Preserve dry-run metadata protection, exact-size downscaling, optional concurrency and explicit 429/5xx backoff; add no fixed IPM scheduler.

Reject retired Lite IDs/aliases with a migration message rather than rerouting paid calls. Remove the Lite-only web-search/sequential CLI paths. Keep historical Pro observations labeled as such; do not transfer Lite claims or Pro quality scores to Flash.

## Sources checked on 2026-10-24

- [Pro / Flash tutorial](https://www.volcengine.com/docs/ark/seedream-5-0-pro)
- [Interactive editing guide](https://www.volcengine.com/docs/ark/seedream-5-0-pro-editing-guide)
- [Generation tutorial and model matrix](https://www.volcengine.com/docs/ark/seedream-4-0-5-0)
- [Prompt guide](https://www.volcengine.com/docs/ark/seedream-4-0-5-0-prompt-guide) — its older model-specific claims are not Flash evidence; only general writing principles transfer.
- [Images API](https://www.volcengine.com/docs/ark/image-generation-api)
- [Pricing](https://www.volcengine.com/docs/ark/model-pricing)

The console links supplied by the user point to these same documents. Full captures stay outside Git. Native generation supports 1K/1.5K/2K, 921,600–4,624,220 pixels and up to ten references for both models. Pro supports standard/fast; Flash supports standard. Ordinary generation produces one image per request.

`background=transparent` is an image-to-image operation: exactly one alpha-bearing input and PNG output. `layer_decomposition=true` is a distinct mode on the same endpoint: one PNG/JPEG input, optional prompt, size auto/1K/1.5K/2K; one base and up to sixteen PNG layers. Each layer includes z-index, bbox, name and description. Edit prompt coordinates use 0–999; returned normalized layer boxes use 0–1000. No invented mask/bbox/layers JSON request fields.

## Implementation sequence

1. Add offline failing contracts for Flash resolution/aliases, retired Lite rejection, Pro-fast/Flash-standard validation, transparent-input restrictions, and multi-output layer saving.
2. Update the capability table and common request builder. Preserve legacy Pro negative-prompt behavior as undocumented; do not claim undocumented Flash support. Explicit content guards may use natural-language prompt clauses when a model has no documented negative field.
3. Add `--background opaque|transparent` to generation/edit/batch and `decompose` for layer extraction. Decode each returned image into a structured record through the existing HTTP path. Save each output in its returned format and native dimensions, plus `layers.json`; never resize every cropped layer to one canvas size or persist signed URLs.
4. Ensure paid generation is not repeated after a download failure; downloads retain their own retry. Requests whose submission outcome is unknown stop explicitly instead of being blindly replayed.
5. Run regression tests, then a bounded real benchmark. Inspect actual outputs and use the results to revise model-routing and prompt guidance.
6. Replace obsolete Lite guidance, correct API/alpha/layer claims, update bilingual catalog descriptions, and run independent review before opening a PR. No merge without a further user instruction.

## First-hand benchmark

At most **16 intentional generation requests**, no automatic reruns of unknown/possibly-sent paid calls. The maximum layer count makes the output-image count larger than the request count; a layer prompt requests two selected elements, but is not treated as a hard server output cap. Public-list-price estimate is below approximately CNY 15 even with conservative layer counts; actual billed amounts remain account-dependent.

| Case | Controlled task | Configurations | Requests |
| --- | --- | --- | --- |
| typography | Chinese headline and three short labels, 2K | Pro standard, Pro fast, Flash standard | 3 |
| small-banner | product banner, final 1500×600 | same three | 3 |
| coordinate-edit | recolor one fixture object using a normalized bbox; keep the other object | same three | 3 |
| multi-reference | retain object shape from image 1 and palette from image 2 | same three | 3 |
| alpha-edit | recolor an alpha PNG, keep transparency | Pro standard, Flash standard | 2 |
| decompose | extract the named object and title from a fixture, 1.5K | Pro standard, Flash standard | 2 |

Use fixed synthetic references and prompts, deterministic case/config IDs, shuffled configuration order and fixed benchmark concurrency. Record API and end-to-end latency, success/failure/unknown outcomes, actual image counts, pixel sizes, encoding, alpha measurements and usage counts. Save images and private execution evidence outside Git; track only portable recipes, source links and a redacted summary.

Quality inspection: exact Chinese text, requested composition, edit target selection and outside-area drift, multi-reference adherence, transparent pixels, layer metadata and recomposition. Four different core tasks per configuration are a small sample, not a latency SLA or a general model ranking; report failures and uncertainty rather than hiding them in averages.

## Acceptance

- Both models use the same endpoint and documented common fields; only supported optimize modes are sent.
- Lite no longer appears as a selectable or recommended model. Historical facts are not silently renamed to Flash.
- Transparent and decomposition misuse fail before an API call when local inputs allow validation.
- Layer output format, cropped dimensions, z-index and both bbox forms survive download/save; returned signed URLs do not.
- Existing fifteen regressions are preserved or migrated meaningfully. New contracts, dry-runs, real sample outputs and skill validation pass.
- Benchmark evidence and guidance distinguish official capabilities, observed behavior and untested claims.
