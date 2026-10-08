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

Same family, same per-token price; the difference is the speed/quality point:

- **sunburst** = base/quality model — use for finals, text-heavy and edit-critical
  work.
- **flare** = small/speed model, quality "comparable to
  GPT Image 2" — use for drafts, exploration, high-volume everyday work.

Historical 2026-09-30 skill probes measured ~34s/18s medians at high. These are
not current latency guarantees or a matched comparison with Nano Banana 2.1.

Their per-token rates match; equal cost per call is not guaranteed because
token consumption can differ. Flare prioritizes speed. To spend less, try lower
`--quality` and check actual usage. For demanding references or edits, evaluate
Sunburst; a useful workflow is Flare for exploration and Sunburst for final work.

## Parameter model

| Lever | Values | Notes |
|---|---|---|
| `--quality` | auto/low/medium/high/xhigh/max | rendering detail, latency, and cost tradeoff |
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

- These models support controlled generation and editing. Inspect framing and
  product form after each edit rather than treating preservation as guaranteed.
- **flare** occasionally adds unrequested text/decoration; if the canvas must
  stay clean, use the allowlist wording or switch to sunburst.
- **Mask edits are a guide, not a hard pixel boundary** — the model is nudged
  by the mask rather than physically constrained. For pixel-exact compositing,
  composite the result deterministically afterward.
- Mask handling on upstream gateways has shown occasional hiccups (a region
  flattened to black); rerun critical mask edits rather than trusting one try.

## When Banana may fit better

- Reference-based recontextualization where banana's behavior suits the brief;
  reference count alone does not favor banana (GPT accepts 16, banana 14).
- Extreme ratios like 8:1 / 1:8.
- Output canvases beyond GPT Image 2.5's documented edge/pixel limits. More
  output pixels alone do not imply better visual detail.
