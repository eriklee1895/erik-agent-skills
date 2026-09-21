# Character and series templates

Use a reference image whenever a particular identity must persist. Text descriptions can
define a new character but do not establish an existing person's likeness.

## Character consistency sheet

**Use when:** Establish a reusable character before producing scenes, animation references,
or a visual series.

**Fixed requirements:** Lock defining face, proportions, age, hair, clothing construction,
colors, accessories, view count, and required expressions.

**Creative latitude:** Choose sheet composition, neutral presentation treatment, subtle
lighting, and spacing unless a downstream pipeline fixes them.

```text
Deliverable: clean character reference sheet on [opaque/transparent] background.
Character: [age, build, facial structure, skin tone, hair, signature clothing, accessories].
Views: exactly [count] full-body views — [front, three-quarter, profile, back] — evenly spaced at the same scale.
Consistency: identical face, proportions, hairstyle, clothing construction, colors, and accessories in every view.
Expression row: exactly [count] head-and-shoulder expressions — [list].
Rendering: [medium], neutral light, readable silhouette, clean separation.
Avoid: redesign between views, cropped limbs, extra characters, unintended labels, or watermark.
```

**Visual QA:** Count views and expressions; compare face, body ratios, garment construction,
patterns, colors, accessory placement, scale, and cropped anatomy.

**Evidence/status:** Official recurring-character guidance plus current production character-sheet practice.

## Numbered action or pose contact sheet

**Use when:** A downstream animation, video, dance, sport, or game workflow needs an ordered
set of poses in one image.

**Fixed requirements:** Lock grid dimensions, panel count, numbering order, action sequence,
identity, outfit, scale, background, and whether limbs must stay fully visible.

**Creative latitude:** Design transitional poses, rhythm, weight shift, camera consistency,
and line/rendering treatment within the named action.

For difficult motion, start with an 8-panel (4×2) sheet and inspect continuity before
scaling to 16 panels. This is an iteration heuristic, not a model limit.

```text
Image 1: character identity, outfit, color, and accessory reference.
Deliverable: [rows]-by-[columns] contact sheet showing [ACTION SEQUENCE] in exactly [count] distinct full-body poses.
Order: read left to right, top to bottom; number every cell [range] in its upper-left corner.
Consistency: preserve face, proportions, hairstyle, outfit construction, colors, accessories, camera, and character scale in every cell.
Presentation: [plain background], equal cell sizes, clear separation, full limbs visible.
Avoid: missing/duplicate numbers, repeated poses, cropped anatomy, extra characters, text beyond panel numbers, or watermark.
```

**Visual QA:** Count cells and numbers; verify sequence order, distinct poses, identity,
accessories, garment patterns, anatomy, full limbs, and constant camera/scale.

