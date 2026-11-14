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

**Drift over long chains is cumulative.** Independent measured runs (Segmind's 12-round sneaker chain, OmniArt's 10-round café chain) find the protected frame darkens gradually — roughly half an RGB level per round, invisible early but extrapolating to a visible exposure shift by round 50–100, alongside blotchy shadows at full resolution. Mitigations: keep chains short and branch variants from a master; on long chains attach the accepted master as an additional reference each round (an extra input charge) to re-anchor identity and exposure; compare every round against the original, not only the previous frame. In auto/aspect edit modes the output can also come back a few pixels larger than the source — resize round 1 before any pixel diffing or compositing.

**Anchor cadence and chain discipline.** Community consensus from 10-, 12- and 20-round measured chains: treat 10–15 rounds as the lookback window — schedule an explicit master re-anchor (resend the accepted master as a reference) within that window, and hard-restart from the master instead of stacking corrective prompts once drift appears. Keep every intermediate file; a failed round returns to the last checkpoint under the no-auto-replay rule. Never route chain intermediates through JPEG: a live single-round comparison measured protected-region MAE rising from 1.07 to 1.80 and the changed-`>8`-pixel fraction from 0.25% to 1.39% after one quality-90 JPEG transit, because compression artifacts are treated as image content on the next edit. The CLI now warns when an edit/reference call requests JPEG output; use PNG for intermediates and export JPEG only for final delivery.

**Acceptance QC between rounds.** On same-size, same-color-space lossless pairs: stack the previous and new output with a difference blend (black = identical), first mask out the region this round was allowed to change plus its expected reflections/shadows, then investigate any remaining bright clusters. Separately sample the mean RGB of a fixed untouched patch each round to catch exposure creep early, and always assert the target actually changed — a no-op can score a perfect protected-region similarity. JPEGs and screenshots cannot be diffed reliably because compression and misalignment light up the whole frame.

**Coordinate grammar from the official editing guide.** The 5.5 editing contract inherits the 5.0 interactive-edit patterns, all using prompt tags on the 0–999 scale (never the 0–1000 response-box scale):

- Multi-subject box: when a `<bbox>` contains several objects, name the target inside it — “把图1 `<bbox>120 180 640 760</bbox>` 区域内左侧的人物换成机器人”.
- Keep-unchanged box: mark protected regions with their own box — add “图1 `<bbox>700 120 920 360</bbox>` 区域保持不变”.
- Cross-image placement: “将图1 `<bbox>…</bbox>` 的主体放到图2 `<bbox>…</bbox>` 位置”, disambiguating which image and which box.
- `<point>x y</point>` leaves the affected area to the model; `<bbox>` is the more controlled option for fixed-layout work.

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

## Community prompt patterns

Distilled from BytePlus Lumina's official how-to and independent hands-on runs (OmniArt 10-round chain, Huashu 20-round sticker test, AIPick spot edits); consistent with this skill's measured benchmark:

