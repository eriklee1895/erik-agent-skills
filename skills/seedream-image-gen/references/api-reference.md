# Seedream 5.5 Images API contract

Checked **2026-11-14** against the official [5.5 tutorial](https://console.volcengine.com/ark/region:cn-beijing/docs/seedream-5-5), [Images API](https://console.volcengine.com/ark/region:cn-beijing/docs/image-generation-api), [general tutorial](https://console.volcengine.com/ark/region:cn-beijing/docs/image-generation-tutorial), [streaming events](https://console.volcengine.com/ark/region:cn-beijing/docs/image-generation-streaming-responses), [legacy editing guide](https://console.volcengine.com/ark/region:cn-beijing/docs/seedream-5-0-pro-editing-guide), [legacy tutorial](https://console.volcengine.com/ark/region:cn-beijing/docs/seedream-5-0-pro) and [pricing](https://www.volcengine.com/docs/ark/model-pricing). Account limits and pricing can change.

## Endpoint and model

`POST https://ark.cn-beijing.volces.com/api/v3/images/generations`, bearer `ARK_API_KEY`. Generation, editing and decomposition use the same endpoint. Default model: **`doubao-seedream-5-5-261028`**. There is no new `/edit` or `/layers` endpoint in the Ark contract. Third-party wrappers may expose their own endpoints and fields.

The CLI accepts only this 5.5 ID and its listed aliases. Other IDs and aliases are rejected before submission; custom endpoints and older models are outside this skill.

## Request fields

| Field | Seedream 5.5 contract |
|---|---|
| `model` | Dated 5.5 ID above; aliases resolve locally. |
| `prompt` | Required for generation/editing; optional for decomposition. |
| `image` | URL/data URL string or array. Up to ten references for generation, including RGBA output; exactly one for decomposition. |
| `size` | Generation: 1K/1.5K/2K or WxH, default 2K. Layers: auto/1K/1.5K/2K, default auto. |
| `background` | auto (API default), transparent or opaque. Transparent supports text-only, RGB or alpha inputs, up to ten references. CLI default remains opaque. Omit this field for decomposition. |
| `output_format` | png (API default) or jpeg. Transparent requires png. In layer mode it controls the base only; foregrounds always PNG. |
| `layer_decomposition` | Existing boolean, false by default. Up to one base + 99 layers. |
| `layer_decomposition_options` | Valid with layer_decomposition true. |
| `…max_images` | Integer 2–100, default 30, includes base. Upper bound; not exact output count. CLI `--max-images`. |
| `…text_recognition` | Boolean, default false. Rich-text OCR for eligible regular text layers. CLI `--text-recognition`. |
| `optimize_prompt_options.mode` | standard only. `fast` is unsupported. |
| `response_format` | url (default, valid 24h) or b64_json. CLI downloads URLs immediately; decoder also accepts base64. |
| `watermark` | API default true; CLI explicitly sends false unless requested. |

5.5 returns one image per ordinary request and does **not** support `sequential_image_generation`, tools/web search or streaming. The existence of a general SSE event reference does not enable streaming on 5.5. CLI `--n` and JSONL batches issue independent requests; they do not send an API `n` field. Do not invent `seed`, `mask`, `bbox`, `num_images`, ControlNet or font-file upload fields. Spatial tags belong inside the prompt.

## Native size and input constraints

Generation: **921,600–4,624,220 total pixels**, aspect 1/16..16. These bounds apply to W×H, not each side. `1K` / `1.5K` / `2K` are resolution tiers with prompt-dependent aspect. No native 3K/4K tier is documented. A platform's “4K” export may be an additional resize, not this API's native output.

The CLI accepts exact small destinations by generating at the smallest valid approximately matching aspect, then LANCZOS-downscaling. Example 1500×600 → API 1520×608 → final 1500×600. `--no-auto-upscale` rejects below-floor sizes. Above-cap/invalid-aspect targets fail locally.

Generation references: jpeg/png/webp/bmp/tiff/gif/heic/heif, ≤30 MB and ≤36M pixels each, sides >14 px, aspect at most 16:1. Decomposition: one PNG/JPEG, 262,144–36M pixels and ≤30 MB. Local files become MIME data URLs; remote references must be reachable by the server. Some constraints remain server-validated.

Layer `auto` and fixed tiers can output a base at different dimensions from the source and enlarged individual crops. Do not assume source, base, bbox and crop sizes are interchangeable.

## Response additions

`data[]` contains downloadable `url` / `b64_json`, `size`, `output_format` and actual `background` (`opaque` / `transparent`). Actual background may differ from a request using auto; normal CLI metadata preserves it as `reported_background` when supplied.

In decomposition mode, `data[]` also carries `z_index`, `bounding_box`, `name`, `description` and optional **`text_recognition`**. The CLI preserves these fields in `layers.json` along with request options.

- z-index 0 is the base; ascending indices define composition order.
- `bounding_box.absolute`: [left, top, right, bottom] in **output-base pixels**. Resize each PNG crop to the bbox dimensions, then place it.
- `bounding_box.normalized`: matching bounds in 0–1000. Edit prompt coordinates instead use 0–999.
- OCR: `text`, `lines[].bounding_box`, `lines[].runs[].text` and `runs[].style` with `similar_font_family`, `foreground_color`, `bold`, `italic`, `underline`, `strikethrough`, `shadow`, `translucent`.
- OCR is limited to regular text; font matches are approximate and may be unknown. It does not return exact font files, font size or PSD text objects. See [OCR structure and reconstruction](transparent-layers.md).

`usage.generated_images` counts outputs; `input_images` counts references. Layer billing depends on the actual outputs and their individual pixel tiers. IPM is provisionally reserved using max_images (default 30 for 5.5), with unused quota released. This is not evidence that the same number of images is monetarily charged or that a client should hardcode a rate limit.

## Outpainting

`edit --outpaint direction:pixels` creates a padded opaque canvas locally and asks the model to extend it. It is a CLI convention, not an API field. It cannot use the current CLI's transparent-edit mode. Center pixels can change; inspect the result.

## Failure handling

| Outcome | Action |
|---|---|
| 400/401/403 | Fix parameters/auth/access; no retry loop. |
| Explicit 429/5xx | Bounded backoff, respecting numeric retry-after. |
| Timeout/transport outcome unknown | Stop with OutcomeUnknown; do not automatically replay a possibly billed submission. |
| Download failure after success | Retry the download only; never regenerate automatically. |
| Missing asset, per-item error or invalid layer indices | Report failure, preserving available evidence; do not claim an empty success. |

Any server-side layer-generation failure fails the whole decomposition request. Output download/validation failures are separate. Immediately download assets because signed URLs expire; do not save credentials, inline image payloads or expiring response URLs in manifests.

## Public list price snapshot (CNY)

| Model / task | Input image | Each output image |
|---|---|---|
| **5.5, generation or decomposition** | **0.05 each, including first** | **≤2.61M pixels: 0.13; >2.61M through native cap: 0.23** |

Snapshot from official pricing, not an account bill. Total = sum input charges + sum actual output-tier charges. 1.5K normally shares the ≤2.61M tier. Each layer can have its own size/tier; do not calculate all layers using the base's dimensions. A 5.5 two-reference 1K generation is list-estimated 0.23 (0.10 + 0.13), not 0.13. Pricing comparisons should include inputs and distinguish generation from decomposition. Failed outputs are not billed according to the pricing page.
