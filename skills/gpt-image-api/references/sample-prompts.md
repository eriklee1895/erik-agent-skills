# GPT Image 2.5 sample prompts

Adapt these examples rather than stacking every field into every request.
For a sparse or specialized brief, use
[template-selection.md](template-selection.md) to choose at most one reusable
asset under `assets/templates/`.

## Product generation

```text
Deliverable: landscape hero image for a premium tea storefront.
Primary request: A single matte charcoal tea tin on a pale limestone plinth, label facing camera.
Composition: eye-level three-quarter product shot; tin in the right third; clear negative space on the left.
Style and medium: photoreal commercial product photography; crisp metal and paper texture.
Lighting and color: large softbox from upper left, restrained warm-neutral palette, natural contact shadow.
Text (exact): "MOUNTAIN TEA", centered once on the label in clean uppercase serif lettering.
Avoid: no extra products, no extra text, no watermark.
```

## Exact-text poster

```text
Deliverable: 2:3 cultural-event poster.
Primary request: Contemporary editorial poster built around one abstract cobalt paper sculpture.
Text (exact): Render "SPRING WORKSHOP" exactly once as the main title, uppercase, one line, bold white sans-serif, centered in the upper third. Render "APRIL 18" exactly once below it in smaller type.
Composition: strong grid, generous margins, sculpture in the lower half.
Avoid: no other letters, numbers, logos, signatures, or watermark.
```

## Precise product edit

```text
Image 1: edit target and final canvas.
Change: Change only the white chair upholstery to deep forest-green velvet with realistic pile and highlights.
Preserve: Keep the chair frame, shape, seams, product label, room, floor, camera angle, crop, lighting direction, shadows, color balance, and every other object unchanged.
Avoid: no new furniture, no text, no watermark.
```

## Identity-preserving composite

```text
Image 1: base street scene and final canvas.
Image 2: identity and clothing reference for the person to insert.
Change: Place the person from Image 2 beside the bicycle in Image 1, full body visible, naturally holding the handlebar.
Preserve: Keep the person's facial structure, expression, skin tone, hairstyle, age, body proportions, and clothing unchanged. Keep Image 1's buildings, bicycle, camera angle, crop, and existing objects unchanged.
Integration: Match Image 1's perspective, overcast light, scale, ground contact, and shadow direction.
Avoid: no additional people, text, logos, or watermark.
```

## Transparent product cutout

```text
Image 1: product photograph to extract.
Change: Isolate the exact product on a fully transparent canvas.
Preserve: Keep product geometry, label spelling, material, reflections, glass transparency, and edge detail unchanged.
Output: centered subject, clean alpha, crisp silhouette, no halo or color fringe.
Avoid: no solid backdrop, checkerboard, scenery, invented shadow, restyling, or watermark.
```

## Diagram

```text
Deliverable: landscape educational infographic for software engineers.
Primary request: Explain a retrieval pipeline from query to final answer.
Layout: five numbered stages left to right: "QUERY", "EMBED", "SEARCH", "RERANK", "ANSWER". One arrow between each adjacent stage. A compact legend below, no crossing arrows.
Style and medium: clean technical editorial illustration, white background, dark navy lines, one cyan accent.
Text: render every stage label exactly once; no other text.
Constraints: relationships and arrow direction must be logically correct.
```
