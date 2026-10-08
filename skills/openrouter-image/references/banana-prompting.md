# Prompting Nano Banana 2.1 (`banana`)

Model: `google/gemini-nano-banana-2.1`, accessed through OpenRouter's dedicated
`/api/v1/images` route. The guidance below separates this route's controls from
capabilities available through Google's native API.

## Choose the output budget

| Lever | Supported here | Use |
|---|---|---|
| `--resolution` | `1K`, `2K`, `4K`; default `1K` | 1K for drafts or large headings; 2K for finer copy/detail |
| `--aspect` | explicit ratio, including `8:1`, `1:8`, `4:1`, `21:9` | match the deliverable; no `auto` |
| references | up to 14 total | assign each repeated `--image` a role |
| `--n` | 1 | separate calls for alternatives |

512px is no longer supported. Resolution changes the output pixel budget,
not a quality or thinking setting. A large returned file alone does not prove
native detail or accurate text; inspect at the intended viewing size. Check the
decoded dimensions as well: an `8:1` / `2K` probe returned 5856×704 (about 8.32:1),
and `21:9` / `4K` returned 6336×2688. Allow room to crop when exact aspect or
placement is a delivery requirement.

`--out` does not select an encoding. All 12 live outputs were JPEG; the CLI
detects image bytes, saves the matching extension, and records the actual paths
in metadata. It also detects reference MIME from bytes, so an old JPEG named
`.png` is uploaded as `image/jpeg` rather than mislabeled.

Google's direct API supports `minimal`, `medium` (default), and `high` thinking,
and Web/Image Search grounding. The checked OpenRouter Image API endpoint does
not expose thinking/search parameters or allow them as passthrough options.
This CLI has no thinking, search, mask, or conversation-history flag. Do not
invent those controls or imply that asking for current facts activates search.
For factual imagery, research separately, then supply the verified facts in the
prompt. An annotated reference can guide a semantic edit; it is not a hard
pixel mask. Transparency/background control is unavailable on this route.

## Exact copy and layout

2.1 improves text rendering and infographic layout, but small text, long
paragraphs, exact positioning, and unwanted added copy remain inspection points.
Finalize the wording before generating the image. Put verbatim strings in
quotes, give each a layout role, and state how often each appears. Keep visual
style instructions separate from the copy list.

```text
制作可直接使用的平面竖版科技海报，深蓝背景，中部是发光几何立方体。
顶部为大字主标题，下面为英文副标题；下部三个等宽信息区；底部为日期地点。
文字白名单：主标题“智能体新纪元”；副标题“AGENT NEXT”；
三个信息区从左到右分别写“更强推理”“更长上下文”“更低延迟”；
底部“2026年10月18日 上海”。每段文字只出现一次，逐字保留数字与空格。
文字清晰、边距充足、互不重叠。画面没有其他文字、页码或标志。
输出完整平面设计，不是纸张或屏幕实拍。
```

Use `--resolution 2K --aspect 3:4` for this brief. Read every string, including
punctuation, repeated characters, and background signs. Compare repeated outputs
before treating one correct image as evidence of reliability. For a failed
string, try a focused edit with its exact old/new wording; if the same failure
recurs, enlarge or shorten the copy. Long document text and mathematically exact
charts are better composed with layout/chart tools. For strict final typography,
consider sunburst and inspect its output too.

Specify punctuation as part of the copy contract. In a plain-prompt probe the
model added a middle dot to the date/location and pseudo lettering to the cube;
two 2K whitelist probes preserved the visible date formatting and avoided that
extra copy. The same whitelist also worked at 1K for these large headings:
15.48s/$0.0374 versus 25.35–26.45s/$0.0547 at 2K. This small comparison supports
trying 1K when the viewing size allows it, not a guarantee for small or dense text.

## Reference roles and authority

Up to 14 images is the API ceiling, not a guarantee that 14 identities will
survive a composite. Google's guidance distinguishes up to 4 character references
and up to 10 object references. Start with the fewest clear references that cover
the job; add another view only when it resolves an ambiguity.

- Use a clear face/subject view for identity, a readable front view for a product
  label, and a separate environment image when spatial context matters.
- Number references in their actual `--image` order and name each subject. State
  which supplies identity, product geometry, composition, background, or style.
- If a reference supplies only style, say so: its objects and text should not be
  copied. Resolve conflicting outfits, labels, or poses by naming the source
  that wins.
