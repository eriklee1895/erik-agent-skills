# GPT Image 2.6 Image API reference

This reference describes the contract implemented by `scripts/gpt_image_api.py`. OpenAI's API reference is authoritative when it changes.

## Endpoints

- Generation: `POST /v1/images/generations` → `client.images.generate(...)`
- Edit: `POST /v1/images/edits` → `client.images.edit(...)`

Always send an explicit model. Use `gpt-image-2.6-flare` or `gpt-image-2.6-sunburst`, or the CLI shorthands `flare` and `sunburst`.

## Provider model names

The CLI uses the OpenAI Images API endpoints and request shape. Compatible providers can differ in which fields they honor; request acceptance is not proof of parity.
Only the provider-facing model ID changes:

| Resolved base URL | Flare wire model | Sunburst wire model |
| --- | --- | --- |
| `api.ofox.ai` or earlier `api.ofox.io` | `openai/gpt-image-2.6-flare` | `openai/gpt-image-2.6-sunburst` |
| OpenAI or any other provider | `gpt-image-2.6-flare` | `gpt-image-2.6-sunburst` |

The CLI records a canonical `model`, the `wire_model`, and the resolved provider
in dry runs and sibling metadata. Provider detection never changes
`/v1/images/generations` or `/v1/images/edits`. Experimental GIF edits are separately restricted to OFOX.

Custom credentials are an atomic pair: `CUSTOM_OPENAI_API_KEY` is accepted only with `CUSTOM_OPENAI_BASE_URL`, and vice versa. This prevents a standard OpenAI credential from being sent to a custom host. Without that pair, the CLI uses `OPENAI_API_KEY` and optional `OPENAI_BASE_URL`.

## Shared request fields

| Field | Values | Local default |
| --- | --- | --- |
| `prompt` | Non-empty string, at most 32,000 characters | Required |
| `model` | Flare or Sunburst model ID | Flare alias |
| `n` | 1–10 variants of the same prompt | 1 |
| `size` | `auto`, preset, or valid `WIDTHxHEIGHT` | `auto` |
| `quality` | `auto`, `low`, `medium`, `high`, `xhigh`, `max` | `auto` |
| `background` | `auto`, `opaque`, `transparent` | `auto` |
| `output_format` | `png`, `jpeg`, `webp`; generation also `gif`, `svg` | `png` |
| `complexity` | `low`, `medium`, `high` | Omitted; model default currently high |
| `frame_count` | GIF only: integer 2–16 | Omitted; API default 9 |
| `frame_duration_ms` | GIF only: integer 20–2000, encoded in 10 ms units | Omitted; API default 200 |
| `output_compression` | 0–100 for JPEG/WebP only | Omitted |
| `moderation` | `auto`, `low`; generation endpoint only | `auto` |

GPT Image responses contain base64-encoded image bytes in the requested format. The CLI does not send `response_format`; URL responses are not supported for these models.

## Still-image dimensions

Custom dimensions must satisfy all conditions:

- width and height are multiples of 16;
- long:short ratio is at most 3:1;
- each edge is at most 3,840 pixels;
- total pixels are 655,360–8,294,400;
- outputs above 2,560×1,440 total pixels are experimental.

Presets: `square`, `landscape`, `portrait`, `wide`, `2k-square`, `2k-landscape`, `4k-landscape`, `4k-portrait`, and `auto`.

## Native GIF and SVG generation

GIF `size` is per frame: `auto` or positive width/height that are multiples of 16. The static minimum pixel gate does not apply. The API enforces GIF-specific sheet and request pixel budgets. Read [animated-gif.md](animated-gif.md) for the 2–16 schema versus 2–64 guide discrepancy, provider control mismatches, transparency, and reference-to-GIF opt-in.

GIF and SVG reject streaming, partial images, compression, and local downscaling. Frame fields require GIF. SVG requires `n=1`; the official edit endpoint does not support SVG. Neither format is a supported raster edit input. The CLI validates and preserves original GIF/XML bytes, rather than resizing or converting them.

