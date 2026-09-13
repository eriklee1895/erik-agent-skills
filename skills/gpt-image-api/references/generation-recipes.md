# GPT Image 2.5 generation recipes

These are original, parameterized briefs distilled from OpenAI guidance and the
evidence-labeled community patterns in [community-practices.md](community-practices.md).
Replace bracketed fields, delete irrelevant lines, and send the resulting prompt
verbatim. Start with Flare; choose Sunburst for difficult typography, dense
layouts, identity-sensitive work, or final campaign assets.

## Product hero

```text
Deliverable: [placement and aspect ratio] hero image for [brand/product context].
Primary request: One [product], with [defining geometry/material/label] clearly visible.
Composition: [camera height and angle]; product in [frame position]; negative space in [area] for downstream layout.
Lighting and color: [key-light direction and softness]; [palette]; realistic contact shadow.
Material behavior: [matte/gloss/translucent/fabric] with [specific reflections or texture].
Text (exact): Render "[COPY]" exactly once on [location], [typography description].
Avoid: no duplicate product, invented accessories, extra text, logo, signature, or watermark.
```

## Exact-text poster or social card

```text
Deliverable: [ratio] [event/campaign] poster.
Visual concept: [one concrete graphic device or subject].
Layout: [grid, margins, hierarchy, subject placement].
Text (exact):
- "[HEADLINE]" exactly once, [case], [line count], [font character], at [location].
- "[SECONDARY COPY]" exactly once, smaller, at [location].
Color and medium: [palette]; [print/editorial/photographic/3D] treatment.
Avoid: no additional letters, numbers, fake logos, signatures, or watermark.
```

## Editorial or article illustration

```text
Deliverable: [cover/inset/divider] illustration for an article about [idea].
Primary request: Show [visible metaphor or concrete moment], not literal interface chrome.
Narrative focus: [single action or relationship the reader should notice first].
Composition: [framing]; [subject placement]; quiet area in [location].
Medium: [paper cut/ink/soft 3D/editorial collage/etc.] described through materials and mark-making.
Lighting and palette: [lighting]; [three-to-five-color palette].
Avoid: no words unless specified, no watermark, no decorative element that changes the meaning.
```

## Character consistency sheet

```text
Deliverable: clean character reference sheet on [opaque/transparent] background.
Character: [age, build, facial structure, skin tone, hair, signature clothing and accessories].
Views: exactly [count] full-body views — [front, three-quarter, profile, back] — evenly spaced at the same scale.
Consistency: identical face, proportions, hairstyle, clothing construction, colors, and accessories in every view.
Expression row: exactly [count] head-and-shoulder expressions — [list].
Style and rendering: [medium], neutral studio lighting, readable silhouette.
Avoid: no redesign between views, no cropped limbs, no extra characters, labels, or watermark.
```

## Technical or educational infographic

```text
Deliverable: [ratio] educational infographic for [audience].
Topic: Explain [system/process/concept] from [start] to [outcome].
Structure: exactly [count] numbered stages arranged [direction]; one connector between adjacent stages; no crossing arrows.
Labels (exact): "[LABEL 1]", "[LABEL 2]", "[LABEL 3]"[, ...], each exactly once.
Visual encoding: [shape/color] means [concept]; [shape/color] means [concept].
Style: clean technical editorial illustration, [background], [line and accent colors].
Accuracy constraints: [relationships, direction, counts, or scale that must be correct].
Avoid: no other text, decorative arrows, fake controls, logos, or watermark.
```

## Transparent asset, icon, or sprite

```text
Deliverable: isolated [asset/icon/sprite] on a genuinely transparent canvas.
Subject: [object/character] with [silhouette, materials, pose, identifying details].
Framing: entire subject visible, centered, [padding percentage] clear padding on every side.
Rendering: [photo/3D/pixel art/illustration], crisp boundary, preserved holes and fine edge detail.
Alpha requirements: clean alpha, no halo, no color fringe, no painted checkerboard, no scenery.
Avoid: no platform, frame, caption, logo, signature, watermark, or invented shadow unless [shadow requirement].
```

## UI concept image

```text
Deliverable: visual concept for a [desktop/mobile] [product] screen, [ratio].
User goal: [one primary task].
Layout: [navigation pattern], [main content regions], [primary action location], generous spacing.
Content hierarchy: [title], [key metric/content], [supporting elements].
Text (exact): only "[short labels]"; render each once and keep all other copy abstract or absent.
Visual language: [surface, radius, border, typography, color tokens].
Avoid: no device frame, browser chrome, status bar, fake logo, watermark, or dense body copy.
Note: treat this as ideation; rebuild production UI with deterministic code and accessibility checks.
```
