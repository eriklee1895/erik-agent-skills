# Selecting prompt template assets

Template assets are optional scaffolds, not mandatory prompt molds. A complete brief
goes directly to prompt review and `--dry-run`; do not load a template merely because
one exists.

## Selection rule

- For a complete brief, preserve its creative direction and normalize only what is
  needed for clarity.
- A complete specialized brief also bypasses templates; deliverable type alone never
  triggers a template.
- For an incomplete brief that lacks useful structure, load one template slice from
  the table below and adapt one matching template.
- Do not stack full templates. Combine only the few fields required by a genuine
  hybrid deliverable.
- Resolve or delete all unresolved placeholders before the API call.
- Keep API parameter syntax for model, quality, size, background, and output settings
  outside the image prompt. Keep visual intent inside it: describe target framing or
  aspect-ratio composition, scene/background appearance, and genuine transparency or
  opaque-canvas requirements when they affect the image.

## Asset routing

| Need | Load |
| --- | --- |
| Natural photo, article illustration, transparent asset, historical scene, game asset | [`generation-core.md`](../assets/templates/generation-core.md) |
| Object/text edits, identity, try-on, background, weather, style, sketch, outpaint | [`editing-core.md`](../assets/templates/editing-core.md) |
| Posters, UI, diagrams, scientific scales, slides, publication layouts | [`layout-and-text.md`](../assets/templates/layout-and-text.md) |
| Character sheets, pose grids, recurring characters, comics, collectible figures | [`characters-and-series.md`](../assets/templates/characters-and-series.md) |
| Product heroes, brand systems, campaigns, architecture, product-development boards | [`brand-product-and-space.md`](../assets/templates/brand-product-and-space.md) |

## Adaptation contract

Each asset template separates five concerns:

- **Use when:** routing signal, not prompt content.
- **Fixed requirements:** facts, exact text, counts, relationships, identity, and edit
  invariants that must survive adaptation.
- **Creative latitude:** composition, palette, medium, light, texture, visual metaphor,
  or other choices the agent may originate when the user has not fixed them.
- **Prompt scaffold:** a reusable starting shape. Rewrite it naturally; do not send
  headings or empty fields that add no value.
- **Visual QA:** acceptance checks after generation.

Evidence/status identifies official patterns, community adaptations, and unverified
ideas. Community popularity is not model validation. Preserve source attribution in
research notes, but the final image prompt should contain only task-relevant visual
instructions.

## Cost and iteration

One template selects one prompt direction; it does not authorize extra variants,
model comparisons, or a “main plus alternative” batch. Start with one result unless
the user requested more. When a result misses one criterion, change that condition
only and re-check the complete acceptance set.