- **Five-part generation formula**: image type/job first → subject with one or two must-keep details → real setting with named light source/direction/time → camera/lens/framing/DoF using short technical words → settings (ratio, tier, background). Describe visible outcomes ("fine natural skin texture, blemishes removed, no smoothing") instead of abstract quality words ("better skin", "premium").
- **Exact text**: put every string in quotes with role (headline/subhead/caption), weight, color, alignment and reading order; dense unquoted copy is the dominant garbled-text failure. Proof at 100% and at display size.
- **RGBA trigger phrases that work**: "transparent background", "PNG with a transparent background", "no background", "alpha channel", plus explicit exclusions ("no backdrop, no surface, no checkerboard"). Set `background: transparent` regardless; wording alone does not switch modes.
- **Self-contained edit rounds**: write each round as if the model has no memory — "Use image 1 as the current frame. Change only one thing: X. Keep everything else — list the objects, light direction and framing — exactly as in image 1." Never refer to "the thing added last round". To restore something an earlier round covered, attach the original accepted image as a second reference instead of describing history.
- **Branching, not repairing**: for independent colorways, languages or markets, branch each from the same accepted master; do not chain unrelated variants. If drift appears, return to the last checkpoint rather than prompting corrective edits on top of drift.
- **Sticker/keylines**: thin 1 px white outlines blur away at 1.5K — render sticker sheets at 2K and proof partial-alpha elements (wings, gauze, steam) on both light and dark layouts.
- **Hard edges are reliable; soft edges need inspection**: packaging, bottles and electronics cut out cleanly; hair, fur, wispy steam and glass interiors remain case-by-case. Partial-alpha pixels usually live at edges and contact shadows — their presence does not prove the glass itself transmits a new background.
- **Localization discipline**: derive every language market from the same accepted original, never chain-translate previous markets; lock brand and packaging lettering with an explicit "do not translate or redraw this lettering" instruction, and add a duplicate-slogan proofing step — a measured failure rendered one slogan twice in different sizes. For invariant labels, use the OCR-line-bbox local typesetting path instead of regenerative editing.
- **Sprite/sticker sheets in two stages**: first generate the character or element as a transparent PNG master, then one grid-based sheet prompt (cell count, reading order, consistent scale, no overlap) at 2K because thin 1 px keylines blur away at 1.5K; request a no-shadow variant and add shadows in layout, then slice the single output locally and verify frame continuity separately.
- **Production cost logging**: the CLI metadata keeps raw `usage`; per-attempt list cost is inputs × 0.05 plus each output's tier (0.13 at ≤2.61MP, 0.23 above), with decomposition layers tiered independently. Log the cost of the usable asset including rejected and re-reviewed attempts rather than treating the headline per-image price as the unit cost.
- **Three-version retention**: keep the original source, the accepted key visual and the final deliverable as named artifact classes, with branch points for variants; this pairs with the no-auto-replay checkpoint rule so a failed round returns to a known master instead of spending on corrective generations.

Troubleshooting map (community + measured):

| Symptom | Fix |
|---|---|
| Edit spills into surrounding pixels | Add an explicit keep list (object edges, shadow, crop); change only one thing per round. |
| White/colored box behind a "transparent" export | Use explicit transparent mode and alpha-channel wording, never "transparent look" or auto alone; inspect on a dark layout. |
| Garbled small text | Quote every line including line breaks, state size/reading order, render at 2K, proof at 100%. |
| Identity drift across rounds | Fix three named features in the keep list, repeat the same lighting words, attach the reference again. |
| Plastic/waxy skin | Name the light source and direction; ask for visible pores and soft shadow, drop "perfect skin". |
| Layer rebuild looks like paper cut-outs | Fog/steam never gets a layer and shadows may be dropped; repaint atmosphere manually rather than re-splitting. |

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

