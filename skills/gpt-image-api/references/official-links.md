# Official OpenAI references

Verified against official OpenAI documentation on 2026-11-05.

## Current models

- [GPT Image 2.6 Flare](https://developers.openai.com/api/docs/models/gpt-image-2.6-flare)
- [GPT Image 2.6 Sunburst](https://developers.openai.com/api/docs/models/gpt-image-2.6-sunburst)

## Guides

- [Image generation](https://developers.openai.com/api/docs/guides/image-generation)
- [Image prompting](https://developers.openai.com/api/docs/guides/image-prompting)
- [Images and vision](https://developers.openai.com/api/docs/guides/images-vision)
- [Image input token and cost calculator](https://developers.openai.com/api/docs/guides/image-cost-calculator)
- [API pricing](https://developers.openai.com/api/docs/pricing#image-generation)

## Python API reference

- [Images resource](https://developers.openai.com/api/reference/python/resources/images)
- [`images.generate`](https://developers.openai.com/api/reference/python/resources/images/methods/generate)
- [`images.edit`](https://developers.openai.com/api/reference/python/resources/images/methods/edit)
- [Image generation streaming events](https://developers.openai.com/api/reference/python/resources/images)
- [Image edit streaming events](https://developers.openai.com/api/reference/python/resources/images)

## Native format and markup sections

- [Animated GIF output](https://developers.openai.com/api/docs/guides/image-generation#generate-animated-gif-output)
- [SVG output](https://developers.openai.com/api/docs/guides/image-generation#generate-svg-output)
- [Markup-guided edits](https://developers.openai.com/api/docs/guides/image-generation#markup-guided-edits)
- [Current generation endpoint schema](https://developers.openai.com/api/reference/resources/images/methods/generate)
- [Current edit endpoint schema](https://developers.openai.com/api/reference/resources/images/methods/edit)
- [Images 2.6 launch](https://openai.com/index/introducing-images-2-6/)
- [Official API demo explaining sprite-sheet generation, automatic frame extraction, and looping GIF assembly](https://www.youtube.com/watch?v=9ZxCOHkfn_8)

The generation guide and endpoint schema currently disagree on GIF frame limits (2–64 versus 2–16) and delay ranges (20–2000 ms versus a wider encoded cap). The CLI uses the narrower limits. Compatible providers may accept fields without honoring them; the decoded animation remains the evidence of actual frames and timing. Official GIF generation-only guidance is separate from the explicitly enabled OFOX edit extension.
