# GPT Image 2.5 Image API reference

This reference describes the contract implemented by `scripts/gpt_image_api.py`. OpenAI's API reference is authoritative when it changes.

## Endpoints

- Generation: `POST /v1/images/generations` → `client.images.generate(...)`
- Edit: `POST /v1/images/edits` → `client.images.edit(...)`

Always send an explicit model. The CLI supports only the Flare and Sunburst aliases and their `2026-09-08` snapshots.

Custom credentials are an atomic pair: `CUSTOM_OPENAI_API_KEY` is accepted only with `CUSTOM_OPENAI_BASE_URL`, and vice versa. This prevents a standard OpenAI credential from being sent to a custom host. Without that pair, the CLI uses `OPENAI_API_KEY` and optional `OPENAI_BASE_URL`.

## Shared request fields

| Field | Values | Local default |
| --- | --- | --- |
| `prompt` | Non-empty string, at most 32,000 characters | Required |
| `model` | Current Flare/Sunburst alias or snapshot | Flare alias |
| `n` | 1–10 variants of the same prompt | 1 |
| `size` | `auto`, preset, or valid `WIDTHxHEIGHT` | `auto` |
| `quality` | `auto`, `low`, `medium`, `high`, `xhigh`, `max` | `auto` |
| `background` | `auto`, `opaque`, `transparent` | `auto` |
| `output_format` | `png`, `jpeg`, `webp` | `png` |
| `output_compression` | 0–100 for JPEG/WebP only | Omitted |
| `moderation` | `auto`, `low`; generation endpoint only | `auto` |

GPT Image responses contain base64-encoded image bytes in the requested format. The CLI does not send `response_format`; URL responses are not supported for these models.

## Dimensions

Custom dimensions must satisfy all conditions:

- width and height are multiples of 16;
- long:short ratio is at most 3:1;
- each edge is at most 3,840 pixels;
- total pixels are 655,360–8,294,400;
- outputs above 2,560×1,440 total pixels are experimental.

Presets: `square`, `landscape`, `portrait`, `wide`, `2k-square`, `2k-landscape`, `4k-landscape`, `4k-portrait`, and `auto`.

## Edit inputs and masks

- Supply 1–16 PNG, JPEG, or WebP images, each smaller than 50MB.
- Input order is significant. Number and role-label images in the prompt.
- A mask must be PNG, smaller than 4MB, contain alpha, and match the first image's dimensions.
- Fully transparent mask pixels indicate the region to edit.
- A mask guides the model; it is not a pixel-hard compositing boundary.

The SDK exposes a generic `input_fidelity` field, while current model-specific guidance and examples do not establish a clear GPT Image 2.5 contract for it. This CLI intentionally omits the field until a model-specific live contract test resolves that discrepancy.

## Transparency

Use `background="transparent"` with PNG or WebP. Ask for an isolated subject or transparent canvas in the prompt as well. Preserve the decoded alpha channel; a painted checkerboard is not transparency. The CLI checks that the result contains an alpha channel with at least one transparent pixel.

## Streaming

Use `--stream --partial-images 0..3`. The Image API guide and endpoint schemas document partial image SSE events for generation and editing. Each requested partial adds output-token cost, and the final image can arrive before every requested partial.

The model pages' generic feature matrix says streaming is unsupported, but a live Flare Image API contract check on 2026-09-13 accepted streaming and returned a completed event. A requested partial may still be absent when the final image finishes first. Treat partial-image streaming as an endpoint capability and keep it opt-in. The CLI supports one final image (`n=1`) per streaming invocation and does not retry after event iteration has begun.

Event types:

- `image_generation.partial_image`
- `image_generation.completed`
- `image_edit.partial_image`
- `image_edit.completed`

## Output and metadata

Without `--force`, the CLI preflights final images, partials, downscaled copies, and sibling metadata before the API call. Final metadata records request settings, response settings, complete usage when returned, request ID when available, elapsed time, attempts, inputs, roles, and mask.

## Errors and retries

Retry with bounded exponential backoff for connection failures, timeouts, HTTP 408/409/429, and 5xx responses. Do not automatically retry authentication, quota, moderation, or user-correctable request errors.

Use `error.code` as the stable discriminator when available. `moderation_blocked` can include `moderation_stage` (`input`, `output`, `unknown`) and coarse categories. Keep end-user messages generic; use details for developer diagnostics.
