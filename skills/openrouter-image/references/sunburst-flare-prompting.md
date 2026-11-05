# Prompting GPT Image 2.6 (`sunburst` / `flare`)

The two GPT Image 2.6 models share one OpenRouter parameter matrix. Use `sunburst` or `flare` and select quality and complexity for the deliverable.

## What these models are good at

- **Exact in-image text**: posters, slides, infographics with many verbatim
  labels; precise hierarchy and counts.
- **Controlled edits**: state the change and preservation list, then inspect
  the regions and attributes that should remain.
- **Transparent backgrounds, natively**: soft alpha, real refraction through
  glass — no downstream cutout needed.
- **Up to 16 reference images** and up to **10 variants per call** (`--n`).

## sunburst vs flare

The two aliases share the same controls. Sunburst emphasizes detail and
consistency across edits; Flare emphasizes speed. Use the requested tier, or start with Sunburst
for a task whose text/layout or edit fidelity needs evaluation. The tier name
is not a guarantee for a particular prompt; inspect the required details.

Model selection and `--quality` are separate controls. Adjust quality when it
addresses a visible requirement, and read actual usage after generation.

## Parameter model

| Lever | Values | Notes |
|---|---|---|
| `--quality` | auto/low/medium/high/xhigh/max | rendering detail, latency, and cost tradeoff |
| `--complexity` | low/medium/high | 2.6 planning before rendering; omitted uses the upstream default |
| `--output-format` | png/jpeg/webp | omitted uses provider default; GIF/SVG unavailable on this route |
| `--output-compression` | 0–100 | requires explicit jpeg/webp; PNG has no compression knob here |
| `--n` | 1–10 | distinct variants of one prompt |
| `--aspect` | 1:1, 3:2, 2:3, 4:3, 3:4, 16:9, 9:16, 21:9, auto | `auto` allowed |
| `--background` | auto/transparent/opaque | transparency is native |
| references | up to 16 | repeated `--image` |
| streaming | API supported | SSE partial frames; not exposed by this CLI |

`complexity` and `quality` are separate: use less planning for a straightforward
draft, more planning for a complex arrangement, and quality for rendering detail.
The CLI sends complexity under `provider.options.openai`, never as a top-level
field. Native OpenAI's default is high; this CLI omits the field when unspecified.
Transparent background requires PNG or WebP and is rejected with JPEG.

## OpenRouter access boundary

OpenAI's official API demo describes its GIF workflow as sprite-sheet generation followed by automatic frame extraction and looping GIF assembly. Native GIF names the finished API deliverable. OpenRouter's supported output formats determine whether that workflow is available through this access path. [Official OpenAI demo](https://www.youtube.com/watch?v=9ZxCOHkfn_8)

Use `POST https://openrouter.ai/api/v1/images` for generation and edits.
Reference images use `input_references`; this route exposes no native mask or
markup image field. GPT 2.6's native GIF and SVG features appear in the model
description, but OpenRouter's per-endpoint output formats are png/jpeg/webp and
its passthrough allowlist is only moderation/complexity. `frame_count` and
`frame_duration_ms` are unavailable; do not bury them inside provider options.
The global Image API can return SVG for other vector models, which does not
establish SVG support for GPT 2.6.

Buffered responses carry `data[].b64_json`, optional `media_type`, and `usage`.
Inspect actual bytes and the saved metadata's `response.images` labels. Rates
on 2026-11-05 were $5/M text-input tokens, $8/M image-input tokens, and $30/M
image-output tokens for both tiers; query current rates before budgeting and
use actual `usage.cost` after calls.

Verified sources (2026-11-05):

- [Sunburst endpoint descriptor](https://openrouter.ai/api/v1/images/models/openai/gpt-image-2.6-sunburst/endpoints)
- [Flare endpoint descriptor](https://openrouter.ai/api/v1/images/models/openai/gpt-image-2.6-flare/endpoints)
- [OpenRouter Image API](https://openrouter.ai/docs/guides/overview/multimodal/image-generation)
- [Typed Python SDK image parameters](https://openrouter.ai/docs/client-sdks/python/sdks/images/README.md)

Model choice (`flare`) and `--quality max` are separate: "flare + quality max"
is the fast family at maximum detail, not a different model.

## Prompting patterns

**Text-heavy deliverable — quote every string and keep an allowlist:**

```text
竖版海报，深色背景。仅出现以下文字：
主标题“智能体新纪元”；副标题“2026 全球开发者大会”；
时间“10月18日 上海世博中心”；底部“更强推理 · 更长上下文 · 更低延迟”。
除此以外画面中不出现任何文字。
```

An explicit copy list reduces ambiguity about decorative text; check that the
result contains only those strings, with the correct spelling and counts.

**Structured edit — Change / Preserve:**

```text
Change: only the date, from “2026年3月15日” to “2026年4月8日”,
same font, size, color and position.
Preserve: the title “产品发布会”, the background, the layout, and every
pixel outside the date region.
```

Naming the preserved layout and attributes helps constrain the edit. It does
not establish pixel-identical regions outside the requested change.

**Fuse references — number each image's role:**

```text
Image 1 is the product, image 2 supplies only the style (palette and light).
Keep image 1's product shape and edges identical; do not let image 2 alter it.
```

**Variants:** use `--n 4` for four alternatives to the same prompt in one call.
Use separate prompts when the brief itself changes, and check returned usage
rather than assuming a multi-output call saves money.

## Behavior to expect

- These models support controlled generation and editing. Inspect framing and
  product form after each edit rather than treating preservation as guaranteed.
- Inspect unrequested text or decoration on either model; refine the copy list
  and layout when the brief requires a clean canvas.
- This CLI exposes no mask control. For pixel-exact preservation outside an
  edited region, composite the result deterministically afterward.

## When Banana may fit better

- Reference-based recontextualization where banana's behavior suits the brief;
  reference count alone does not favor banana (GPT accepts 16, banana 14).
- Extreme ratios like 8:1 / 1:8.
- Output canvases beyond the chosen GPT route's supported dimensions. More
  output pixels alone do not imply better visual detail.
