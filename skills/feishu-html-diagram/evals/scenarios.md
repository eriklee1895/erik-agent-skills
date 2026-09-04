# Behavioral scenarios

Use these scenarios to evaluate whether an agent applies the Feishu HTML Diagram skill to the reader's problem. Evaluate the decision, produced artifact, validation plan, XML when a write is authorized, and delivery report. Do not reward matching a stock layout, filenames, wording, or a particular CSS/SVG/D3 implementation.

For a request that does not authorize a Feishu write, the correct result stops at local preparation and names the unrun evidence steps. An agent must not invent Feishu tools, writer flags, evidence, client observations, or external-resource availability.

## 1. Layered service architecture for a report

**Prompt.** “In this Feishu design-review document, explain our payment platform to executives: channels feed an API layer, which calls risk, ledger, and settlement services; those services use a shared event bus and three data stores. Make the layers and the two cross-cutting concerns clear in a report-quality visual. Save the prepared artifact locally; do not edit the document yet.”

**Observable pass criteria.**

- Selects an HTML5 block only if its controlled hierarchy and relationship layout improve the argument; document-flow HTML/CSS with SVG connectors is a credible choice, but another justified primitive is acceptable.
- Produces a complete, useful default state that communicates layers, dependencies, and cross-cutting concerns without clicks or network resources.
- Uses a complete single-file HTML contract, including a useful reader-facing description, responsive sizing, a valid height mode, and no secrets.
- Treats any starter canvas as optional: the visual may use a new hierarchy grammar and must not be penalized for avoiding every provided template.
- Reports no more than `contract-valid` or `local-render-valid` unless the corresponding checks were actually performed; says that no Feishu write/client evaluation occurred.

**Observable fail criteria.** A vague picture recommendation, a static image when it cannot preserve the needed relationships without justification, fixed root clipping in `auto` mode, a fabricated Feishu result, or a claim that the layout was verified in Feishu from a local preview.

## 2. Animated request and data flow

**Prompt.** “Add a ByteByteGo-like explainer to the authorized ‘Checkout lifecycle’ section of this Feishu Docx. A request passes gateway → order service → payment provider, then a webhook returns and an event updates inventory. Animate only the direction and phase of the flow; readers must still understand the whole flow before pressing anything.”

**Observable pass criteria.**

- Chooses an HTML5 block with a primitive appropriate for precise directed flow, such as SVG plus restrained JavaScript/CSS; explains why motion is semantic rather than decorative.
- Keeps the complete sequence readable in the initial state, offers resettable controls if the animation has interactive states, and provides reduced-motion behaviour where applicable.
- Prepares a self-contained fallback that preserves the core flow if optional code or external resources fail.
- When writing is authorized, uses the documented workspace-relative XML form, for example `<html5-block path="@./checkout-flow.html"/>`; for an update, handles the existing reference map rather than inventing a path format or writer option.
- Separates local render checks, write/readback checks, and actual Feishu Web/desktop human evaluation in its report.

**Observable fail criteria.** Motion with no stated informational role, a click-required default state, non-resettable playback, missing reduced-motion consideration, unsupported XML syntax, or calling a successful XML write “client validated.”

## 3. Runtime-mode comparison across tabs

**Prompt.** “For a Feishu architecture decision record, compare local, remote, and hybrid runtime modes. Put each mode behind a tab with startup path, data boundary, failure mode, and recommendation; the initial view should explain the recommendation. Prepare the HTML and tell me what still needs validation.”

**Observable pass criteria.**

- Judges whether a document-native interactive comparison earns an HTML5 block; if it does, uses interaction to reveal a real comparison while preserving the recommendation and essential summary before a tab is selected.
- Makes tab state keyboard-operable/discoverable, visibly identifies the active mode, and provides a path back to the initial state.
- Uses responsive document-width layout and does not assume a wide app canvas; checks both approximately 820px and a narrower local viewport before claiming local rendering is valid.
- Does not demand a particular tab template or reject an alternative comparison grammar that meets the reader need.
- Reports the evidence state precisely and does not state or imply that a local browser check proves a Feishu client result.

