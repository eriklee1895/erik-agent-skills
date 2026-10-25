# Prompt recipes from the 2026-10-25 study

Evidence: [120-request report](../evals/comprehensive-benchmark.md), [per-sample results](../evals/comprehensive-results.json). Pro is always the default unless the user explicitly selects Flash or authorizes replacing Pro with a faster/lower-cost model. A draft, style preset or batch request alone does not change the model.

These are starting points and inspection criteria, not hard model guarantees. The controlled comparisons used two samples per variant/model. Keep the user's actual subject/style rather than copying the test objects into unrelated tasks.

## 1. Local edits: use the smallest clear instruction

For a single obvious target, this worked in both models:

```text
把图1左侧红色杯子改为深蓝色。
```

For overlapping objects or a scope that must be made explicit, add a region and name what stays:

```text
把图1 <bbox>100 350 550 780</bbox> 中左侧红色杯子改为深蓝色，
杯子外形和把手不变。右侧花瓶、顶部NOVA文字、所有位置和米色背景保持不变。
```

The eight paired samples retained the other objects under both recipes. Longer wording did not consistently reduce outside-box RGB error. Coordinates communicate intent; a generative edit can still alter pixels elsewhere. Use a real mask/compositing workflow downstream if exact pixel preservation is required.

## 2. Exact text and operation language

Chinese and equivalent English operation instructions both replaced NOVA with 星野 correctly in all eight A/B samples. Use the clearest language, quote the literal replacement and state which old text disappears:

```text
把图1顶部标题NOVA替换为中文“星野”，只出现“星野”一次，不保留NOVA。
保持标题位置、左对齐、深蓝色粗无衬线风格，其他物体不变。
```

Check **spelling, duplication, location and weight separately**. In the tested Pro outputs, correct Chinese characters still came with lighter-than-requested lettering under both languages. If a specific font/weight is a delivery requirement, inspect it or typeset the final text after generation; more English is not an established repair.

## 3. Marker edits: inspect cleanup, keep an outline option

When the target is already known by coordinates, native prompt tags avoid adding colored pixels. For a visual marker workflow, an outline-only option was tested successfully:

```bash
uv run scripts/seedream_image_gen.py edit --reference-image source.png \
  --marker-rect '10%,35%,45%,43%' --marker-alpha 0 \
  --prompt '把红框内杯子改为深蓝色，保留形状和把手，框外内容不变，移除全部标记。'
```

Flash retained pink fill in its first two main samples, but both new filled controls and both outline samples were clean. Pro cleaned both styles. This supports checking marker residue and keeping alternatives; it does not prove alpha 0 always beats alpha 80. The CLI's established marker default is unchanged. After residue, return to the original unmarked image for a new intentional edit instead of stacking another annotation over a flawed output.

## 4. Wide covers: describe one continuous scene and the whole footprint

“Product on the right, left 60% empty” allowed encroachment and once produced a hard white panel. The paired recipe moved the product farther right:

```text
一张横向连续的真实产品摄影封面。同一暖米色墙面和桌面自然延续贯穿整个画面，
左侧至少60%是干净的同场景留白。将青绿色鹅颈咖啡壶整体缩小，
把壶嘴、壶身、把手和阴影全部放在画面最右侧35%以内，完整不裁切。
柔和自然窗光。不要白色遮挡板、拼贴、分栏、分割线或局部照片窗口。
```

The revised Flash samples visually met the clear-area criterion; Pro's were close but still slightly short. All new controls also avoided the earlier white panel. Inspect the complete silhouette and shadow before adding a heading. Exact percentages remain a layout requirement to verify, not guaranteed coordinates; use deterministic placement/composition when the safe area must be exact.

## 5. Infographics: semantics first, renderer-like tokens optional

Start with the content and visible arrangement:

```text
3:4竖版信息图，绿树街道真实摄影为底图。顶部居中标题“城市慢行”。
四张白色半透明毛玻璃卡片按2乘2排列，可以透过卡片看到背景。
左上“步行 35%”，右上“骑行 25%”，左下“公交 30%”，右下“其他 10%”。
深蓝色清晰文字，每项只出现一次，不加其他文字、图表或图标。
```

Both this approach and the longer camera/CSS/position recipe produced correct text and translucent cards in all eight samples. Camera names, rgba, blur pixels and border radii are optional visual metaphors, not API renderer controls. Neither length guarantees contrast: some dark titles landed over dark foliage. Inspect the actual heading background; for a repair, move the heading to a calm light area or request a light title band. That repair direction was not separately A/B-tested here.

## 6. Style and character inspection

The main study found specific misses despite otherwise attractive pictures. The following are inspection/repair directions; their repair wording was not separately paired in this round:

- **Isometric icons:** verify that the top and two sides are visible. If the result is frontal, describe a view from above/front/side rather than relying on the word `isometric` alone.
- **Character scenes:** check identity cues separately from action, props and contact. “Same robot watering a potted seedling” can keep identity while missing the watering can or pot. Describe visible action relations if needed: hand holds the can, water reaches the soil inside the pot.
- **Book/page metaphors without text:** check for pseudo-print. A repair can name blank unprinted pages explicitly; a generic no-text clause did not prevent every instance.
- **Hand-drawn diagrams:** inspect the causal action and object count separately from pencil texture. A recognizable style can still add glowing eyes or multiple leaves.

Retain useful historical Pro recipes, but do not promote a historical score, font convention or camera phrase into a universal requirement for either model.
