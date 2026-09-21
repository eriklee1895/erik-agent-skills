# Core editing templates

Number every input and give it one role. Use Sunburst when preservation failure invalidates
the result. A generative edit is never a pixel lock; composite deterministically when exact
untouched pixels are required.

## Replace or remove one object

**Use when:** One identifiable object or region should change while the scene stays stable.

**Fixed requirements:** Lock the target, nearby protected objects, composition, text,
camera, and lighting unless the requested change logically requires one exception.

**Creative latitude:** Infer seams, fill texture, contact, occlusion, and physically
plausible integration inside the authorized region.

```text
Image 1: edit target and final canvas.
Change: [replace/remove] only [precisely identified object and location] [with replacement details].
Preserve: every other object, identity, geometry, text, crop, camera angle, lighting direction, shadows, reflections, and color balance.
Integration: match surrounding perspective, material response, texture, occlusion, and depth of field.
Avoid: new objects, composition change, global relighting, restyling, extra text, or watermark.
```

**Visual QA:** Compare the target and all protected regions before/after; inspect seams,
supporting shadows, repeated textures, and accidental object loss.

**Evidence/status:** Official single-change pattern from the [GPT Image 2.5 editing examples](https://developers.openai.com/api/docs/guides/image-prompting), reinforced by community preservation workflows.

## Conservative restoration or detail recovery

**Use when:** A low-resolution, compressed, noisy, or mildly blurred image should become
clearer without changing its documented content.

**Fixed requirements:** Lock the source composition, object count, identity, geometry,
colors, lighting, and any supplied text. Treat the source as evidence, not an invitation
to invent unsupported detail.

**Creative latitude:** Reconstruct only strongly supported edges, texture, and local
contrast; choose restrained denoising and sharpening appropriate to the source.

```text
Image 1: low-resolution source image and final canvas.
Change: conservatively reduce [compression/noise/blur] and recover supported detail.
Preserve: exact composition, object count, identity, geometry, colors, lighting, and text.
Avoid: redesign, beautification, invented objects or letters, halos, oversharpening, or watermark.
```

**Visual QA:** Compare against the source at the same crop; inspect object identity,
edges, small text, textures, and whether “recovered” detail is actually invented.

**Evidence/status:** Community restoration pattern; one local Sunburst check improved a
512×341 derivative while preserving the scene, but this is not lossless restoration.

## Replace or localize text

**Use when:** Existing in-image copy must be replaced or translated without redesigning it.

**Fixed requirements:** Lock exact old/new strings, occurrence count, non-target text,
text box, hierarchy, line count, alignment, and surrounding imagery.

**Creative latitude:** Adjust micro-kerning or line fit only when required by the new copy
and consistent with the original design.

```text
Image 1: edit target and final canvas.
Change: replace only "[OLD COPY]" with "[NEW COPY]" exactly [count] time(s).
Typography: preserve the original text box, hierarchy, font character, weight, color, alignment, and baseline; authorize only [necessary fit adjustment].
Preserve: all images, logos, borders, remaining text, spacing, crop, texture, and colors.
Avoid: duplicate words, untranslated target text, changes to other copy, invented copy, broad reflow, or watermark.
```

**Visual QA:** Compare every character, count occurrences, search for leftover source-language
text, and check line breaks, spacing, hierarchy, and non-target copy.

**Evidence/status:** Official [layout-preserving translation](https://developers.openai.com/api/docs/guides/image-prompting) pattern, expanded with explicit QA.

## Identity-preserving composite

**Use when:** A person from one reference must appear naturally in another scene.

**Fixed requirements:** Lock facial structure, skin tone, age, hair, expression, body
proportions, clothing if requested, and the base scene's camera and protected objects.

**Creative latitude:** Choose a natural pose, gaze, micro-expression, and integration
details consistent with the requested action.

```text
Image 1: base scene and final canvas.
Image 2: identity [and clothing] reference for the person to insert.
Change: place the person from Image 2 [pose/action/location] in Image 1.
Preserve person: facial structure, skin tone, apparent age, hairstyle, expression, proportions, and [locked clothing/accessories].
Preserve scene: camera angle, crop, architecture, protected objects, and visual character from Image 1.
Integration: match perspective, scale, light direction, color temperature, ground contact, occlusion, and shadow softness.
Avoid: face redesign, extra people or limbs, clothing change unless authorized, extra text, or watermark.
```

**Visual QA:** Compare identity against the source at similar scale; inspect anatomy,
hands, feet, ground contact, light, occlusion, and whether scene objects drifted.

**Evidence/status:** Official identity insertion/preservation pattern from the [GPT Image 2.5 guide](https://developers.openai.com/api/docs/guides/image-prompting).

## Clothing try-on with multiple references

**Use when:** A person's clothing should be replaced from one or more garment references.

**Fixed requirements:** Lock identity, expression, pose, body geometry, background,
camera, and each garment's construction, material, colors, and visible branding.

**Creative latitude:** Resolve realistic fit, folds, tension, layering, and occlusion while
respecting the body and garment references.

```text
Image 1: person, identity, pose, body geometry, and final canvas.
Images 2..N: garment references, one garment role per image.
Change: replace only the clothing with the referenced garments, fitted naturally to Image 1's existing pose and body.
Preserve: face, skin tone, age, hair, expression, body shape, pose, hands, background, camera angle, and crop.
Garments: preserve construction, length, pattern, material, closures, colors, and [logo policy].
Integration: realistic fabric folds, layering, contact, shadows, and color temperature.
Avoid: accessories not supplied, body reshaping, pose change, identity drift, extra text, or watermark.
```

**Visual QA:** Check face and body identity first, then garment construction, pattern
continuity, hands, layering, folds, closures, and background preservation.

**Evidence/status:** Adapted from OpenAI's official multi-reference clothing example; the prompt requests preservation but cannot guarantee pixel identity.

## Product placement or multi-reference composition

**Use when:** A referenced product or object must be integrated into a base scene.

**Fixed requirements:** Lock product silhouette, proportions, label spelling, logo policy,
material, finish, and the base scene's protected composition.

**Creative latitude:** Choose final orientation and integration details when not prescribed,
including contact, reflections, and plausible shadowing.

```text
Image 1: base scene and final canvas.
Image 2: exact product reference; transfer identity and geometry only.
[Image 3: material/style reference; transfer only the named traits.]
Change: place the product from Image 2 at [location, scale, and orientation] in Image 1.
Preserve product: silhouette, proportions, construction, label spelling, logo placement, material, finish, and color.
Preserve scene: [protected objects], framing, perspective, light source, and background.
Integration: physically plausible contact, reflection, occlusion, and shadow matching Image 1.
Avoid: product redesign, duplicate product, label mutation, scene replacement, extra text, or watermark.
```

**Visual QA:** Compare product geometry and every label character, then inspect scale,
perspective, contact, reflections, occlusion, and scene drift.

**Evidence/status:** Official multi-reference composition practice plus product-preservation constraints from the current local workflow.

## Background replacement

**Use when:** Keep the foreground subject while replacing the entire environment.

**Fixed requirements:** Lock subject identity, silhouette, position, scale, camera angle,
edges, product text, and any protected foreground objects.

**Creative latitude:** Design the requested new environment and authorize only the minimum
relighting needed to integrate the subject.

```text
Image 1: foreground subject, edit target, and final canvas.
Change: replace only the background with [complete new environment].
Preserve: subject identity, silhouette, position, scale, angle, fine edges, labels, and protected foreground objects.
Relighting: [none / allow only specified rim light, reflections, and contact shadow] to match the environment.
Integration: consistent perspective, horizon, depth, color temperature, reflections, and edge spill.
Avoid: subject redesign, crop change, invented props touching the subject, altered text, or watermark.
```

**Visual QA:** Inspect hair and product edges, spill, depth, horizon, contact shadow,
reflections, subject color drift, and preserved labels.

**Evidence/status:** Original bounded-edit scaffold derived from official change/preserve guidance and production background-replacement practice.

## Lighting, weather, or time-of-day change

**Use when:** Environmental conditions should change without changing scene geometry.

**Fixed requirements:** Lock subjects, faces, object count, architecture, geometry, text,
camera, and crop.

**Creative latitude:** Choose physically plausible atmospheric detail, practical lights,
surface reflections, precipitation, and color temperature within the requested condition.

```text
Image 1: edit target and final canvas.
Change: change only the lighting and atmosphere to [time/weather/lighting setup].
Visible effects: [key-light direction], [shadow behavior], [sky/practical lights], [reflections], [air or precipitation].
Preserve: people, faces, objects, architecture, geometry, text, camera angle, crop, and material identities.
Avoid: object removal/addition, structural change, style transfer, face change, extra text, or watermark.
```

**Visual QA:** Verify scene geometry and identities, then check consistent light direction,
shadow density, reflections, atmosphere, and believable weather interaction.

**Evidence/status:** Official one-condition iterative-edit pattern from the [GPT Image 2.5 guide](https://developers.openai.com/api/docs/guides/image-prompting).

## Role-bounded style transfer

**Use when:** A reference should control visual medium, palette, or mark-making without
transferring its subject or composition.

**Fixed requirements:** Lock the new subject and scene, and explicitly list which style
traits may transfer and which reference content must not transfer.

**Creative latitude:** Interpret the allowed palette, texture, brushwork, edge quality,
and material language for the new subject.

```text
Image 1: style reference only; transfer [palette/texture/medium/line quality] and nothing else.
[Image 2: subject or composition reference, if needed, with its separate role.]
Primary request: render [new subject and scene] using only the named style traits from Image 1.
Preserve: [identity/geometry/layout requirements from the task].
Avoid: copying Image 1's people, objects, text, logo, composition, or unrelated motifs; no watermark.
```

**Visual QA:** Confirm the desired style traits transferred, reference subjects did not,
and the requested new subject, composition, and protected identity remain correct.

**Evidence/status:** Official role-labeled style-transfer pattern; wording is an original bounded adaptation.

## Sketch or layout to finished rendering

**Use when:** A drawing, wireframe, or layout should become a finished visual without
losing its geometry.

**Fixed requirements:** Lock object count, placement, silhouette, proportions,
perspective, negative space, and camera crop from the source drawing.

**Creative latitude:** Select plausible materials, lighting, surface detail, palette,
and final rendering medium consistent with the requested result.

```text
Image 1: composition and geometry reference; preserve its arrangement and proportions.
[Image 2: style/material reference; transfer only named treatment.]
Change: render Image 1 as a finished [photo/architectural visualization/illustration/product render].
Preserve: exact object count, placement, silhouette, perspective, negative space, and crop.
Finish: [materials], [lighting], [surface detail], [depth of field], and [palette].
Avoid: new structural elements, changed viewpoint, altered proportions, extra text, or watermark.
```

**Visual QA:** Overlay or compare the source geometry, then inspect material coherence,
lighting, perspective, and any invented structural content.

**Evidence/status:** Official sketch-to-render pattern from the current OpenAI image prompting guide.

## Outpaint or change aspect ratio

**Use when:** Extend beyond an existing image to a new canvas without redesigning the
original center.

**Fixed requirements:** Lock the original subject, text, geometry, color, and placement;
define the new canvas ratio and which edges may extend.

**Creative latitude:** Invent only the continuation outside the original bounds while
matching perspective, texture, horizon, light, and depth.

```text
Image 1: protected original image placed within a new [width:height] final canvas.
Change: extend only beyond [named boundaries] to create [new framing and surroundings].
Preserve: every original-region subject, face, object, text, geometry, color, and lighting.
Extension: continue perspective, horizon, textures, light, depth of field, and repeating structures naturally.
Avoid: scaling/cropping the original content, duplicated subjects, a new competing focal point, extra text, or watermark.
```

**Visual QA:** Compare the original-region content, inspect boundary seams, repeated
patterns, horizon and light continuity, duplicate subjects, and final composition.

**Evidence/status:** Community production pattern aligned with official preservation guidance; exact unchanged pixels require deterministic compositing.

## Consolidated drift-reset edit

**Use when:** Several approved edits have accumulated drift and should be reapplied from
the last clean base in one authorized pass.

**Fixed requirements:** Use the named clean base, enumerate only approved changes, and
repeat the complete invariant list.

**Creative latitude:** Resolve interactions among approved changes, but do not reinterpret
the overall composition or art direction.

```text
Image 1: last approved clean base and final canvas.
[Images 2..N: references for explicitly named identities, products, garments, or materials only.]
Apply these settled changes in one pass:
1. [approved change one]
2. [approved change two]
3. [approved change three]
Preserve: [complete invariant list copied from the approved base acceptance criteria].
Avoid: intermediate artifacts, texture softening, altered small text, identity drift, composition drift, or watermark.
```

**Visual QA:** Compare against both the clean base and the last approved intermediate;
verify all approved changes, identity, small text, texture, and composition.

**Evidence/status:** Community iterative-editing pattern recorded in [`community-practices.md`](../../references/community-practices.md); locally plausible but not a pixel-preservation guarantee.
