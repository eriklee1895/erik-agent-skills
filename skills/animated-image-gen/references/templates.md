# Template selection

Read one relevant brief from `assets/templates/`. Its inputs and defaults are starting points. Preserve user overrides by adapting the prompt, source-pose structure and timeline together. `templates NAME` displays the JSON.

| Request | Brief | Measured condition |
| --- | --- | --- |
| Blink, avatar or subtle reaction | [blink-reaction](../assets/templates/blink-reaction.json) | Identity and eye motion checked across multiple samples. Alpha-reference editing is a separate tested route |
| Sleepy character or breathing idle | [sleepy-idle](../assets/templates/sleepy-idle.json) | Use one pose and a selected local chest-outline region. Whole-sheet breathing moved supporting objects |
| Engineer reacts to another error | [build-panic](../assets/templates/build-panic.json) | Human-engineer samples. Robot transfers had identity or monitor-layout faults |
| Isolated pixel-style effect | [pixel-flame](../assets/templates/pixel-flame.json) | Two color variants, separated background, base registration and nearest-neighbor finishing |
| Two-character argument | [comic-argument](../assets/templates/comic-argument.json) | Four acting beats, local text and reading holds. Inspect hands and caption reservation |
| Steam or product micro-motion | [product-steam](../assets/templates/product-steam.json) | Lock static product and background regions after inspection |
| A playful response inside a photo | [photo-reaction](../assets/templates/photo-reaction.json) | Evidence uses one user photo. A second scene variant also used supplied animation keyframes |
| Fixed tool-call explanation | [agent-tool-loop](../assets/templates/agent-tool-loop.json) | The local `flow` helper covers a fixed four-node topology at two canvas sizes |

The template fields guide the agent and local compositor. The Ark payload contains the image prompt, model, sheet size and references. Output timing, final canvas and delivery format belong to the animation layer.

Ordinary actions can begin at 6–9 poses. Photo reactions can use 9–12 and captioned stories 12–16. More poses help when the acting needs additional stages. A short story can hold a few poses for reading, while breathing or ambient motion may benefit from a reversible local cycle.

Before generation, plan the subject, acting beats, camera and identity anchors. After generation, check actual cell boundaries and every pose. For captions, reserve a suitable band and use local overlays for exact wording. [Observed limitations](pitfalls.md) and [template evidence](../evals/template-results.json) provide the measured boundaries. [Community patterns](community-patterns.md) record the inspiration and source scope.

## Included previews

These synthetic examples show inspected outputs from the research and installed-entrypoint checks. The preview files are bundled with the skill.

| Preview | Delivery | Measured sequence |
| --- | --- | --- |
| [Fox blink](../assets/previews/blink-reaction.webp) | Lossless WebP, 256×256 | 9 frames, 1.2 seconds, alpha-reference editing and local base registration |
| [Pixel flame](../assets/previews/pixel-flame.gif) | GIF, 256×256 | 8 frames, 0.8 seconds, nearest resizing, 64 colors and local base registration |
| [Comic argument](../assets/previews/comic-argument.gif) | GIF | Synthetic characters with local captions and reading holds |
| [Agent tool loop](../assets/previews/agent-tool-loop.webp) | Lossless WebP, 960×540 | Fixed four-node flow, 4.8 seconds, local rendering |

All four previews repeat indefinitely. The [release validation](../evals/release-validation.json) records fresh-install tests and the separate three-call live smoke run.
