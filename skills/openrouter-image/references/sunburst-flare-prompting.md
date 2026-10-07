# Prompting GPT Image 2.5 (`sunburst` / `flare`)

The two GPT Image 2.5 models share one parameter matrix; this is their model
knowledge, mirroring [banana-prompting.md](banana-prompting.md).

## What these models are good at

- **Exact in-image text**: posters, slides, infographics with many verbatim
  labels; precise hierarchy and counts.
- **Structured edits that preserve everything else**: state the change and the
  preservation list, and regions outside the edit stay stable.
- **Transparent backgrounds, natively**: soft alpha, real refraction through
  glass — no downstream cutout needed.
- **Up to 16 reference images** and up to **10 variants per call** (`--n`).

## sunburst vs flare

Same family; September measurements showed this speed/quality tradeoff:

- **sunburst** = base/quality model. Slower (~34s at high), most literal and
  precise — use for finals, text-heavy and edit-critical work.
- **flare** = small/speed model. Faster (~18s at high), quality "comparable to
  GPT Image 2" — use for drafts, exploration, high-volume everyday work.

They shared the same token price in the September tests; actual call cost
depends on usage. To reduce the detail budget, lower `--quality`. The quality
gap between them widens as the task gets harder (more references, more demanding
edits), so a good working rhythm is flare to find
the direction, sunburst to finish.

## Parameter model

| Lever | Values | Notes |
|---|---|---|
| `--quality` | auto/low/medium/high/xhigh/max | reasoning budget; the detail lever |
| `--n` | 1–10 | distinct variants of one prompt |
| `--aspect` | 1:1, 3:2, 2:3, 4:3, 3:4, 16:9, 9:16, 21:9, auto | `auto` allowed |
| `--background` | auto/transparent/opaque | transparency is native |
| references | up to 16 | repeated `--image` |
| streaming | supported | SSE partial frames |

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

Listing exactly what text is allowed is what prevents decorative copy the model
might otherwise invent.

**Structured edit — Change / Preserve:**

```text
Change: only the date, from “2026年3月15日” to “2026年4月8日”,
same font, size, color and position.
Preserve: the title “产品发布会”, the background, the layout, and every
pixel outside the date region.
```

A bare "change the date" can let the model re-render the whole scene; naming
what is preserved is what makes the edit stay local.

**Fuse references — number each image's role:**

```text
Image 1 is the product, image 2 supplies only the style (palette and light).
Keep image 1's product shape and edges identical; do not let image 2 alter it.
```

**Variants:** use `--n 4` to get four alternatives in one call (cost scales
with the count). This is cheaper than reasoning about four separate prompts
when only composition varies.

## Behavior to expect

- These models are the most **literal** of the three — framing and product form
  are preserved rather than re-imagined.
- **flare** occasionally adds unrequested text/decoration; if the canvas must
  stay clean, use the allowlist wording or switch to sunburst.
- **Mask edits are a guide, not a hard pixel boundary** — the model is nudged
  by the mask rather than physically constrained. For pixel-exact compositing,
  composite the result deterministically afterward.
- Mask handling on upstream gateways has shown occasional hiccups (a region
  flattened to black); rerun critical mask edits rather than trusting one try.

## When NOT to use these — pick banana instead

- Fusing more than ~6 references at once (banana takes 14 and is built for it).
- Extreme ratios like 8:1 / 1:8.
- A creatively different reinterpretation rather than a literal result.
