# Prompting Grok Imagine 2.0 and MAI-Image-2.6

Both are verified members of the curated list. The measurements below come from
a 14-call probe on 2026-11-04 (identical prompts across Grok 2.0, MAI 2.6, and a
comparison set); they describe observed behavior, not a model card or an arena
ranking.

## What each is good at

**Grok Imagine Image 2.0** (`x-ai/grok-imagine-image-2.0`)

- Strongest stylized-illustration rendering in the group: painterly hair, light
  and material detail, convincing glowing effects.
- 2K output (2048×2048 at 1:1, 1776×2368 at 3:4) — the highest native detail
  among the cheaper aliases.
- Accurate short Chinese copy: a three-line poster rendered every glyph
  correctly in the probe.
- Weaknesses: 45–110 s per image, and **only three references**.

**MAI-Image-2.6** (`microsoft/mai-image-2.6`)

- Clean, restrained editorial look; good for product shots, UI-style visuals
  and thumbnails where a soft painterly finish is not wanted.
- Cheapest per image of the curated set (~$0.03) and reasonably fast (24–36 s).
- Accurate short Chinese copy in the probe.
- Weaknesses: **~1 MP ceiling** (768×1024 at 3:4, 1024×1024 at 1:1) — do not use
  for posters, print, or anything that needs fine type at large size. The
  provider rejects any `n` other than 1.

## Parameter matrix

| Lever | Grok | MAI |
|---|---|---|
| Aspect | 1:1, 3:4, 4:3, 9:16, 16:9, 2:3, 3:2, 9:19.5, 19.5:9, 9:20, 20:9, 1:2, 2:1, auto | 1:1, 4:3, 3:4, 16:9, 9:16, 3:2, 2:3, auto |
| Resolution | `1K` / `2K` | none |
| Quality | `low` / `medium` | none |
| `n` | 1 | 1 (provider error: `must be exactly 1`) |
| References | 3 | 5 |
| Transparency | unsupported | unsupported |
| Compression | unsupported | unsupported |

Omitting `--resolution` and `--quality` on Grok leaves both fields out of the
request and the provider defaults apply (observed: 1K/medium, $0.06).

## Prompt patterns

**Stylized illustration (Grok's strongest case)**

```text
精致日漫插画头像：30岁东亚女性产品设计师，深紫短卷发，大眼，轻雀斑，
不戴眼镜，穿紫绒短西装与青绿真丝翻领，浅紫背景，发光蝴蝶。
头肩近景，脸部约占画面高度45%，背景铺满方形画布，无文字。
```

Grok adds visual density on its own, so keep the prompt specific and avoid
stacking style adjectives — they mostly add clutter.

**Budget editorial visual (MAI)**

```text
极简产品图：一只陶瓷杯，奶油白背景，柔和侧光，干净留白，
右上角一个抽象紫色几何标记，无文字。
```

MAI tends to invent a tidy workspace backdrop (papers, dashboards) if the
prompt leaves the environment open. Name the background explicitly when the
canvas must stay clean.

## Reference use

- Grok: number each image's role and keep to three. A fourth reference is
  rejected before generation:
  `input_references: must have between 0 and 3 items`.
- MAI: up to five references. Each reference raises cost; the probe with two
  references cost $0.055 versus $0.039 without.

Both preserve a supplied character well when the prompt names the attributes to
keep and the ones to change (Change / Preserve style). Neither offers mask
control.

## Choosing between them

| Job | Pick |
|---|---|
| Anime / painterly character art, avatar, cover illustration | grok |
| Poster with large type, dense layout, print resolution | sunburst |
| Cheap drafts, product/UI visuals, thumbnails | mai |
| Wide panoramas, 4K canvases, 8:1 ratios | banana |
| Many variants of one prompt | sunburst / flare (`--n`) |

## Evidence boundary

The probe covered one prompt per capability (Chinese poster, two-reference edit,
1:1 illustration) plus four parameter-boundary calls. It establishes that both
models work and where their limits are; it does not establish superiority for
every art direction. Re-run a matched pair before switching a production
workflow to either model.