The [Seed team's launch article](https://seed.bytedance.com/zh/blog/more-realistic-images-more-stable-editing-across-100-rounds-introducing-seedream-5-5?view_from=content_recommend) reports its own preference/text-corruption evaluations (severe text corruption 0.4%, minor 1.7%, realism image-edit GSB +55.62%) and 100-round examples. Those are vendor evaluations, distinct from this skill's measured sample. Third-party “3K/4K” claims conflict with the documented Ark native range; use the official API contract.

## Second live verification pass (2026-11-14)

A separate verification session against the live Ark endpoint combined a direct field/error/boundary probe matrix with paid CLI calls covering edit chains, transparency, decomposition, fusion and outpaint. New evidence beyond the benchmark above:

- **Three-round edit chain on a dense 2K poster all succeeded**: bbox calligraphy title swap ("秋日咖啡节"→"冬日红茶节"), a chained small-print price edit ("88/118"→"68/98"), and a visible-marker badge edit ("CAFÉ"→"THÉ" with accented glyph). Layout, cup, leaves and protected copy stayed intact; round three removed its marker cleanly.
- **Transparent outputs**: text-only logo (83% fully transparent pixels), RGB-poster cup cutout including steam (88%), and a glass of water. The glass prompt explicitly demanded see-through transmission and refraction; interior alpha then contained real partial-alpha regions (sampled means around 210–240/255) and the dark-background composite visibly transmits — an improvement over the benchmark's opaque-interior glass, but still not uniform physical transparency.
- **Decomposition of the same poster** (max_images 20 + OCR) returned one base plus nine semantic layers (badge, calligraphy title, subtitle, four-line info block, board, cup, three leaf groups). Typeset layers carried OCR with font matches (`Times New Roman`, `汉仪中宋`); the brush calligraphy and the circular emblem got names/descriptions but no OCR, reconfirming the regular-text limit.
- **Probe results**: `n`, `seed`, `mask` and unknown fields are silently ignored with HTTP 200 (never rely on them); `tools`, `sequential_image_generation`, `stream`, `fast` mode, `webp`, `3K`, bad enums and out-of-range sizes return 400 naming the parameter; `response_format: b64_json` returns inline PNG bytes for ordinary generation and also works per layer in decomposition (a seven-item split returned all items as inline b64 with z-index, bbox and OCR intact); the legacy 5.0 Pro model id still serves 5.0 images directly, which the CLI guard prevents by design.
- **Layer splitting is nondeterministic by design**: two identical decomposition requests on the same poster both returned eight outputs but with different groupings (one merged cup and tray, the other split them) and reworded `name` strings — key downstream logic on `z_index`/`bounding_box`, not names. Naming more elements than `max_images` allows does not error: a prompt naming 12 elements with cap 6 returned six outputs, the rest merged into the base or dropped.
- **Compliance field enforcement**: the server rejects `safety_identifier` over 64 characters with 400 but accepts whitespace inside a token; the CLI applies a stricter local ASCII/no-whitespace policy and never persists the value.
- **Outpaint** now preserves exact padded dimensions while they fit the pixel contract (1024² + 200 px returned an exact 1224×1024 image); padding outside the 921,600–4,624,220 pixel window or beyond aspect 16:1 falls back to tier sizing with an explicit warning, including padded canvases below the pixel floor.

Additional firsthand sources consulted in this pass:

| Source | Useful test hypothesis / workflow | Qualification |
|---|---|---|
| [OmniArt hands-on, 2026-11-12](https://omniart.studio/blog/models-insights/seedream-5-5-hands-on-test) | 10-round one-change chain; wall patch darkened ~5% by round 10 while 5.0 drifted cyan; glass body stays opaque while edges alpha correctly; keep every intermediate. | One run per brief, 1440p wrapper caps. |
| [ttqq.dev Huashu 20-turn test](https://ttqq.dev/en/tool/huashu-selfie-sticker-seedream-animated-gif/) | Identity held to turn 20 (SSIM 0.983–0.995); self-contained prompts; attach original as second reference to restore; open-source sprite-slicing sticker skill. | Third-party repo without a LICENSE file. |
| [BytePlus Lumina how-to](https://ai.byteplus.com/lumina/en/image/how-to-use-seedream-5-5) | Five-part prompt formula, troubleshooting table, RGBA trigger wording and dark/light proofing. | Official overseas-platform guidance; wrapper UI labels differ from Ark fields. |
| [ComfyUI partner node (merged 2026-11-10)](https://github.com/Comfy-Org/ComfyUI/pull/17631) | Premultiplied-alpha layer resize; the node still sends a `seed` field on 5.5 requests but Ark silently ignores it (the skill's own seed probe returned HTTP 200 with one ordinary image), so it has no reproducibility effect; incomplete layer responses fail rather than drop. | Node implementation, not Ark documentation. |
| [AirMore / Promptif 35-run WaveSpeed test](https://airmore.ai/ai-review/seedream-5-review) | Median 25.4 s per image; 3/3 transparent-glass attempts failed to transmit; dense newspaper copy still errors. | Relay platform; small sample. |
