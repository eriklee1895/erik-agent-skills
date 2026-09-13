# Image editing workflow

Use `edit` whenever one or more images must influence the result. GPT Image editing is generative: preservation can be strong but is not a pixel identity guarantee.

## Assign input roles

List images in intentional order and use the same numbering in the prompt and CLI:

```text
Image 1: edit target and final canvas.
Image 2: identity reference only.
Image 3: garment reference only.
```

With a mask, Image 1 is the edit target. A style reference must not silently contribute its subject; an identity reference must not control the background.

## Change / Preserve / Avoid

Write editing instructions in this order:

```text
Change: Change only <target> to <finished visual state>.
Preserve: Keep <identity, geometry, labels, pose, framing, lighting, background> unchanged.
Avoid: No <few consequential unwanted additions>.
```

Describe the finished state rather than an image-processing operation. “Change only the jacket to deep forest-green velvet” is clearer than “apply a green hue shift.”

## Precision patterns

### Identity or clothing

Preserve facial structure, expression, skin tone, hairstyle, age, body shape, proportions, and pose. Change only the named garment or property. Use Sunburst when likeness failure invalidates the result.

### Products and labels

Preserve silhouette, proportions, camera angle, scale, material, reflections, logo, label, spelling, and every printed character. If product pixels must remain exact, composite the accepted generated region back onto the original.

### Background replacement

Name the complete new environment and list what the subject retains: size, position, angle, edge shape, and light. If the new environment implies different lighting, explicitly authorize and constrain relighting.

### Add or remove

Removing is usually more bounded than adding. For removal, name nearby objects that must remain, including supports or shadows. For addition, anchor the new object relative to something already present and request matching perspective, scale, light, and contact shadow.

### Text replacement or translation

Quote the exact replacement copy. Preserve layout, hierarchy, non-target text, icons, colors, and spacing. Verify every character and whether any source-language text remains. For publication-critical copy, treat the result as a draft and finish typography deterministically.

### Style transfer and compositing

Assign each reference a single purpose. State whether palette, texture, line quality, medium, subject, or composition transfers. For compositing, identify the source element, destination, relative placement, lighting match, and all base-scene invariants.

## Masks

The mask must be a same-dimension PNG with alpha and at least one fully transparent pixel. Transparent pixels indicate the editable area. Include enough area for seams, reflections, and contact shadows, but avoid protected labels and geometry. Inspect outside-mask drift after generation; the mask guides the edit but does not guarantee untouched pixels. When preservation matters, request the first input's exact dimensions instead of `auto`; hold that size constant through later edits.

## Iterative editing

- Start every turn from the last approved image.
- Request one meaningful change per turn.
- Repeat earlier approved changes in `Preserve`.
- Keep every intermediate and its metadata.
- Hold dimensions constant through the chain.
- Compare fine texture, small text, and identity against the original.
- Start over when an instruction fails repeatedly, protected detail softens, or preservation instructions become longer than the change.

For a settled sequence, consider restating all approved changes in one edit from the original source to reduce accumulated rerendering drift.
