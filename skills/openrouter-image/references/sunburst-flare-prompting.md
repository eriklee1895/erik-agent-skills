# Prompting GPT Image 2.5 (`sunburst` / `flare`)

The two GPT Image 2.5 models share one parameter matrix; this is their model
knowledge, mirroring [banana-prompting.md](banana-prompting.md).

## What these models are good at

- **Exact in-image text**: posters, slides, infographics with many verbatim
  labels; precise hierarchy and counts.
- **Controlled edits**: state the change and preservation list, then inspect
  the regions and attributes that should remain.
- **Transparent backgrounds, natively**: soft alpha, real refraction through
  glass — no downstream cutout needed.
- **Up to 16 reference images** and up to **10 variants per call** (`--n`).

## sunburst vs flare

The two aliases share the same controls. Sunburst is the base/quality tier;
Flare is the small/speed tier. Use the requested tier, or start with Sunburst
for a task whose text/layout or edit fidelity needs evaluation. The tier name
is not a guarantee for a particular prompt; inspect the required details.

Model selection and `--quality` are separate controls. Adjust quality when it
addresses a visible requirement, and read actual usage after generation.

## Parameter model

| Lever | Values | Notes |
|---|---|---|
| `--quality` | auto/low/medium/high/xhigh/max | rendering detail, latency, and cost tradeoff |
| `--n` | 1–10 | distinct variants of one prompt |
| `--aspect` | 1:1, 3:2, 2:3, 4:3, 3:4, 16:9, 9:16, 21:9, auto | `auto` allowed |
| `--background` | auto/transparent/opaque | transparency is native |
| references | up to 16 | repeated `--image` |
| streaming | API supported | SSE partial frames; not exposed by this CLI |

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
- Output canvases beyond GPT Image 2.5's documented edge/pixel limits. More
  output pixels alone do not imply better visual detail.