- Preserve concrete distinguishing details: freckles, glasses, cap shape,
  label wording, proportions, and color. “Keep the same person/product” alone
  leaves these choices underspecified.

```text
Image 1 supplies Maya's identity: tight copper curls, freckles, round
tortoiseshell glasses. Image 2 supplies only the product: a cobalt-blue
cylindrical bottle, smooth black cap, thin gold ring, label “ERIK LAB” / “SERUM 21”.
Place Maya holding that exact bottle in a softly lit studio. Keep her face and
those product details recognizable; match the lighting naturally. Show one Maya
and one bottle. Do not copy image 2's background or add any other text.
```

## Local edits and repeated changes

Specify **Change** and **Preserve** independently, including framing and colors.
These are generation instructions, not a promise of unchanged pixels.

```text
Change: only the bottom date, from “2026年10月18日 上海” to “2026年11月08日 上海”.
Use the same type size, font style, color, baseline and position.
Preserve: the title, English subtitle, three information panels, cube,
background, margins and overall composition. No additional text.
```

Each CLI call is stateless. For a follow-up, supply the approved composition as
image 1; a simple local/background edit can start with that base alone. When
face, label, or shape starts drifting, also supply the original
identity/product references, name their roles, and reapply the desired edits
from the approved base. Do not keep chaining already-damaged outputs. Combining
compatible edits into one brief can reduce the number of regeneration steps;
inspect each accepted result before using it as the next base.

Make the approved base the authority for framing, pose, product placement and
scale. In one background-edit comparison, both base-only and base-plus-originals
preserved the face and product label; extra references showed no clear visual
advantage and used more input tokens. Add them to address a specific drift or
ambiguity rather than automatically including every original on every edit.

For pixel-exact preservation outside a region, use deterministic compositing
rather than certifying a generative edit as pixel-identical.

## Extreme formats

2.1 specifically addresses tiling artifacts on wide/panoramic formats at 2K/4K.
For `8:1`, describe left/center/right zones with a continuous horizon,
perspective, light direction, and transitions. For `1:8`, describe top-to-bottom
zones. Inspect seams, repeated structures, and subject cropping across the whole
canvas. Resolution tier and returned dimensions vary by ratio/provider; neither
large dimensions nor increased token counts prove the model's internal rendering
method.

## Inspect and recover

Inspect exact copy, counts, face/product details, preserved regions, panorama
seams, and returned dimensions. Check sibling metadata for actual `usage.cost`.
Check instance counts separately from scene quality: the `8:1` panorama had four
bicycles although the prompt requested three. Visually preserved details also
do not imply unchanged foreground pixels; the date/background edits retained
their semantic content but showed pixel differences outside the requested change.
For candidates in parallel, launch separate calls with distinct output paths.

## Sources and verification

Endpoint capabilities were checked on 2026-10-08 against OpenRouter's
`GET /api/v1/images/models` and
`GET /api/v1/images/models/google/gemini-nano-banana-2.1/endpoints`.
Thinking/search were absent from the Image API descriptors and passthrough
allowlist. Recheck these records before adding new controls.

After earlier upstream 429s, 12 dedicated Image API calls succeeded on 2026-10-08:
poster control/whitelist/repeat/1K comparison, product and portrait fixtures,
two-reference composite, date-only edit, two background edits, and 2K/4K
panoramas. Total reported cost was $0.666531; latency ranged from 11.92 to 34.15s.
The examples above reflect those inspected outputs. This is a small application
probe, not a reliability benchmark or a head-to-head GPT comparison; 14-reference
capacity, thinking/search control, transparency and long edit chains were not
tested. Nano Banana 2 observations do not establish 2.1 performance.

- [OpenRouter model](https://openrouter.ai/google/gemini-nano-banana-2.1) and
  [Image API capabilities](https://openrouter.ai/docs/guides/overview/multimodal/image-generation)
- [Google 2.1 specifications](https://ai.google.dev/gemini-api/docs/models/gemini-nano-banana-2.1?hl=en)
  and [image prompting/reference guidance](https://ai.google.dev/gemini-api/docs/image-generation)
- [Google model card: comparisons and limitations](https://deepmind.google/models/model-cards/nano-banana-2-1/)

For evaluation, use the [replay probes](../evals/banana-2.1-probes.jsonl) and
[application scenarios](../evals/evals.json). Routine generation does not require
running them.
