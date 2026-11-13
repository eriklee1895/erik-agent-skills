# Seedream 5.5 workflows and evidence

Read for task-specific prompts, multi-round edits, transparency, fusion or layer/text reuse. Official API constraints are in [api-reference.md](api-reference.md); measured results and sample limitations are in [the 5.5 benchmark](../evals/seedream55-benchmark.md).

## Evidence selection

Research checked 2026-11-14, using Chinese Doubao Search queries plus English/Chinese web searches. Read the official 5.5 tutorial, API, OCR fonts, generic tutorial, streaming reference and both legacy editing documents. The console pages expose Markdown routes under `ark.volcengine.com/region:cn-beijing/docs/<slug>.md`; the bundled volcengine-doc-fetcher also successfully retrieved their public `/docs/ark/<slug>` equivalents.

Community sources are useful for tasks and failure hypotheses, not Ark parameter authority:

| Firsthand source | Useful test hypothesis / workflow | Qualification |
|---|---|---|
| [Segmind, 2026-11-11](https://blog.segmind.com/seedream-5-5-is-here-edit-in-rounds-transparent-pngs-and-layers/) | Product colorway edit chains; inspect brightness drift and glass opacity; localize copy. | Vendor-authored tests on its wrapper. Its endpoint names and USD prices are not Ark's. |
| [XinYu, 2026-11-12](https://xinyuai.app/zh/news/seedream-5-5-layer-split-measured) | Recompose crops by bbox; inspect lost shadows, haze, inpainted backgrounds and cross-layer contamination. | Five images, one decomposition each; it did not enable OCR. “Text layers are images” does not mean 5.5 lacks OCR. |
| [花叔, 2026-11-10](https://www.woshipm.com/ai/6491515.html) | State one change plus explicit protected details; reuse product packaging and role-specific references; sticker/sprite assets. | UI-based selected examples, not a reproducible Ark benchmark or proof that every 100-round chain preserves pixels. |
| [APPSO firsthand account](https://c.m.163.com/news/a/LBANNEU305118O8G.html) | Iterative design work, independent transparent assets and reusable marketing layers. | UI workflows can include application-level postprocessing. |

The [Seed team's launch article](https://seed.bytedance.com/zh/blog/more-realistic-images-more-stable-editing-across-100-rounds-introducing-seedream-5-5?view_from=content_recommend) reports its own preference/text-corruption evaluations and 100-round examples. Those are vendor evaluations, distinct from this skill's measured sample. Third-party “3K/4K” claims conflict with the documented Ark native range; use the official API contract.

## Precise edits and multi-round continuity

A concise edit recipe:

> 只把图1左侧马克杯的杯身和把手改为深蓝色。保持杯子形状、右侧花瓶、花朵、柠檬、桌面、背景、光影和构图不变。

Add normalized point/bbox tags when target identity or location is ambiguous. For fixed-layout artwork, lock geometry explicitly:

> 只修改图1 <bbox>58 64 512 175</bbox> 内的标题，把“GREEN STUDIO”改成“BLUE STUDIO”。严格保持文字原来的左上角位置、字号、颜色和字体。框外所有像素保持原样，不调整布局、不增加纹理、不移动色块、不改变留白，保持1536×1024画布。

In the measured flat-poster case, the shorter target+preservation prompt caused a global shrink/recenter. This more explicit recipe retained geometry through six chained edits, while still adding texture and accumulating slight darkening. One chain does not prove universal reliability; it does show why “keep everything else” alone can be insufficient. The region is a semantic instruction, not a hard mask. Use the previous **accepted** output as the next reference; keep an original and checkpoints. Compare changes both to the previous round (local drift) and the original (cumulative drift), and separately verify that the target changed correctly. RGB input plus `background=opaque` is the official recommendation for long editing chains.

A no-op or incorrect target change can score excellent protected-region similarity. A global exposure change may have tiny mean error yet accumulate across rounds. Do not equate “looks like the same scene” with literal unchanged pixels.

For many colorways, prefer branching from the accepted original when independent variants are wanted; use chaining when changes are intended to accumulate. For multilingual markets, branch each localization from the original design.

## Transparent assets

> 独立的红色陶瓷茶壶，完整壶嘴与把手，柔和半透明接触投影，主体之外完全透明，不要桌面、背景或文字。

Use `--background transparent --output-format png`. With an RGB reference, specify “只提取…” and the exact subject; no pre-cut alpha input is necessary on 5.5. For several references, state each subject and arrange them independently on **one** transparent canvas. Split or decompose later if separate files are required.

Check the actual alpha channel and composite over contrasting backgrounds. Glass needs an interior transparency check; antialiased edges alone produce partial-alpha pixels even when the object's interior is opaque. Soft contact shadows, smoke, hair and refraction need visual inspection.

Transparent sticker and sprite sheets are promising community uses. Specify rows/columns, count, cell order, consistent character scale and no overlap. Native output is still one raster; frame extraction, registration and animation assembly are additional local work. Exact frame count and animation continuity require separate validation.

## Text and small print

> 横版茶叶海报，标题准确写“桂馥茶集”，副标题“冬日暖茶，第二杯半价”。小字四行：“净含量：250克”“配料：云南红茶、桂花”“活动日期：2026.11.20—11.30”“门店地址：上海市静安区新绿路128号”。奶油白背景，深绿无衬线字，右侧热茶，布局疏朗。

Quote exact payloads; state hierarchy, line count, location and visual font description. Use 2K when text is dense, then inspect full resolution and final presentation size. Verify digits, punctuation, signs, accents and scripts independently; “readable” and “exact” are different criteria. Arabic/other unfamiliar scripts need a capable reader/OCR with a known ground truth before claiming accuracy. The model's own OCR is a convenience, not an independent evaluator of its generated text.

For invariant production labels or last-mile copy changes, use local text typesetting rather than repeatedly generating a finished label. Rich-text OCR helps recover content and layout, but font matching and visual style remain approximate.

## Reference fusion and realism

Assign reference roles and protected properties:

> 图1负责杯子和花瓶的形状、颜色与材质，图2负责海报布局。把产品放进图2右下角，保持图2所有文字和背景。产品尺寸合理、透视统一，左侧窗光与接触阴影一致。

Inspect object count, shape, identity and relative scale separately from attractive lighting. A composition can look polished while moving a protected object, losing lettering or changing a handle. For people, check hands, facial expression and proportions; for materials, inspect metal reflections, glass transmission and fabric texture. A small sample supports task observations, not a universal model ranking.

## Layer granularity and local text edits

Start with automatic decomposition plus `--text-recognition`. Use a moderate `--max-images` appropriate to complexity; raise it when unrelated elements are merged, rather than assuming it specifies an exact count. Compare semantic layers, background removal and recomposition. An embedded product label may remain part of a product/shape layer and consequently have no OCR.

To change only copy without generative drift: extract layers and OCR → omit the original text layer → re-render the replacement in the OCR line bbox with an available font → compose the other layers unchanged. If the text layer contains multiple lines, preserve or re-render the other lines too. [The layer reference](transparent-layers.md) documents coordinate systems, OCR fields and limitations.
