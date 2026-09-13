# Prompting GPT Image 2.5

The model reads natural-language briefs, not unordered keyword bags. Choose the format that makes requirements easy to inspect and update. Short paragraphs work for simple scenes; labeled sections help complex layouts and edits.

## Build the brief

Use only fields that affect acceptance:

```text
Deliverable: <where and how the image will be used>
Primary request: <subject and visible result>
Input images: <Image 1 role; Image 2 role> (when present)
Composition: <frame, placement, counts, negative space>
Style and medium: <photo, illustration, render, material conventions>
Lighting and color: <direction, softness, palette>
Text (exact): "<literal copy>"
Change: <edit only>
Preserve: <edit only>
Avoid: <few consequential exclusions>
```

Do not emit empty labels. Do not repeat or contradict requirements. The CLI sends the final prompt exactly as supplied.

## Concrete visual language

- Open with the deliverable: product listing photo, campaign banner, textbook diagram, mobile poster.
- Describe visible properties instead of praise words: soft window light from the left, matte ceramic, shallow depth of field, four objects in a row.
- Give exact counts and place elements relative to named elements: “three labels below the diagram,” not “several labels around it.”
- Treat camera and lens language as appearance cues, not guaranteed physical simulation.
- Name the medium and its conventions instead of a creator's name.
- Choose output dimensions before writing framing; the model recomposes for the requested shape.

## Exact text

Put required copy in quotes. State capitalization, line breaks, occurrence count, typography, color, and location. Spell unusual Latin names letter by letter when necessary. Ask for no additional text, then inspect every character and diagram relationship. Dense legal copy and pixel-perfect typography still belong in a deterministic design tool.

## Reference images

Number every input and state what it controls: identity, product, garment, style, background, layout, or inserted object. Say what may transfer and what must not. A reference without a role lets the model decide how to use it.

## Iterate

Change one condition at a time and use the approved result as the next input. Restate critical invariants. Compare accumulated texture and small text against the original, not only the previous pass. Once all changes are settled, consider a single consolidated edit from the approved base to reduce accumulated drift.
