---
name: feishu-html-diagram
description: Use when a Feishu Docx needs a high-fidelity architecture diagram, animated data flow, interactive explainer, or programmable data visualization beyond Mermaid, whiteboard, table, or image constraints.
metadata:
  author: liyuheng.erik
---

# Feishu HTML Diagram

## Core principle

Treat an HTML5 block as a programmable mini-webpage living inside a Feishu Docx. The agent already knows HTML, CSS, SVG, JavaScript, and D3; use that capability to make the document's argument easier to inspect, not to turn a document into an application.

## Use and route boundaries

Use this skill when the visual needs controlled layout, motion, interaction, or a visual grammar that Mermaid, a whiteboard, a table, or a static image cannot express well. Route a request for an editable Feishu canvas to `lark-whiteboard`; route ordinary charts that need no document-native custom experience to a table or image/chart workflow; route a standalone web product to a web-development workflow.

## Eight-step workflow

Follow this sequence. Do not skip evidence just because the HTML looks plausible.

1. **Recognize the opportunity.** Identify the claim or decision the visual must help a reader understand.
2. **Model the information.** Decide the entities, relationships, sequence, quantities, states, and what must remain readable at a glance.
3. **Choose the medium and Web primitive.** Confirm that an HTML5 block is the right medium, then choose the simplest natural primitive: document-flow HTML/CSS for cards and hierarchy; SVG for connectors, topology, or precise geometry; Canvas for dense pixels or custom drawing; D3 when data-driven layout or interaction earns its complexity; JavaScript only for meaningful state or interaction.
4. **Create a single-file HTML document.** Make the initial/default state complete and useful without a click. When an HTML file will be embedded or updated, read [the HTML5 block contract](references/html5-block-contract.md) first.
5. **Validate locally.** Before any completion claim, read [the validation guide](references/validation.md) and collect the applicable local evidence.
6. **Write the XML.** With authorization to edit the specified Feishu Docx, embed the local file using the platform XML contract.
7. **Fetch back.** Read the document after the write and inspect its `reference_map`; do not treat an XML placeholder as the HTML itself.
8. **Validate in Feishu.** Check the rendered block in the applicable Feishu Web and/or desktop client and report the achieved evidence state.

## Design freedom

Templates are optional inspiration, never a whitelist. Invent a new visual grammar whenever it better explains the information: a causal loop, operating model, progressive disclosure, state machine, systems map, or another purpose-built form may be clearer than a familiar diagram type. Keep one visual focused on one main argument; add interaction or motion only when it reveals state, sequence, or comparison that a static view cannot.

## Third-party code and data

The default embedded artifact must be self-contained, with no network dependency, and must provide an understandable static reading experience inside the Feishu document. If a third-party library, font, image, or data source materially improves the visual, treat it as an optional enhancement: retain that in-document static fallback when the enhancement does not load, then separately verify the enhanced external-resource experience in Feishu. External resources are uncertain at embed time; disclose that uncertainty and never put credentials, tokens, private URLs, or other secrets in the HTML.

## Execution boundary

Creating local HTML is preparation. Writing or updating a Feishu document is an external mutation: perform it only for the user-authorized document and section, preserve unrelated document content, and stop for direction if the target document, replacement scope, or required external access is unclear. Do not claim Feishu rendering from a local preview or a successful write alone.

## Delivery report

State the reader-facing purpose, selected primitive, and whether the block is static, animated, or interactive. Name the local HTML and target document/section, then state the highest evidence level actually reached: `contract-valid`, `local-render-valid`, `feishu-write-valid`, or `feishu-experience-valid`. List any untested client, external dependency, interaction, or human-evaluation item as remaining work.

## Common failure modes

- Treating a template as the set of permitted diagrams instead of modelling the reader's question.
- Choosing a flashy primitive when document-flow HTML/CSS would be clearer and more maintainable.
- Shipping an empty, clipped, or click-required default state.
- Fixed-height layouts in `auto` mode, overflow hidden at the root, or a layout that only works on a wide local viewport.
- Calling a local screenshot, XML write, or fetched `data-ref` proof that the Feishu client experience works.
- Adding motion that has no semantic meaning, ignores reduced-motion needs, or cannot be reset after interaction.
- Depending on unverified external resources or embedding secrets in a document artifact.

Read [the HTML5 block contract](references/html5-block-contract.md) whenever embedding or updating HTML. Read [the validation guide](references/validation.md) before claiming local or Feishu completion.
