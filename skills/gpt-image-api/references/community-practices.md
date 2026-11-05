# Community practices for GPT Image 2.6

Use attributed observations to shape prompts and inspect outputs. Provider behavior, article examples, and suggested templates carry their own evidence scope.

## Native GIF evidence (2026-11-05)

The official API demo describes a sprite sheet that captures the poses, followed by automatic frame extraction and looping GIF assembly. Treat native GIF as the API's finished output format when discussing community results. [Official OpenAI demo](https://www.youtube.com/watch?v=9ZxCOHkfn_8)

These launch-day examples are small, attributed observations, not reliability benchmarks or proof of model architecture.

| Source | Observed result | Reusable implication |
| --- | --- | --- |
| [Kingy's direct Sunburst API test](https://kingy.ai/blog/chatgpt-gifs-images-2-6-vs-2-5-hands-on-test/) | A decoded 512px ten-frame product GIF retained readable labels, but gained a badge artifact and had uneven movement and a reset jump. A separate ChatGPT test returned different dimensions. | Inspect labels, motion spacing, and the seam. Keep ChatGPT and API evidence separate. |
| [CellCog's paid API experiment](https://cellcog.ai/blog/gpt-image-2-6-vs-2-5/#animated-gifs-from-one-prompt) | A mascot wave and labeled process animation worked; the diagram marker stepped and the reset jumped. Sixteen frames were accepted; 17/32 were rejected despite the guide advertising 64. | Prefer one action and stable landmarks. The CLI uses the schema's conservative 2–16 bound. |
| [Tencent creator examples](https://cloud.tencent.com/developer/article/2776489) | Returned product/character/ambient GIFs showed background and object-shape drift, changing fine details, and a broken hand/umbrella relationship. | Inspect every frame's contact relationships and fixed geometry. A successful action sequence does not prove reference fidelity. |
| [OFOX native GIF example](https://ofox.ai/blog/gpt-image-2-6-gif-guide/) | Provider-native Flare GIF had nine distinct 512px frames at 200 ms; the bird moved while branch and leaf details shifted. Its separate sheet conversion and untested templates were labeled separately. | A finished returned GIF is a real deliverable; a converted sheet or proposed template is different evidence. |
| [Official launch and partner demos](https://openai.com/index/introducing-images-2-6/) | Reaction stickers, a hand-drawn owl animation, and Town's mascot typing indicator illustrate short-form uses. | Useful pilot ideas; selected launch examples do not establish production outcomes or universal quality. |

The shared practical pattern is one subject, one short action, a locked camera, named identity details, and an explicit return toward the start. This is a synthesis, not a measured success-rate claim. Animated text, exact diagrams, complicated contact, and long camera moves remain acceptance-sensitive. ChatGPT's reference-to-GIF interface does not establish the official image edit API's GIF contract.

A local OFOX check on the same date verified real native generation and reference-edit GIF bytes, distinct decoded frames, and transparent pixels in every frame for a transparent request. However, multiple requested frame counts/delays still returned nine frames at 200 ms. Separate left/right markup requests were accepted but both recolored the right mug, so markup spatial following was not validated. These are provider-route observations. The CLI records actual artifact settings, warns on mismatches and OFOX markup, and requires explicit opt-in for that provider's GIF edit extension. They do not show equivalent behavior on direct OpenAI. OFOX SVG requests failed with a missing-`svg.model` error both without selection and with an explicit model from its live catalog, so native SVG delivery was not validated on that route.
