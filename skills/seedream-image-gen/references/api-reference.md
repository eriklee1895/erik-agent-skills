# Seedream Pro / Flash API contract

Checked **2026-10-24** against the official [API](https://www.volcengine.com/docs/ark/image-generation-api), [Pro/Flash tutorial](https://www.volcengine.com/docs/ark/seedream-5-0-pro), [interaction guide](https://www.volcengine.com/docs/ark/seedream-5-0-pro-editing-guide), [model tutorial](https://www.volcengine.com/docs/ark/seedream-4-0-5-0), [prompt guide](https://www.volcengine.com/docs/ark/seedream-4-0-5-0-prompt-guide) and [pricing](https://www.volcengine.com/docs/ark/model-pricing). The public pages correspond to the console documentation. Model/account limits can change; they are not hardcoded into a rate scheduler.

## Models and common fields

`POST https://ark.cn-beijing.volces.com/api/v3/images/generations`, bearer `ARK_API_KEY`. Both generation and editing use this endpoint. The skill supports Pro `doubao-seedream-5-0-pro-260628` and Flash `doubao-seedream-5-0-flash-260915`.

| Field | Shared contract |
|---|---|
| `model` | Model ID; CLI aliases resolve explicitly. Custom endpoint IDs retain Pro capability defaults with a warning. |
| `prompt` | Required for generation/editing; optional for decomposition. Prefer concise subject/action/environment plus composition and exact quoted text. |
| `image` | URL/data URL string or list; generation accepts up to ten references, decomposition exactly one. |
| `size` | Generation: 1K/1.5K/2K or WxH. Decomposition: auto/1K/1.5K/2K. |
| `optimize_prompt_options.mode` | Pro: standard/fast. Flash: standard only. Unsupported modes fail locally. |
| `output_format` | png/jpeg; for decomposition this controls the base only. Foreground layers always use PNG. |
| `background` | opaque by default; transparent is only for editing one alpha-bearing input, with PNG output. |
| `layer_decomposition` | false by default; true requests base+layers. |
| `response_format` | url by default, or b64_json. CLI uses URL downloads; decoder also accepts inline base64. |
| `watermark` | API default true; CLI explicitly defaults false. |

Ordinary generation returns one image per request. Neither supported model accepts sequential/storyboard generation, web search or streaming. CLI variants and batches issue separate requests. Do not send invented `n`, `num_images`, `seed`, `mask`, `bbox`, `layers` or ControlNet fields. Coordinate tags belong in `prompt`.

## Sizes

Both native generation models allow **921,600–4,624,220 pixels**, aspect ratio **1/16..16**. Constraints concern W×H, not a fixed bound on each side. Native 512×512 is below the floor; the CLI can generate larger and downsize to that destination. `--no-auto-upscale` restores rejection.

| Aspect | 1K reference | 1.5K reference | 2K reference |
|---|---|---|---|
| 1:1 | 1024×1024 | 1536×1536 | 2048×2048 |
| 4:3 | 1152×864 | 1792×1344 | 2368×1776 |
| 3:4 | 864×1152 | 1344×1792 | 1776×2368 |
| 16:9 | 1424×800 | 2048×1152 | 2816×1584 |
| 9:16 | 800×1424 | 1152×2048 | 1584×2816 |
| 3:2 | 1248×832 | 1872×1248 | 2496×1664 |
| 2:3 | 832×1248 | 1248×1872 | 1664×2496 |
| 21:9 | 1568×672 | 2352×1008 | 3136×1344 |

These are official preset reference mappings, not guarantees for arbitrary prompts. Explicit WxH controls destination pixels. Layer `auto` follows each source element's dimensions within native bounds and adjusts below/above them; never assume all crops share the base size.

## Input and transparency restrictions

Generation accepts jpeg/png/webp/bmp/tiff/gif/heic/heif references, ratio 1:16..16:1, sides >14px, ≤30MB and ≤36M pixels per image. Local files become lowercase-MIME data URLs. URLs are passed to the service and must be reachable there.

Decomposition accepts only one PNG/JPEG, 262,144–36M pixels and ≤30MB. Transparent editing requires one alpha-bearing image and PNG output. It is not direct text-to-transparent generation, nor a JPEG cutout switch. A foreground PNG returned by decomposition is a suitable next-step transparent-edit input.

## Coordinate editing

Use image-relative `<point>x y</point>` or `<bbox>left top right bottom</bbox>` tags in the prompt, normalized to 0–999. Name the object if several overlap the box, and explicitly name any object/region to preserve. Reference numbering must match upload order.

Visible marker drawing remains an alternative. Marker rectangles use x,y,width,height, not right/bottom. Coordinate tags guide a generative edit; they are not a hard pixel mask. Native mask, depth-map or custom LoRA uploads are not exposed by this CLI.

## Layer response

The response `data` array contains one base (`z_index: 0`) and up to sixteen foreground PNGs. Each item may include `url`/`b64_json`, `size` and `output_format`; layer-specific fields include `z_index`, `bounding_box`, `name` and `description`.

- `bounding_box.absolute`: [left, top, right, bottom] in the **output base's pixel coordinates**. Resize a crop to right-left by bottom-top before placing it.
- `bounding_box.normalized`: corresponding bounds in **0–1000**, suitable for a resized target canvas. This range differs from edit prompt tags.
- Stack in ascending z-index. The model-generated name is descriptive metadata, not a trusted filename.
- Any layer generation failure makes the decomposition request fail as a whole according to the API contract. Client/download failures do not authorize another generation request.

The CLI stores local files and `layers.json`, not expiring response URLs or inline base64. See [transparency and reconstruction](transparent-layers.md). PSD export is not claimed; files plus positioning metadata allow downstream reconstruction.

## Outpainting

Existing `edit --outpaint direction:pixels` creates a padded local canvas and asks the model to extend the scene. It is a client convention, not a native `outpaint` API field. The current padded canvas is opaque, so it cannot be combined with transparent editing. Generative outpainting may repaint the center; it does not guarantee pixel identity.

## Responses and failure handling

`usage.generated_images` counts successful output images, `input_images` counts references, and token fields describe image generation usage. Layer mode may return many charged outputs from one request. URL assets last 24 hours and are downloaded immediately.

| Outcome | Client action |
|---|---|
| 400/401/403 | Stop; fix parameters, credentials or access. |
| Explicit 429/5xx | Existing bounded backoff and numeric retry-after handling. |
| Timeout/transport outcome unknown | Stop with OutcomeUnknown; do not automatically repeat a possibly paid request. |
| Download failure after generation | Retry only the download; exhaustion never repeats generation. |
| Missing image/per-item error | Report failure; do not report an empty success. |

Layer requests provisionally reserve seventeen IPM and refund the difference after actual output count is known. This describes quota accounting, not a reason to impose a fixed client IPM target or cap user concurrency. Filter/rejection errors should be reported accurately; do not disguise content to evade a provider rejection.

## Public list pricing snapshot

| Model / task | Output image | Input image |
|---|---|---|
| Pro generation, ≤2.61M pixels | CNY0.30 | first free, additional CNY0.02 each |
| Pro generation, >2.61M pixels | CNY0.60 | same |
| Pro decomposition, ≤2.61M pixels | CNY0.15 per output | same |
| Pro decomposition, >2.61M pixels | CNY0.30 per output | same |
| Flash generation/decomposition | CNY0.12 per output | free |

Snapshot from the linked pricing page, not an account bill or runtime rate limit. Each layer is priced by its own actual output tier. The official guide states 1.5K shares the 1K tier; it can be a useful intermediate choice before 2K. Failed images rejected by the service are not charged according to that pricing page.
