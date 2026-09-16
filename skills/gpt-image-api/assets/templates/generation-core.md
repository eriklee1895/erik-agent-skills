# Core generation templates

Load this asset only for a sparse brief or one of the deliverables below. Replace or
remove every bracketed field. The scaffold is a starting point, not required wording.

## Natural editorial photograph

**Use when:** The result should feel candid, documentary, or naturally photographic.

**Fixed requirements:** Preserve the requested subject, action, location, body framing,
and any factual setting. Do not invent identity from text alone.

**Creative latitude:** Choose a plausible viewpoint, lens character, light direction,
texture, and color response unless the user specifies them.

```text
Deliverable: [placement and aspect ratio] natural editorial photograph.
Primary request: [adult subject] doing [action] in [location].
Composition: [body framing and viewpoint]; believable interaction with the setting.
Appearance: real skin, fabric, surface wear, and ordinary environmental detail.
Lighting and color: [natural source and direction], plausible shadows, restrained color.
Avoid: beauty-filter smoothing, staged studio polish, artificial blur, extra text, or watermark.
```

**Visual QA:** Inspect anatomy, hands, skin texture, perspective, contact, light agreement,
and whether the scene looks observed rather than staged.

**Evidence/status:** Adapted from the [official GPT Image 2.5 prompting guide](https://developers.openai.com/api/docs/guides/image-prompting); structure locally reviewed, not a quality guarantee.

## Editorial or article illustration

**Use when:** An article needs a cover, inset, divider, or conceptual editorial image.

**Fixed requirements:** Preserve the article's actual thesis, named objects, requested
format, and any reserved area for editorial layout.

**Creative latitude:** Invent a fitting visual metaphor, medium, palette, mark-making,
and atmospheric treatment when the brief leaves them open.

```text
Deliverable: [cover/inset/divider] illustration for an article about [idea].
Primary request: Show [concrete moment or visual metaphor] so the reader first notices [relationship/action].
Composition: [framing and subject placement], with [reserved area] left quiet if needed.
Medium: [paper cut/ink/soft 3D/collage/etc.] expressed through visible materials and marks.
Lighting and palette: [direction and mood], [palette or agent-selected restrained palette].
Avoid: unrelated symbolism, decorative elements that change the meaning, extra text, or watermark.
```

**Visual QA:** Check that the metaphor communicates the article idea, hierarchy survives
at publication size, and decorative content does not introduce a false claim.

**Evidence/status:** Original 2.5-oriented scaffold informed by OpenAI's deliverable-first and concrete-visual-language guidance; not benchmarked as a fixed style.

## Transparent asset, icon, or sprite

**Use when:** A project needs an isolated raster asset with genuine alpha transparency.

**Fixed requirements:** Keep the requested silhouette, identifying details, padding,
output purpose, and any product label or semi-transparent material.

**Creative latitude:** Choose rendering medium, surface treatment, pose, and subtle internal
lighting when they are not constrained by an existing asset system.

```text
Deliverable: isolated [asset/icon/sprite] on a genuinely transparent canvas.
Subject: [object or character] with [silhouette, pose, material, and identifying details].
Framing: entire subject visible, centered, with [padding] clear space on every side.
Edges: crisp silhouette, preserved holes and fine details, clean alpha, no halo or color fringe.
Avoid: solid backdrop, checkerboard, scenery, frame, caption, logo, watermark, or invented shadow unless requested.
```

**Visual QA:** Decode the image and inspect alpha around hair, glass, reflections, holes,
soft shadows, and edge pixels; reject painted checkerboards.

**Evidence/status:** Based on [official transparent-background guidance](https://developers.openai.com/api/docs/guides/image-prompting) and locally exercised native-alpha validation.

## Historical or real-world scene

**Use when:** A scene depends on a real place, date, culture, or period-specific context.

**Fixed requirements:** Lock the verified location, date or era, named event, required
people or objects, and known factual constraints. Do not let the model invent facts.

**Creative latitude:** Choose framing, weather, moment, and photographic or illustrative
treatment when they do not contradict the evidence.

```text
Deliverable: [photo/illustration] of [event or scene] in [place] during [date or era].
Primary request: [visible action and subjects].
Period requirements: [clothing, architecture, tools, transport, signage, staging].
Composition: [viewpoint and scale] emphasizing [historically relevant focus].
Style and light: [documentary/photo/illustration treatment], [plausible conditions].
Avoid: anachronisms, modern objects, invented insignia, unsupported claims, extra text, or watermark.
```

**Visual QA:** Check clothing, props, built environment, signs, technology, and staging
against the stated period; treat the image as an illustration, not evidence.

**Evidence/status:** Official pattern from [OpenAI's historical-context example](https://developers.openai.com/api/docs/guides/image-prompting); facts still require external verification.

## Game environment or standalone game asset

**Use when:** The deliverable is concept art, a gameplay environment, a tileable texture,
or a standalone raster asset for a game pipeline.

**Fixed requirements:** Lock gameplay function, camera convention, required landmarks,
asset boundaries, repeatability or transparency, and technical consumption constraints.

**Creative latitude:** Invent worldbuilding details, atmosphere, materials, lighting,
palette, and focal storytelling within those gameplay constraints.

```text
Deliverable: [environment concept/gameplay backdrop/tileable texture/standalone asset] for [game context].
Primary request: [biome, scene, material, prop, or character asset].
Gameplay constraints: [camera angle, navigable zones, landmarks, silhouette, tiling, padding, alpha].
Composition: [establishing/top-down/side view], with [focal point and readable routes].
Rendering: [realistic/stylized/pixel art/painted], [materials and lighting].
Avoid: unusable perspective, hidden routes, seams for tileable output, text, logos, or watermark.
```

**Visual QA:** Inspect silhouette, gameplay readability, camera consistency, tiling seams
or alpha edges, and whether decorative detail obscures the asset's function.

**Evidence/status:** Selective adaptation of asset-type practices from the community [template taxonomy](https://github.com/freestylefly/awesome-gpt-image-2/blob/main/docs/templates.md); not copied from a gallery prompt.
