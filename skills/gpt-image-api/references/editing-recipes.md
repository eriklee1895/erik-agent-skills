# GPT Image 2.5 editing recipes

Number every input and state its one role. Start with one requested change, then
list only acceptance-critical invariants. Use the previous approved output for a
small next edit; return to the approved base for a consolidated pass when drift
accumulates.

## Replace or remove one object

```text
Image 1: edit target and final canvas.
Change: [replace/remove] only [precisely identified object and location] [with replacement details].
Preserve: Keep every other object, subject identity, geometry, text, crop, camera angle, lighting direction, shadows, reflections, and color balance unchanged.
Integration: Match surrounding perspective, occlusion, material response, texture, and depth of field.
Avoid: no new objects, composition change, relighting, restyling, text, or watermark.
```

## Replace or localize text

```text
Image 1: edit target and final canvas.
Change: Replace only "[OLD COPY]" with "[NEW COPY]" exactly once.
Typography: Preserve the original text box, line count, alignment, hierarchy, font character, weight, color, tracking, and baseline unless [explicit exception].
Preserve: Keep all images, logos, borders, remaining text, spacing, crop, texture, and colors unchanged.
Avoid: no duplicate words, translation of other text, invented copy, layout reflow, or watermark.
```

## Identity-preserving composite

```text
Image 1: base scene and final canvas.
Image 2: identity and clothing reference for the person to insert.
Change: Place the person from Image 2 [pose/action/location] in Image 1.
Preserve person: facial structure, skin tone, apparent age, hairstyle, expression, body proportions, clothing construction, colors, and accessories.
Preserve scene: camera angle, crop, architecture, existing objects, and visual style from Image 1.
Integration: Match perspective, scale, light direction, color temperature, ground contact, occlusion, and shadow softness.
Avoid: no face redesign, clothing change, extra people, extra limbs, text, or watermark.
```

## Product placement or multi-reference composition

```text
Image 1: base scene and final canvas.
Image 2: exact product reference; transfer identity and geometry only.
[Image 3: material/style reference; transfer only [specified traits].]
Change: Place the product from Image 2 at [location and orientation] in Image 1.
Preserve product: silhouette, proportions, construction, label spelling, logo placement, material, finish, and color.
Preserve scene: [critical objects], framing, perspective, light source, and background.
Integration: Add physically plausible contact, reflection, occlusion, and shadow matching Image 1.
Avoid: no product redesign, duplicate product, label mutation, scene replacement, or watermark.
```

## Lighting, weather, or time-of-day change

```text
Image 1: edit target and final canvas.
Change: Change only the lighting and atmosphere to [time/weather/lighting setup].
Visible effects: [key-light direction], [shadow behavior], [sky or practical-light changes], [surface reflections], [air or precipitation].
Preserve: Keep people, faces, objects, architecture, geometry, text, camera angle, crop, and material identities unchanged.
Avoid: no object removal/addition, structural change, style transfer, face change, extra text, or watermark.
```

## Sketch or layout to finished rendering

```text
Image 1: composition and geometry reference; preserve its arrangement and proportions.
[Image 2: material/style reference; transfer only palette, material language, and rendering treatment.]
Change: Render Image 1 as a finished [photo/architectural visualization/illustration/product render].
Preserve: exact object count, placement, silhouette, perspective, negative space, and camera crop from Image 1.
Finish: [materials], [lighting], [surface detail], [depth of field], [palette].
Avoid: no new structural element, changed viewpoint, altered proportions, text, or watermark.
```

## Outpaint or change aspect ratio

```text
Image 1: protected original image centered within the new [width:height] canvas.
Change: Extend only beyond the original boundaries to create [new framing and surrounding content].
Preserve: Keep every original pixel-region subject, face, object, text, geometry, color, and lighting unchanged.
Extension: Continue perspective, horizon, textures, lighting, depth of field, and repeating structures naturally into the added area.
Avoid: no scaling or cropping of the original content, duplicated subject, new focal point, extra text, or watermark.
```

## Consolidated drift-reset edit

```text
Image 1: last approved clean base and final canvas.
[Images 2..N: references for explicitly named identities, products, or materials only.]
Apply these settled changes in one pass:
1. [change one]
2. [change two]
3. [change three]
Preserve: [complete invariant list copied from the approved base acceptance criteria].
Avoid: all intermediate artifacts, accumulated texture changes, altered small text, identity drift, composition drift, or watermark.
```
