# Seedream 5.5 focused prompt recipes

Use one model and select the recipe by the user outcome. These are recommended starting points grounded in the [measured benchmark](../evals/seedream55-benchmark.md); added layout/grouping constraints are adaptations, not independently measured success guarantees. Native alpha, decomposition and OCR require their API switches as well as semantic prompt instructions. See [API fields](api-reference.md) and [layer/OCR coordinates](transparent-layers.md) when needed.

## 1. Text rendering: exact copy, hierarchy and placement

**Recipe:** purpose/layout → exact quoted strings, one line at a time → location/hierarchy → visual font/color → illustration/materials → content constraints.

```text
横版茶叶海报，奶油白背景，深绿色文字，右侧一杯热茶，布局疏朗。
左上大标题准确写“桂馥茶集”；下面一行副标题“冬日暖茶，第二杯半价”。
左下小字按以下四行逐字排版：
“净含量：250克”
“配料：云南红茶、桂花”
“活动日期：2026.11.20—11.30”
“门店地址：上海市静安区新绿路128号”
标题、副标题、说明文字层级清楚，文字与杯子不要重叠；仅出现以上文案，不增加杯身标签或其他品牌文字。
```

Use `generate --size 2K`. Describe a font category when the design needs one (for example, 深绿色无衬线粗体); font naming is guidance, not an exact font-file selector. For multilingual copy, provide the approved translation for each language and its line/location, rather than asking the model to invent and translate copy while drawing. Specify numerals, units and punctuation literally.

**Check:** exact payload and extra text are separate criteria. In the measured primary tea/lab samples, both models rendered the specified Chinese/English copy, but one 5.5 lab image added a bottle label despite a no-extra-text instruction. Inspect full resolution and final display size, including accents, dates, prices, ±, °C and units. Unfamiliar scripts need a capable reader or independent OCR before claiming exactness; the model's own OCR is not an independent text-quality evaluator. Use local typesetting for invariant production labels.

## 2. Multi-round editing: one change plus protected geometry

**Product/material recipe:** name the target and new state, then explicitly protect object identity, adjacent objects, light and composition.

```text
只把图1左侧马克杯的杯身和把手改为深蓝色。
保持杯子形状、右侧花瓶、花朵、柠檬、桌面、背景、光影和构图不变。
```

**Fixed-layout text recipe, used in the refined six-round study:**

```text
只修改图1 <bbox>58 64 512 175</bbox> 内的标题，把“GREEN STUDIO”改成“BLUE STUDIO”。
严格保持文字原来的左上角位置、字号、颜色和字体。
框外所有像素保持原样，不调整布局、不增加纹理、不移动色块、不改变留白，保持1536×1024画布。
```

Use `edit --reference-image previous-accepted.png --background opaque --size 1536x1024` for that example. Replace the bbox and size with the actual input geometry. Prompt coordinates are normalized **0–999**, not pixels. RGB inputs and opaque mode are the official preference for editing consistency. The recipe asks for pixel preservation; it does not enforce a hard mask.

**Round handling:** feed the previous accepted output into the next round, describe the new delta, and retain earlier accepted changes. Compare both with the preceding round and the original. A no-op can score excellent protected-region similarity; verify the target changed too. For independent colorways or language markets, branch from the same accepted original instead of chaining unrelated variants.

**Check:** the short poster prompt recentered/shrank the layout; the explicit geometry recipe preserved approximate geometry through six rounds, but still added texture and darkened. Check target, position/scale, small print, light and accumulated drift separately. Return to a checkpoint after a failed round.

## 3. Layer splitting/classification: define semantic units and preserve OCR

**Recipe:** invoke native decomposition → name independently reusable elements → state what should stay together → request meaningful separation without inventing API class fields.

```text
将这张活动海报拆分为可单独复用的图层。
主标题、副标题、日期和票价分别独立；杯子、花瓶、装饰色块分别独立；背景作为底图。
同一物件的把手、边缘和内部细节保持在该物件图层中，避免混入相邻物体。
保留原有构图、颜色和各元素的相对位置；不要生成图层示意拼图，不增加新元素。
```

This selection/grouping prompt is an adaptation of the tested automatic splitting and object-selection workflow, not a guarantee of exact grouping. Start with **no prompt** for automatic splitting, then add a short selection/grouping prompt when unrelated elements are merged or only specific subjects are needed.

```bash
uv run scripts/seedream_image_gen.py decompose --reference-image poster.png \
  --max-images 20 --text-recognition --size auto --out-dir output/poster-layers \
  --prompt-file layers-prompt.txt
```

**Switches:** `layer_decomposition=true` invokes the operation; `layer_decomposition_options.max_images` is a total-output upper bound including the base; `text_recognition=true` requests structured OCR for regular text layers. Saying “识别文字” in a prompt does not replace the OCR switch. Do not pass `background` in decomposition mode.

**Classification:** the schema returns `name` / `description`, z-index and optional OCR, not a native `layer_type` or `role` enum. Base = z-index 0. OCR-bearing layers are recognized regular text. For the rest, inspect crop + name/description to derive subject/decoration/raster-text/mixed-group labels. Missing OCR does not prove no text is present; the measured “ARK 55” lettering stayed inside a blue shape without its own OCR.

**Check/reuse:** resize each crop to its bbox in the **returned base's** coordinate system before composition. Evaluate background inpainting, shadow loss, crop contamination and approximate reconstruction. To change copy deterministically, omit the old text layer and render replacement text at the OCR line bbox with an available font; preserve other lines if the omitted layer contains several. Font matching and styles are approximate, and no native PSD text object/font file is returned.

## 4. Transparent images: isolate the subject and specify alpha-sensitive details

**Text to transparent product asset:**

```text
独立的红色陶瓷茶壶产品素材，完整呈现壶嘴、壶盖和把手，不裁切主体。
只保留茶壶和壶底柔和的半透明接触投影，主体及投影之外完全透明。
不要桌面、场景、背景色板、棋盘格或文字。
```

**Ordinary RGB reference to transparent cutout:**

```text
只提取图1左侧的红色马克杯，完整保留杯身和把手、原颜色、形状与材质。
移除花瓶、柠檬、桌面及其他背景，杯子以外完全透明，不增加新物件或文字。
```

Use `generate` / `edit` with **`--background transparent --output-format png`**. No pre-cut alpha input is needed. For a clean sticker, remove the shadow requirement. For glass or gauze, explicitly describe interior transmission and edge/refraction requirements, then validate them; alpha output alone does not establish real translucency.

For multiple references, identify the subject from each image and place them independently without overlap on **one transparent canvas**. A normal request still returns one image; use separate calls or decomposition for separate downloadable assets. Sprite sheets are a community use: specify grid, cell order, character scale and no overlap, then slice/register locally. Native output is not a timed animation; frame count and motion continuity need separate checking.

**Check:** decode actual alpha and composite on light/dark backgrounds; inspect hair/edges, halos, shadow softness and subject fidelity. The measured glass image had a transparent exterior but fully opaque interior despite the request. Partial-alpha edge pixels do not prove that glass transmits a new background.

## Multi-reference role assignment

State each reference's role explicitly in upload order:

> 图1负责杯子和花瓶的形状、颜色与材质，图2负责海报布局。把产品放进图2右下角，保持图2所有文字和背景。产品尺寸合理、透视统一，左侧窗光与接触阴影一致。

Inspect identity, count, scale, perspective, contact shadows and protected lettering separately from visual polish. Names of camera/material/style conventions are guidance, not exact render controls.

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