For SVG, `quality` and `complexity` control the reference image. Optional `--svg-model` selects an available SVG author; `--svg-reasoning` sets its separate effort. The SDK sends `svg={"model":"...","reasoning":{"effort":"..."}}`. Omit both if selection is disabled. A provider may require `svg.model`; do not invent a model name or silently choose an author. In the local OFOX check, both omission and a supplied model from its live model list still returned a missing-`svg.model` error. SVG delivery through that route remained blocked; `--svg-model` has not been validated as a fix. JSONL fields are `svg_model` and `svg_reasoning`. Author reasoning values depend on the chosen author even though the schema enum includes `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, and `max`.

SVG output must be valid UTF-8 XML with an SVG root and static vector content. The CLI rejects scripts, embedded raster images, external resources, and active elements. It records `svg_usage` separately when returned. XML structure validation does not prove visual quality, text accuracy, or transparent rendering.

## Edit inputs and masks

- Supply 1–16 PNG, JPEG, or WebP images, each smaller than 50MB.
- Input order is significant. Number and role-label images in the prompt.
- A mask must be PNG, smaller than 4MB, contain alpha, and match the first image's dimensions.
- Fully transparent mask pixels indicate the region to edit.
- A mask guides the model; it is not a pixel-hard compositing boundary.

The CLI omits `input_fidelity`, following the current [official prompting guidance](https://developers.openai.com/api/docs/guides/image-prompting).

## Markup-guided 2.6 edits

Keep the original as Image 1. Supply `--markup annotations.png` as a separate transparent PNG layer with circles, sketches, or arrows, and describe the intended change and preservation constraints. Do not flatten the annotations onto the target. The SDK uploads the layer as the named multipart `markup` field, separate from `image`.

- After EXIF orientation, markup dimensions must match Image 1.
- Markup must contain transparent pixels, be smaller than 50MB, and contain at most 16,777,216 pixels; the matching first image has the same pixel ceiling.
- Do not combine markup with a mask or `prompt_rewriter` (the CLI does not expose the latter).
- Markup applies to Image 1; other inputs remain role-labeled references.

A local 2026-11-05 OFOX left/right A/B check accepted both uploads but recolored the right mug for both circle positions. Spatial following was **not validated**. The CLI warns on OFOX markup requests; no hidden flattened-image fallback is used. Whether this comes from provider forwarding or model behavior remains unresolved. Use an unambiguous prompt and inspect the chosen region.

## Transparency

For documented raster alpha support, use `background="transparent"` with PNG or WebP. The CLI also permits transparent 2.6 GIFs based on an OFOX observation and checks all decoded frames; this is not a universal provider guarantee. SVG transparency follows vector rendering rather than raster alpha validation. Ask for an isolated subject or transparent canvas in the prompt as well. Preserve the decoded alpha channel; a painted checkerboard is not transparency. The CLI checks that the result contains an alpha channel with at least one transparent pixel.

## Streaming

Use `--stream --partial-images 0..3`. The Image API guide and endpoint schemas document partial image SSE events for generation and editing. Each requested partial adds output-token cost, and the final image can arrive before every requested partial.

A requested partial can be absent when the final image finishes first. Keep streaming opt-in and verify support on the selected provider route. The CLI supports one final image (`n=1`) per streaming invocation and does not retry after event iteration has begun.

Event types:

- `image_generation.partial_image`
- `image_generation.completed`
- `image_edit.partial_image`
- `image_edit.completed`

## Output and metadata

Without `--force`, the CLI preflights final images, partials, downscaled copies, and sibling metadata before the API call. Final metadata records request settings, canonical and wire model IDs, provider, response settings, complete usage when returned, request ID when available, elapsed time, attempts, inputs, roles, mask/markup, and inspected artifact settings. GIF metadata includes dimensions, actual frame count, per-frame durations, cycle duration, loop, unique frame count, transparent frame count, and mismatches. Requested settings remain separate. Buffered requests emit a heartbeat about every 15 seconds. JSONL batches are capped at 500 jobs and report progress plus a success/failure summary.

## Errors and retries

Retry with bounded exponential backoff for connection failures, timeouts, HTTP 408/409/429, and 5xx responses. Do not automatically retry authentication, quota, moderation, or user-correctable request errors.

Use `error.code` as the stable discriminator when available. `moderation_blocked` can include `moderation_stage` (`input`, `output`, `unknown`) and coarse categories. Keep end-user messages generic; use details for developer diagnostics.

## SDK and source status

The bundled script requires OpenAI Python SDK 3.46.0 or newer, whose named Images parameters include complexity, frame controls, SVG selection, and multipart markup. No new fields are tunneled through `extra_body`. Current official links and known documentation discrepancies are listed in [official-links.md](official-links.md).
