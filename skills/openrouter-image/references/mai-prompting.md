# Prompting MAI-Image-2.6 (`mai`)

Model: `microsoft/mai-image-2.6`, through OpenRouter's `/api/v1/images`.
Microsoft describes this tier around generation, multi-reference composition,
and controllable iterative edits. Use this guide to turn a brief, composition,
product assets, and style references into an explicit edit contract.

## Controls on this route

| Control | Supported values | CLI behavior |
|---|---|---|
| `--aspect` | 1:1, 4:3, 3:4, 16:9, 9:16, 3:2, 2:3, auto | default `1:1`; `auto` lets the model choose |
| `--image` | up to 5 references | includes any approved base |
| `--n` | 1 | separate calls for alternatives |
| quality / resolution / background / compression / mask | unavailable here | omit these flags |

Choose a fixed ratio for a series or a known placement. Use `auto` when the
composition may determine the frame. There is no 2K/4K selector in this CLI;
requesting a size in prose does not create an API control. Inspect actual
dimensions and legibility before committing to a delivery size.

MAI's upstream capabilities include web grounding. The checked OpenRouter Azure
endpoint lists `web_grounding` under `provider.options`, but this CLI exposes no
provider-options or grounding flag. For current facts, research outside the
generation call and supply verified facts and references. This alias does not
automatically invoke search, nor does it select MAI-Image-2.6 Flash.

## Generate from a design brief

Name the deliverable and its subject, then layout, materials, background, and
light. Give blank regions an explicit purpose and location so the composition
can accommodate later typesetting. Quote required copy separately.

```text
A square product visual for a cobalt-blue glass serum bottle with a smooth
black cap and a thin gold ring. One bottle stands upright in the lower-right
third on warm ivory stone, with a soft contact shadow. The background is a
continuous cream wall, lit from the upper left. Leave the upper-left half clear
for copy to be added later. No surrounding packaging, furniture, or lettering.
```

Use `generate --model mai --aspect 1:1`. If an exact product exists, pass its
reference and state the geometry and label details to preserve instead of
relying on a text-only reconstruction.

## Compose references by role and authority

MAI accepts up to five sources in one request. Use a reference for information
it actually supplies; five available slots are not a requirement to fill them.
Number sources in their real `--image` order and resolve conflicts explicitly:

| Example source | Authority |
|---|---|
| Approved composition | framing, camera, subject positions and scale |
| Person | face, hair, distinguishing identity details |
| Product | silhouette, cap, material, colors and verbatim label |
| Room | architectural details and background objects |
| Style board | palette and lighting treatment, without importing its objects |

Example for five supplied images in that order:

```text
Image 1 is the approved composition: keep its framing, camera angle, pose,
person position, and product scale. Image 2 supplies only the person's identity:
copper curls, freckles, and round tortoiseshell glasses. Image 3 supplies the
exact cobalt-blue bottle, black cap, thin gold ring, and label “ERIK LAB” /
“SERUM 21”. Image 4 supplies the room architecture and background furnishings;
adapt them to image 1's camera. Image 5 supplies only the muted palette and soft
side light; do not copy its objects or text.
Show one person holding one bottle. Where sources conflict, image 1 wins for
composition, image 2 for identity, and image 3 for product geometry and label.
```

Invoke `edit --model mai --image composition.png --image person.png
--image product.png --image room.png --image style.png --aspect 3:4`.
Inspect the face, fingers/contact, product proportions, label glyphs, and the
relationship between foreground light and background light. Accepting five
images does not guarantee five sources remain faithful.

## Continue from the approved result

Each call is stateless. For the next local edit, supply the approved output as
image 1 and lead with the requested change:

```text
Change only the back wall from cream to muted sage green. Keep the approved
composition, camera, person, freckles, glasses, hand pose, bottle silhouette,
cap, gold ring, and “ERIK LAB” / “SERUM 21” label. Preserve the light direction
and the existing contact shadows; no other design changes.
```

Use `edit --model mai --image approved.png --aspect 3:4`. If the face, product,
or label drifts, restart that edit from the last approved base and add the
original person/product references with explicit roles. The base remains the
framing authority. Base plus two originals uses three of the five slots;
reassess which sources are needed rather than appending to the original five.
For pixel-exact preservation outside a region, use deterministic compositing.

## Evidence and sources

OpenRouter controls were checked on 2026-11-05. Earlier application notes from
2026-11-04 observed 768×1024 at 3:4 and 1024×1024 at 1:1. Treat these as samples,
not a declared universal output ceiling. Short Chinese copy and a two-reference
edit worked in the small probe; five-reference capacity comes from the endpoint
descriptor, not a five-reference fidelity test. The new composition and
follow-up recipes above have not been paid-generation tested.

- [Microsoft model overview](https://microsoft.ai/models/mai-image-2-6/):
  multi-reference creation and controlled editing capabilities.
- [OpenRouter model](https://openrouter.ai/microsoft/mai-image-2.6)
  and [endpoint descriptor](https://openrouter.ai/api/v1/images/models/microsoft/mai-image-2.6/endpoints):
  supported controls and passthrough boundary.

For budget decisions, check current rates and actual `usage.cost`; reference
inputs and output tokens affect spend. Follow [model-routing.md](model-routing.md).
Application scenarios live in [evals.json](../evals/evals.json).