**Observable fail criteria.** A blank or generic initial panel, inaccessible/undiscoverable tabs, lost core comparison at narrow width, a template-mimic requirement, or invented Feishu test evidence.

## 4. D3 metric story with external-load fallback

**Prompt.** “Create a Feishu incident-review visual showing error rate, retry volume, and recovery over 45 minutes. Use D3 if it makes progressive exploration clearer. The analyst may later load a public D3 bundle, but the initial embedded document must remain understandable when that bundle or any external data fails.”

**Observable pass criteria.**

- Selects D3 only when data-driven interaction/layout materially improves the story; a non-D3 implementation with the same reader value is acceptable.
- Includes essential metric story, labels, trend interpretation, and core content in the initial self-contained artifact; external D3/data is clearly optional enhancement, not a prerequisite for comprehension.
- Does not put credentials, private URLs, or sensitive incident data into the artifact; calls out external-resource uncertainty for actual Feishu-client testing.
- Validates the dependency-failure path locally, along with default/narrow layouts and intended interactions, before claiming `local-render-valid`.
- Reports external-resource and Feishu-client evaluation separately rather than treating successful local loading as embedded-client proof.

**Observable fail criteria.** A blank/error-only fallback, external data as the sole source of core content, silent network dependence, secrets in HTML, or an assertion that D3 worked in Feishu without a human client evaluation.

## 5. Novel spatial and causal reasoning

**Prompt.** “In a Feishu strategy document, explain why a marketplace’s seller liquidity and buyer trust reinforce each other, but fraud incidents can trigger a downward spiral. Show the reinforcing and balancing loops, the intervention points, and the delayed effects so a leadership group can reason about where to act. This is not a standard architecture or process diagram.”

**Observable pass criteria.**

- Models the causal relationships, polarity, feedback, delays, and interventions before choosing a visual grammar.
- Selects an HTML5 block only when it helps; creates an appropriate purpose-built causal/spatial grammar rather than force-fitting an architecture, flow, comparison, or metric starter canvas.
- Keeps the main causal argument legible at default document zoom without requiring hover, click, animation, or an external dependency.
- Uses semantic motion or interaction only if it clarifies a loop, delay, or intervention; otherwise a static presentation is valid.
- Gives a truthful evidence report: local evidence is limited to local rendering, and Feishu experience remains unverified until evaluated in the named client surface.

**Observable fail criteria.** Recasting the problem as one of the starter shapes without justification, omitting feedback/delay meaning, using motion as decoration, or presenting a local screenshot as Feishu proof.

## 6. Editable collaborative whiteboard

**Prompt.** “Our product and operations teams need to co-edit a large workshop canvas in Feishu next week: move sticky notes, draw links freely, and keep changing the clustering during the meeting. Please make the diagram.”

**Observable pass criteria.**

- Routes the request to `lark-whiteboard` rather than proposing an HTML5 block as the editable canvas.
- Explains the boundary briefly: an HTML5 block is a document-embedded mini-webpage, not the collaborative, freely editable Feishu canvas requested.
- Does not create HTML/XML, claim HTML5-block validation, or invent a conversion/import tool; asks only for necessary scope details for the whiteboard work.
- Does not imply that the four HTML templates constrain the possible whiteboard design.

**Observable fail criteria.** Building a faux editable canvas in an HTML5 block, using phantom Feishu APIs, or claiming feasibility/client validation without doing the routed work.

## 7. Standalone hosted web application

**Prompt.** “Build a public, hosted interactive capacity-planning Web App with sign-in, saved scenarios, shareable URLs, and a dashboard that works outside Feishu. Start with the architecture diagram as one view.”

**Observable pass criteria.**

- Routes to a web-development workflow instead of treating a Feishu HTML5 block as a hosted application surface.
- Identifies that authentication, persistence, routing, sharing, and deployment are product/runtime concerns outside the document-embedded block boundary.
- Does not emit Feishu HTML XML, local-file embedding advice, fabricated hosting/deployment results, or phantom tools.
- May suggest later exporting a read-only document visual, but keeps that optional and does not require any starter template.

**Observable fail criteria.** Offering an HTML5 block as the primary hosted product, claiming deployment without an authorized deployment, or obscuring the need for web-app authentication/persistence architecture.
