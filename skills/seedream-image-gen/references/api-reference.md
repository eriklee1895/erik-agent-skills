# Seedream 5.5 Images API contract

Checked **2026-11-14** against the official [5.5 tutorial](https://console.volcengine.com/ark/region:cn-beijing/docs/seedream-5-5), [Images API](https://console.volcengine.com/ark/region:cn-beijing/docs/image-generation-api), [general tutorial](https://console.volcengine.com/ark/region:cn-beijing/docs/image-generation-tutorial), [streaming events](https://console.volcengine.com/ark/region:cn-beijing/docs/image-generation-streaming-responses), [error codes](https://console.volcengine.com/ark/region:cn-beijing/docs/error-codes), [legacy editing guide](https://console.volcengine.com/ark/region:cn-beijing/docs/seedream-5-0-pro-editing-guide), [legacy tutorial](https://console.volcengine.com/ark/region:cn-beijing/docs/seedream-5-0-pro), [model list](https://console.volcengine.com/ark/region:cn-beijing/docs/model-list) and [pricing](https://www.volcengine.com/docs/ark/model-pricing). A second live pass on 2026-11-14 re-verified the field behavior below with direct API probes (field/error/boundary matrix) and paid CLI capability calls (edit chains, transparency, decomposition, outpaint) against `doubao-seedream-5-5-261028`. Account limits and pricing can change.

## Endpoint and model

`POST https://ark.cn-beijing.volces.com/api/v3/images/generations`, bearer `ARK_API_KEY`. Generation, editing and decomposition use the same endpoint. Default model: **`doubao-seedream-5-5-261028`**. There is no new `/edit` or `/layers` endpoint in the Ark contract. Third-party wrappers may expose their own endpoints and fields.

The CLI accepts only this 5.5 ID and its listed aliases. Other IDs and aliases are rejected before submission; custom endpoints and older models are outside this skill. The platform still serves the legacy `doubao-seedream-5-0-pro-260628` ID when called directly: a saved live probe returned HTTP 200 with the response `model` field echoing that legacy id and a 1024×1024 image, which is exactly why the CLI's client-side guard exists. A fabricated id such as `doubao-seedream-9-9-fake-999999` was probed the same way and returned 404 `InvalidEndpointOrModel.NotFound` ("The model or endpoint … does not exist or you do not have access to it"), matching the platform error-codes table.

## Request fields

| Field | Seedream 5.5 contract |
|---|---|
| `model` | Dated 5.5 ID above; aliases resolve locally. |
| `prompt` | Required for generation/editing; optional for decomposition. Chinese/English plus 14 more documented languages (Russian, Arabic, Filipino, Thai, Turkish, Korean, Malay, Spanish, Portuguese, Indonesian, French, German, Vietnamese, Japanese). Official length guidance: about 300 Chinese characters or 600 English words; over-long prompts drop elements. |
| `image` | URL/data URL string or array. Up to ten references for generation, including RGBA output; exactly one for decomposition. Data URL MIME suffix must be lowercase. |
| `size` | Generation: 1K/1.5K/2K or WxH, default 2K. Layers: auto/1K/1.5K/2K, default auto. |
| `background` | auto (API default), transparent or opaque. Transparent supports text-only, RGB or alpha inputs, up to ten references. CLI default remains opaque. Omit this field for decomposition — sending it with `layer_decomposition` returns 400. |
| `output_format` | png (API default for 5.5) or jpeg. Transparent requires png; jpeg + transparent returns 400. In layer mode it controls the base only; foregrounds always PNG. `webp` and other formats return 400. |
| `layer_decomposition` | Existing boolean, false by default. Up to one base + 99 layers. |
| `layer_decomposition_options` | Valid with layer_decomposition true. |
| `…max_images` | Integer 2–100, default 30, includes base. Upper bound; not exact output count. CLI `--max-images`. Values outside 2–100 return 400. |
| `…text_recognition` | Boolean, default false. Rich-text OCR for eligible regular text layers. CLI `--text-recognition`. |
| `optimize_prompt_options.mode` | standard only. `fast` is unsupported and returns 400 "must be standard for Seedream 5.5". |
| `response_format` | url (default, valid 24h) or b64_json. CLI downloads URLs immediately; decoder also accepts base64. Live-verified on both ordinary generation and decomposition: every base/layer item returns inline `b64_json` with the same z-index, bbox and OCR structure as URL mode. |
| `watermark` | API default true; CLI explicitly sends false unless requested. |
| `safety_identifier` | Optional end-user compliance id: single ASCII token, max 64 chars, fixed and unique per user (hash the user id/email; never raw PII). Echoed back at the top level when set. The CLI exposes it as `--safety-identifier` (per-job override in batch JSONL) and deliberately does not persist it in local metadata. |

5.5 returns one image per ordinary request and does **not** support `sequential_image_generation`, tools/web search or streaming; sending those fields returns 400 `InvalidParameter` (live-verified for `sequential_image_generation`, `tools` and `stream` — the last with "stream is not supported by the current model"). They belong to 5.0 lite / 4.5 / 4.0. The existence of a general SSE event reference does not enable streaming on 5.5. CLI `--n` and JSONL batches issue independent requests; they do not send an API `n` field. Do not invent `seed`, `mask`, `bbox`, `num_images`, ControlNet or font-file upload fields. Spatial tags belong inside the prompt.

Live probes also show the server **silently ignores unrecognized or inapplicable fields** — `n`, `seed`, `mask` and a bogus `xyz_unknown_field` each returned HTTP 200 with one ordinary image and no error. Ignored fields give no effect and no warning, so the CLI's strict client-side allowlist is the guardrail; never rely on an unknown field reaching the model. `safety_identifier` length is enforced server-side (65 characters returns 400 "must contain at most 64 characters"), while whitespace inside the token is accepted; the CLI applies a stricter local ASCII/no-whitespace policy regardless, since the documented contract asks for an English string hash rather than a display value.

## Native size and input constraints

Generation: **921,600–4,624,220 total pixels**, aspect 1/16..16. These bounds apply to W×H, not each side. `1K` / `1.5K` / `2K` are resolution tiers with prompt-dependent aspect. No native 3K/4K tier is documented; a live `size: "3K"` probe returns 400. A platform's “4K” export may be an additional resize, not this API's native output.

Common tier pixel mappings from the API reference (illustrative, not exhaustive — the model may return other dimensions):

| Tier | 1:1 | 4:3 / 3:4 | 16:9 / 9:16 | 3:2 / 2:3 | 21:9 |
|---|---|---|---|---|---|
| 1K | 1024×1024 | 1152×864 / 864×1152 | 1424×800 / 800×1424 | 1248×832 / 832×1248 | 1568×672 |
| 1.5K | 1536×1536 | 1792×1344 / 1344×1792 | 2048×1152 / 1152×2048 | 1872×1248 / 1248×1872 | 2352×1008 |
| 2K | 2048×2048 | 2368×1776 / 1776×2368 | 2816×1584 / 1584×2816 | 2496×1664 / 1664×2496 | 3136×1344 |

Live probes confirmed the exact error wording at both boundaries: below the floor returns "image area must be at least 921600 pixels"; above the cap returns "image area must be at most 4624220 pixels".

The CLI accepts exact small destinations by generating at the smallest valid approximately matching aspect, then LANCZOS-downscaling. Example 1500×600 → API 1520×608 → final 1500×600. `--no-auto-upscale` rejects below-floor sizes. Above-cap/invalid-aspect targets fail locally.

Generation references: jpeg/png/webp/bmp/tiff/gif/heic/heif, ≤30 MB and ≤36M pixels each, sides >14 px, aspect at most 16:1. Decomposition: one PNG/JPEG, 262,144–36M pixels and ≤30 MB. Local files become MIME data URLs; remote references must be reachable by the server. Some constraints remain server-validated.

Layer `auto` and fixed tiers can output a base at different dimensions from the source and enlarged individual crops. With `auto`, the documented rule keeps the source size inside the native range, clamps below-floor sources to 1K and above-cap sources to 2K, and preserves the source aspect. Do not assume source, base, bbox and crop sizes are interchangeable.

## Response additions

`data[]` contains downloadable `url` / `b64_json`, `size`, `output_format` and actual `background` (`opaque` / `transparent`). Actual background may differ from a request using auto; normal CLI metadata preserves it as `reported_background` when supplied.

In decomposition mode, `data[]` also carries `z_index`, `bounding_box`, `name`, `description` and optional **`text_recognition`**. The CLI preserves these fields in `layers.json` along with request options.

- z-index 0 is the base; ascending indices define composition order.
- `bounding_box.absolute`: [left, top, right, bottom] in **output-base pixels**. Resize each PNG crop to the bbox dimensions, then place it.
- `bounding_box.normalized`: matching bounds in 0–1000. Edit prompt coordinates instead use 0–999.
- OCR: `text`, `lines[].bounding_box`, `lines[].runs[].text` and `runs[].style` with `similar_font_family`, `foreground_color`, `bold`, `italic`, `underline`, `strikethrough`, `shadow`, `translucent`.
- OCR is limited to regular text; font matches are approximate and may be unknown. It does not return exact font files, font size or PSD text objects. See [OCR structure and reconstruction](transparent-layers.md).

Top-level response fields: `created` (unix seconds), `model` (the id that actually served the request), `usage`, and the echoed `safety_identifier` when one was sent. `usage.generated_images` counts successful outputs; `usage.input_images` counts references. `usage.output_tokens` is `sum(width × height) / 256` rounded, and `total_tokens` currently equals it because input tokens are not counted.

## Rate limits and retries

The [model list](https://console.volcengine.com/ark/region:cn-beijing/docs/model-list) documents a non-rigid **500 IPM (images/minute)** maximum for Seedream 5.5, subject to platform load and call pattern; limits are account-wide per model version and are not self-service adjustable (endpoint `ep-*` limits can differ). IPM is provisionally reserved using max_images for decomposition (default 30), with unused quota released after the actual output count is known — this is quota accounting, not monetary billing.

Documented 429 codes include `ModelAccountIpmRateLimitExceeded`, `ModelAccountRpmRateLimitExceeded`, `ServerOverloaded` (capacity, common on cold endpoints) and `RequestBurstTooFast` (burst protection on seed-2.0 and later; ramp growth gradually). A burst-queue header `X-Ark-Max-Wait-Timeout-Ms` (suggested 60000–600000) lets the server queue instead of rejecting. Account limits can be queried via the `ListModelRateLimit` API (AK/SK HMAC auth).

## Outpainting

`edit --outpaint direction:pixels` creates a padded opaque canvas locally and asks the model to extend it. It is a CLI convention, not an API field, and cannot use transparent-edit mode. When no size is explicitly chosen, the CLI sends an explicit WxH size matching the padded canvas whenever its pixels fit the native contract (verified live: a 1024×1024 source plus 200 px returns an exact 1224×1024 image). An explicit `--size` or size shortcut is always respected instead. When the padded canvas falls below 921,600 pixels, exceeds 4,624,220 pixels, or breaches aspect 16:1, the CLI keeps the requested tier size and prints a warning: the output then follows that tier's dimensions rather than the padded canvas, so the extension is rescaled. Center pixels can change; inspect the result.

## Failure handling

| Outcome | Action |
|---|---|
| 400/401/403 | Fix parameters/auth/access; no retry loop. Live 400s include unsupported modes/formats/enums and out-of-range sizes, each naming the offending `param` in an undocumented `error.param` envelope field. |
| 400 content/URL families | `InvalidImageURL.EmptyURL` / `InvalidImageURL.InvalidFormat` for bad data URLs; `InputImageSensitiveContentDetected` (with `.PolicyViolation` / `.PrivacyInformation`) and `OutputImageSensitiveContentDetected` (with `.DeepFake` for counterfeit documents) for moderation blocks. |
| 401 / 403 / 404 | `AuthenticationError` for bad keys; `OperationDenied.ServiceNotOpen` / `AccountOverdueError` for access problems; `ModelNotOpen` and `InvalidEndpointOrModel.NotFound` for unactivated or unknown model ids. |
| Explicit 429/5xx | Bounded backoff, respecting numeric retry-after. 500 `InternalServiceError`/`ModelLoading` and 503 `NoAvailableService` follow the same retry rule. |
| Timeout/transport outcome unknown | Stop with OutcomeUnknown; do not automatically replay a possibly billed submission. Community evidence: a client disconnect after generation starts can still be billed because the synchronous API has no task id. |
| Download failure after success | Retry the download only; never regenerate automatically. |
| Missing asset, per-item error or invalid layer indices | Report failure, preserving available evidence; do not claim an empty success. |

Any server-side layer-generation failure fails the whole decomposition request. Output download/validation failures are separate. Immediately download assets because signed URLs expire (24 h); do not save credentials, inline image payloads or expiring response URLs in manifests.

### Behaviors with no official answer

Treat these as open rather than implied by the docs: the exact prompt/format rules by which `background: auto` chooses alpha (jpeg is always opaque); cross-retry grouping variance beyond the measured fact that identical requests return different groupings and names; and element dropping beyond the 300-character/600-word prompt guidance. Live verification has closed two earlier questions: per-layer `b64_json` is supported in decomposition, and a prompt naming more elements than `max_images` allows returns 200 with silent merging/dropping (a 12-element prompt with cap 6 returned six outputs and no error). Re-verify anything else on the live API before depending on it.

### Regional sibling

The overseas BytePlus ModelArk service uses a separate contract — endpoint `https://ark.ap-southeast.bytepluses.com/api/v3` and model id `dola-seedream-5-5-261028`, with separate entitlement and moderation. This skill covers only the cn-beijing Ark id `doubao-seedream-5-5-261028`; do not mix ids, keys or rate-limit assumptions across regions.

## Public list price snapshot (CNY)

| Model / task | Input image | Each output image |
|---|---|---|
| **5.5, generation or decomposition** | **0.05 each, including first** | **≤2.61M pixels: 0.13; >2.61M through native cap: 0.23** |

Snapshot from official pricing, not an account bill. Total = sum input charges + sum actual output-tier charges. 1.5K normally shares the ≤2.61M tier with 1K, so when a preset fits the brief, prefer 1.5K over 1K at equal list price. Each layer can have its own size/tier; do not calculate all layers using the base's dimensions. A 5.5 two-reference 1K generation is list-estimated 0.23 (0.10 + 0.13), not 0.13. Pricing comparisons should include inputs and distinguish generation from decomposition. Failed outputs are not billed according to the pricing page; text tokens carry no separate image charge.