**Evidence/status:** Source-attributed community adaptation from a [GPT Image 2.5 pose-sheet workflow](https://github.com/wuyoscar/GPT-Image2-Skill/blob/main/skills/gpt-image/references/templates-gpt-image-2.5.md); the structure is useful but not locally benchmarked across actions.

## Multi-camera continuity sheet

**Use when:** A character and location must remain continuous while a shot list explores
several camera positions around the same three-dimensional scene.

**Fixed requirements:** Lock identity, wardrobe, architecture, anchor-object positions,
time, weather, light direction, and spatial relationships across all panels. Vary only
camera position, distance, focal length, and natural micro-pose.

**Creative latitude:** Choose the shot grid, exact framing, lens feel, and restrained
editorial treatment while preserving a continuous moment rather than nine redesigns.

```text
Image 1: character identity and wardrobe reference.
Deliverable: a [rows]-by-[columns] location-scout sheet with exactly [count] shots of the same scene.
Continuity lock: same character, face, outfit, architecture, anchor objects, time, weather, and light direction in every panel.
Shot list: [ordered camera positions, distances, and viewpoints].
Allowed variation: camera position, distance, focal length, and natural micro-pose only.
Avoid: new locations, changed wardrobe, duplicated characters, broken 3D perspective, labels, or watermark.
```

**Visual QA:** Check identity, wardrobe, architecture, anchor-object positions, camera
logic, perspective continuity, shot order, and any accidental scene redesign.

**Evidence/status:** Two local GPT Image 2.5 runs produced coherent 3×3 sheets with both
models; this remains a continuity heuristic, not a guarantee for every cast or scene.

## Continue a character across scenes

**Use when:** An approved character should recur in a new story scene, pose, or page.

**Fixed requirements:** Use the approved character image and repeat defining identity,
proportions, outfit, palette, accessories, personality, and series medium.

**Creative latitude:** Invent the new environment, action, secondary objects, light, and
emotional staging within the story beat.

```text
Image 1: approved character anchor and identity reference.
Primary request: continue the same character in [new scene and action].
Character lock: preserve facial features, proportions, hairstyle, outfit construction, colors, accessories, and [personality cue].
Series lock: preserve [medium, line quality, palette relationship, and rendering density] from Image 1.
Scene: [new environment, action, interaction, and story beat].
Avoid: character redesign, wardrobe change unless requested, duplicate character, style drift, extra text, or watermark.
```

**Visual QA:** Compare the new image with the anchor, not only the previous scene; inspect
face, silhouette, proportions, clothing, accessories, palette, medium, and story action.

**Evidence/status:** Official multi-turn character-consistency pattern from the [GPT Image 2.5 guide](https://developers.openai.com/api/docs/guides/image-prompting).

## Storyboard or comic sequence

**Use when:** A narrative must be expressed in a fixed set of ordered panels or shots.

**Fixed requirements:** Lock panel count, order, characters, continuity objects, actions,
locations, approved text, and the beginning/end state of each beat.

**Creative latitude:** Choose shot scale, angle, staging, transitions, pacing, panel shape,
and emotional emphasis while preserving continuity.

```text
Deliverable: [ratio] [storyboard/comic] with exactly [count] ordered panels.
Continuity anchors: [characters, wardrobe, props, location, time, and style].
Panel 1: [visible action and state].
Panel 2: [visible action and state].
[Continue through exact panel count.]
Layout: clear reading order, separated panels, consistent characters, deliberate shot variation.
Text (exact): [none / approved captions or dialogue with panel assignment].
Avoid: merged panels, missing beats, duplicate characters, continuity drift, extra text, or watermark.
```

**Visual QA:** Count and order panels; check each requested beat, character/prop continuity,
spatial logic, shot diversity, dialogue assignment, anatomy, and missing/merged panels.

**Evidence/status:** Official comic-strip/series principles plus the community scene-storytelling taxonomy; requires sequence-specific visual QA.

## Reference image to collectible figure

**Use when:** Turn an approved character, person, creature, or object into an original
collectible-toy concept.

**Fixed requirements:** Lock recognizable identity, signature silhouette, colors,
accessories, originality, packaging copy, and requested product format.

**Creative latitude:** Design toy material, articulation, stand, packaging structure,
studio lighting, and premium presentation without copying an existing toy line.

```text
Image 1: identity and design reference.
Deliverable: original [collectible figure/toy] concept in [packaging or studio presentation].
Preserve: recognizable face or signature geometry, proportions, colors, outfit/design details, and accessories from Image 1.
Product design: [scale, material, finish, articulation, stand, packaging structure].
Presentation: premium product photography with believable material response and sharp approved print.
Text (exact): [approved packaging copy only].
Avoid: identity drift, cheap plastic appearance unless requested, copied franchise branding, extra characters, extra text, or watermark.
```

**Visual QA:** Compare identity and signature details, then inspect material realism,
articulation, part count, packaging geometry, label text, reflections, and originality.

**Evidence/status:** Selective community pattern from the [character template category](https://github.com/freestylefly/awesome-gpt-image-2/blob/main/docs/templates.md), rewritten for reference preservation and originality.
