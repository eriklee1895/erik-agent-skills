# Native GIF generation and reference animation

Use `output_format="gif"` on `POST /v1/images/generations` to receive the finished animation in `data[].b64_json`. Decode and save the original bytes. A grid of poses, a PNG named `.gif`, and a static GIF are different artifacts; the CLI rejects a mismatched container or single-frame GIF.

## Officially described generation process

OpenAI's November 4, 2026 API demo describes generating the poses in a sprite sheet, automatically extracting its frames, and stitching them into a looping GIF. Here, native GIF refers to the finished animation delivered through the Image API. The service performs the frame extraction and assembly, and this CLI preserves the returned bytes. The demo establishes this processing workflow. It provides no further detail about the model's training or internal temporal representation. [Official OpenAI video](https://www.youtube.com/watch?v=9ZxCOHkfn_8)

For API GIF requests, describe the subject, motion, fixed details, and loop. Set the format and animation controls in request fields. For an explicit sprite-sheet deliverable, specify the cell layout and frame order, then use a separate extraction and encoding workflow. The launch page's OpenArt examples specify six sequential frames in a 3-column by 2-row sheet. [Official launch examples](https://openai.com/index/introducing-images-2-6/)

## Prompt shape

Describe one subject, one short action, and the return to the beginning. Name identity-critical landmarks, camera position, subject scale, baseline, lighting, and background details that should remain stable. For example:

```text
A small red panda mascot with round gold glasses and a teal hoodie, centered with generous margins. Locked camera and a plain pale cream background. The panda raises its right paw, gives one friendly wave, then lowers the paw toward its starting pose for a repeating loop. Preserve the glasses, face markings, hoodie shape, scale, baseline, and background throughout. No captions, logos, grid, or sprite-sheet layout.
```

Start with a single readable action: a wave, blink, bounce, tilt, or small ambient motion. Keep mathematical motion, exact chart geometry, and critical text in deterministic animation when exactness is essential. GIF generation does not establish video-model temporal consistency.

## Request controls

| Field | CLI contract | Omitted behavior |
| --- | --- | --- |
| `model` | 2.6 Flare or Sunburst | Flare |
| `output_format` | `gif` | Still PNG unless selected |
| `size` | `auto` or positive `WIDTHxHEIGHT`, both multiples of 16 | `auto` |
| `frame_count` | Integer 2–16 | API documents 9 |
| `frame_duration_ms` | Integer 20–2000, encoded in 10 ms units | API documents 200 |
| `complexity` | `low`, `medium`, `high`, independent of quality | Model default, currently high |

GIF dimensions are **per frame**. Do not apply the still-image minimum of 655,360 pixels to each GIF frame. The provider still enforces model-specific sheet dimensions and the total budget across frames and `n`. Begin with `auto` or `512x512`; lower dimensions can fail sheet-budget checks. Reduce dimensions, frame count, or number of animations in response to the actual API error.

The [generation guide](https://developers.openai.com/api/docs/guides/image-generation#generate-animated-gif-output) currently advertises 2–64 frames, while the [endpoint schema](https://developers.openai.com/api/reference/resources/images/methods/generate) says 2–16. This CLI uses 2–16 conservatively. [CellCog's reported direct API experiment](https://cellcog.ai/blog/gpt-image-2-6-vs-2-5/#animated-gifs-from-one-prompt) accepted 16 and rejected 17/32. This is a source/runtime discrepancy, not proof that all future providers have the same limit. The schema describes longer encoded delays; the CLI uses the guide's conservative 20–2000 ms range.

GIF output rejects streaming, partial images, masks, custom compression, and the CLI's downscale operation. Frame fields are rejected for non-GIF output. The CLI never flattens animation into a resized first frame.

```bash
uv run "$SKILL_DIR/scripts/gpt_image_api.py" generate \
  --model flare --prompt-file loop-prompt.txt \
  --output-format gif --size 512x512 \
  --frame-count 9 --frame-duration-ms 200 --complexity low \
  --out output/gpt-image-api/panda.gif --dry-run
```

After reviewing the dry run, repeat without `--dry-run`. Distinct GIF jobs can use the same fields in batch JSONL.

## Reference → GIF: explicit OFOX extension

The official [OpenAI generation guide](https://developers.openai.com/api/docs/guides/image-generation#generate-animated-gif-output) says the image edit endpoint does not support GIF output. ChatGPT's image-to-GIF interface is a separate product route.

A local 2026-11-05 check through OFOX's compatible `/v1/images/edits` accepted a product reference and returned a 512×512 native GIF with nine distinct frames at 200 ms. This evidence applies to that provider/model route. The CLI exposes it through `--experimental-gif-edit` and accepts the flag only with an OFOX base URL; it does not silently change endpoints or substitute a static sheet.

```bash
uv run "$SKILL_DIR/scripts/gpt_image_api.py" edit \
  --model flare --image approved-mascot.png --image-role "identity and style reference" \
  --prompt "Preserve this mascot. Make it wave once, then return to its starting pose. Locked camera, stable background." \
  --output-format gif --experimental-gif-edit --size 512x512 \
  --out output/gpt-image-api/mascot-wave.gif --dry-run
```

Masks and markup cannot be combined with this experimental GIF route. Standard raster reference edits keep their existing behavior.

## Transparent GIFs and control mismatches

The official background parameter documents transparent PNG/WebP. A local OFOX check also returned transparent 2.6 GIFs with transparency in every decoded frame, so this CLI permits `background=transparent` with GIF and validates every frame. This provider observation does not establish transparency support across every account or endpoint. Inspect palette edges and disposal/compositing artifacts as well as alpha presence.

The same OFOX run returned nine frames at 200 ms even when different frame counts and delays were requested. An accepted request does not prove that the route honors those fields. The CLI preserves valid GIF bytes, warns when actual count, timing, or dimensions differ, and records requested and actual values separately. The output may remain useful; disclose unmet requirements before claiming a pass.

## Acceptance checks

1. Inspect actual GIF dimensions, frame count, per-frame durations, cycle duration, loop metadata, and unique decoded frame count in the JSON sidecar.
2. Play several cycles at the final display size. Check first-to-last continuity; `loop=0` means repeat forever and does not prove a seamless transition.
3. Inspect all frames for identity, product labels, hands/contact relationships, fixed geometry, background drift, and flicker. Multiple distinct frames do not prove smooth motion.
4. For transparency, inspect all frames and edges on contrasting backgrounds. Alpha validation alone does not establish edge quality.
5. Deliver the animation file itself. A static preview or sharing link may conceal a valid GIF.

[Kingy's direct API test](https://kingy.ai/blog/chatgpt-gifs-images-2-6-vs-2-5-hands-on-test/) found a looping product GIF with a visible reset jump and label artifacts. [Tencent's creator test](https://cloud.tencent.com/developer/article/2776489) found background drift and broken hand/object relationships. These observations motivate inspection; they are not universal model failure rates. See [community-practices.md](community-practices.md) for evidence scope.
