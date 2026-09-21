# Layout and exact-text templates

Use these for raster concepts whose acceptance depends on hierarchy, labels, counts,
or layout. Keep text short. Publication-critical typography and factual charts still
need deterministic finishing and fact verification.

## Exact-text poster or social card

**Use when:** A poster or campaign card has a small set of approved strings and a
clear visual hierarchy.

**Fixed requirements:** Lock every literal string, capitalization, occurrence count,
line count, reading order, format, and required subject.

**Creative latitude:** Choose the visual concept, grid, image/type interaction, palette,
material treatment, and typographic character unless the brand already fixes them.

```text
Deliverable: [ratio] [event/campaign] poster.
Visual concept: [agent-designed concept grounded in the brief].
Layout: [grid, margins, hierarchy, subject placement, and reserved copy areas].
Text (exact):
- "[HEADLINE]" exactly once, [case], [line count], at [location].
- "[SECONDARY COPY]" exactly once, smaller, at [location].
Typography: [approved type character or agent-selected treatment appropriate to the concept].
Avoid: additional letters or numbers, invented dates, fake logos, signatures, or watermark.
```

**Visual QA:** Compare every character, count occurrences, inspect line breaks, hierarchy,
margins, crop, contrast, and any accidental text.

**Evidence/status:** Official exact-text pattern plus a source-attributed community [poster adaptation](https://github.com/wuyoscar/GPT-Image2-Skill/blob/main/skills/gpt-image/references/templates-gpt-image-2.5.md).

## Conceptual typography poster

**Use when:** The title itself should be the main visual structure, not merely placed
above an illustration.

**Fixed requirements:** Lock the exact title, number of posters, approved supporting
copy, subject identity if referenced, and exclusions on logos or copied campaigns.

**Creative latitude:** Interpret meaning through letterform shape, scale, rhythm,
negative space, texture, figure/type interaction, and a restrained color system.

```text
Deliverable: one finished [ratio] conceptual typography poster for the exact title "[TITLE]".
Concept: interpret [meaning, tension, or cultural context] as one coherent visual metaphor.
Typography: make the exact title the dominant readable structure; design intentional letterform weight, width, spacing, rhythm, edge quality, and material texture.
Image interaction: use [figure/object/landscape/none] only when it deepens the title; integrate it through overlap, framing, depth, or negative space.
Composition: strong hierarchy, few elements, purposeful whitespace, [print/material treatment].
Avoid: extra readable copy, generic word art, default-font appearance, unrelated icons, copied campaign aesthetics, misspelling, or watermark.
```

**Visual QA:** Verify title spelling and readability first, then conceptual relevance,
hierarchy, negative space, figure/type interaction, and absence of extra copy.

**Evidence/status:** Selective structural adaptation from the community [industrial template library](https://github.com/freestylefly/awesome-gpt-image-2/blob/main/docs/templates.md); requires 2.5 visual evaluation.

## Technical or educational infographic

**Use when:** Explain a process, system, relationship, comparison, or lesson visually.

**Fixed requirements:** Lock audience, facts, stage count, labels, relationships, direction,
reading order, and any verified values.

**Creative latitude:** Choose shapes, icons, visual encoding, accent colors, connector style,
and illustration treatment while preserving logical meaning.

```text
Deliverable: [ratio] educational infographic for [audience].
Topic: explain [system/process/concept] from [start] to [outcome].
Structure: exactly [count] stages arranged [direction]; one connector between adjacent stages; no crossing arrows.
Labels (exact allowlist): "[LABEL 1]", "[LABEL 2]", "[LABEL 3]"[, ...], each exactly once.
Visual encoding: [shape/color] means [concept]; [shape/color] means [concept].
Style: scan-friendly technical editorial illustration with [background and visual language].
Accuracy constraints: [required relationships, direction, counts, or scale].
Mechanism encoding: [main path, branch, decision, query, or feedback semantics]; use strong continuous arrows for the main path and weaker/dashed connectors for secondary relations.
Text constraint: no explanatory sentences, captions, descriptions, or other legible words beyond the label allowlist.
Avoid: invented facts, other readable text, decorative arrows, fake controls, logos, or watermark.
```

**Visual QA:** Verify facts, every label, stage count, relationship, arrow direction,
legend consistency, reading order, visual hierarchy, and every legible string—not
appearance alone. Any unapproved readable text is a critical failure.

**Evidence/status:** Official process-visualization and scientific-diagram patterns from the [OpenAI prompting guide](https://developers.openai.com/api/docs/guides/image-prompting).

## Scientific scale diagram

**Use when:** A scientific concept should be shown across ordered spatial or temporal scales.

**Fixed requirements:** Lock verified scale names, units, magnification or range, order,
short insights, and required scientific relationships.

**Creative latitude:** Choose container shapes, transitions, rendering style, color coding,
and macro/micro visual treatment.

```text
Deliverable: [ratio] scientific scale diagram about [topic] for [audience].
Structure: exactly [6-8] ordered frames progressing from [small/early] to [large/late].
Each frame: exact scale name, verified unit or magnification, one [3-5]-word insight, and a distinct rendering appropriate to that scale.
Connections: show progression with restrained connectors; make relative scale differences visually legible.
Style: scientific editorial graphic with short readable labels and consistent encoding.
Avoid: repeated levels, identical apparent scale, generic magnifying-glass motifs, long paragraphs, invented values, or watermark.
```

**Visual QA:** Check order, units, relative scale, repeated/missing levels, label accuracy,
scientific plausibility, and whether the visual actually communicates scale change.

**Evidence/status:** Community-derived structural pattern from the [template library](https://github.com/freestylefly/awesome-gpt-image-2/blob/main/docs/templates.md); all scientific content must be independently verified.

## UI concept image

**Use when:** A product team needs a raster concept of a screen, not production UI code.

**Fixed requirements:** Lock platform, screen purpose, primary task, required regions,
approved short labels, and target fidelity.

**Creative latitude:** Choose component composition, spacing, surfaces, color tokens,
typographic hierarchy, and micro-visual details when no design system is supplied.

```text
Deliverable: [low/high]-fidelity visual concept for a [desktop/mobile] [product] screen, [ratio].
User goal: [one primary task].
Layout: [navigation pattern], [main regions], [primary action location], and clear hierarchy.
Content: [required metrics, cards, controls, or states].
Text allowlist (exact, global count): only "[short labels]", each exactly once in the entire canvas. Do not repeat them in navigation, section headers, cards, footers, or badges. Every other UI field must be blank, unlabeled, or a non-readable placeholder shape; do not invent prices, names, descriptions, captions, badges, or button copy.
Visual language: [existing design tokens or agent-selected coherent surfaces, borders, type, and color].
Avoid: unintended device frame, browser chrome, status bar, fake logo, dense body copy, or watermark.
```

**Visual QA:** Inspect task hierarchy, alignment, spacing, practical controls, label accuracy,
platform consistency, overlap, every legible string, and the global occurrence count of
each allowlisted label. Any unapproved or repeated readable text is a critical failure.
Confirm the concept can be rebuilt deterministically.

**Evidence/status:** Official interface-preview pattern plus the current local raster/UI boundary; use code for the shipping interface.

## Productivity slide, chart, or workflow

**Use when:** The output is a slide-like business artifact with real labels or data.

**Fixed requirements:** Lock canvas, title, verified data, chart semantics, labels, sources,
hierarchy, and the exact artifact type.

**Creative latitude:** Choose a restrained visual system, spacing, chart styling, diagram
shapes, and emphasis while maintaining truthful encoding.

```text
Deliverable: one [16:9 slide/chart/workflow] titled "[TITLE]" for [audience].
Purpose: communicate [single takeaway].
Content: [verified numbers, labels, nodes, relationships, and source line].
Layout: [regions and reading order] with clear hierarchy and generous whitespace.
Visual language: professional [brand or agent-selected restrained system], readable typography, polished spacing.
Accuracy: chart axes, legends, arrows, proportions, and labels must match the supplied data.
Avoid: invented values, misleading scale, clip art, generic stock photos, decorative clutter, extra text, or watermark.
```

**Visual QA:** Verify all data and source text, chart encoding, axes, legends, arrows,
hierarchy, readability at presentation size, and absence of invented numbers.

**Evidence/status:** Official productivity-visual pattern from the [GPT Image 2.5 guide](https://developers.openai.com/api/docs/guides/image-prompting); deterministic charting remains preferable for exact data graphics.

## Visual abstract or executive summary

**Use when:** A report or technical topic must become a single-page visual explanation
for readers who need the conclusion, evidence, and next actions quickly.

**Fixed requirements:** Lock the supplied facts, conclusion, evidence count, action count,
reading order, and approved strings. Do not invent metrics, dates, components, citations,
or conclusions.

**Creative latitude:** Choose a restrained editorial system, information hierarchy,
icons, spacing, and visual encoding that make the supplied argument scannable.

```text
Deliverable: one 16:9 [visual abstract/executive summary] for [audience].
Source truth: use only these supplied facts: [facts].
Top: [one direct conclusion].
Middle: exactly [3-5] evidence modules, each with [short label + one factual explanation + one symbol].
Bottom: exactly [count] implications or next actions: [list].
Layout: explicit reading order, strong whitespace, restrained editorial hierarchy.
Text: render only the approved strings and short explanations; no invented numbers or facts.
Avoid: decorative clutter, fake citations, unsupported claims, extra readable text, logos, or watermark.
```

**Visual QA:** Verify every fact, label, module/action count, reading order, text string,
and relationship. For publication-critical copy, finish typography deterministically.

**Evidence/status:** Two local GPT Image 2.5 checks produced usable visual-abstract and
executive-summary concepts; text-heavy success is sample evidence, not a guarantee.

## Document or publication page concept

**Use when:** Explore a white-paper, manual, editorial, catalog, or encyclopedic page system.

**Fixed requirements:** Lock page size, column count, margin logic, hierarchy, approved
copy, folio/navigation needs, and required image/table positions.

**Creative latitude:** Choose grid rhythm, type pairing, rules, callout treatment, image
cropping, and restrained publishing details.

```text
Deliverable: [single page/spread/cover-system concept] for [publication type], [page ratio].
Content hierarchy: [title, deck, section heads, body placeholders or approved copy, captions, folio].
Grid: [column count], [margin character], baseline rhythm, aligned image/table/callout regions.
Visual language: [editorial/technical/catalog] with readable typography and consistent spacing.
Text (exact): render only [approved short strings]; represent long body copy as non-readable layout texture unless supplied for draft visualization.
Avoid: random columns, fake citations, unreadable dense copy, inconsistent margins, decorative clutter, or watermark.
```

**Visual QA:** Check grid, margins, hierarchy, alignment, repeated page logic, exact short
copy, image/caption relationships, and whether deterministic typesetting is still required.

**Evidence/status:** Selective adaptation of the community [document-publishing category](https://github.com/freestylefly/awesome-gpt-image-2/blob/main/docs/templates.md); intended for concepting, not final typesetting.
