# Prompting Grok Imagine Image 2.0 (`grok`)

Model: `x-ai/grok-imagine-image-2.0`, through OpenRouter's `/api/v1/images`.
Use this guide for subject-led stills, changes to an approved image, and
recomposition into a different frame. The recipe follows xAI's prompting guide;
it is not a claim that Grok outperforms the other aliases on these tasks.

## Controls on this route

| Control | Supported values | CLI behavior |
|---|---|---|
| `--resolution` | `1K`, `2K` | omitted when not supplied |
| `--quality` | `low`, `medium` | omitted when not supplied |
| `--aspect` | 1:1, 3:4, 4:3, 9:16, 16:9, 2:3, 3:2, 9:19.5, 19.5:9, 9:20, 20:9, 1:2, 2:1, auto | CLI default `1:1` |
| `--n` | 1 | separate calls for alternatives |
| `--image` | up to 3 references | order becomes reference numbering |
| background / compression / mask / search | unavailable here | no passthrough control in this CLI |

Resolution and quality are independent, optional controls. Pin them for
repeatable request settings; `--resolution 2K --quality medium` requests the
higher available detail settings, without guaranteeing fine text or identity.
The provider decides defaults when a field is absent; the CLI does not infer
them from the command name or reference count.

xAI's native examples use lowercase `2k`, separate generation/edit routes, and
also document quality `auto`. This CLI uses uppercase `2K`, `input_references`,
and only the `low`/`medium` values declared by OpenRouter. Do not copy native
request fields or defaults into this route.

## New image: make the subject recognizable

Lead with the subject, its visible form or action, and its setting. Then specify
materials and counts, art direction, light, colors, and crop. For a series,
keep this order and the camera language consistent. Describe physical surfaces
once rather than stacking synonyms or long negative lists.

Example brief for `--aspect 3:2 --resolution 2K --quality medium`:

```text
A sage-green ceramic coffee dripper rests on a clear glass carafe on a pale oak
counter. One dripper and one carafe, seen at counter height from a three-quarter
angle; the carafe is half full of dark amber coffee. The ceramic has a matte,
fine-grained glaze; the glass edge catches a narrow white highlight.
White square tiles behind the counter, one folded linen cloth at the left.
Window light enters from the right with soft fill on the shaded side.
Keep the green ceramic distinct from the warm wood and amber coffee.
One continuous product photograph, both vessels sharp, fully inside the frame.
```

For an illustration, state the drawing medium and visible treatment after the
subject and composition. Name the shapes, colors, and light that matter; an
anime or painterly style is a prompt choice, not a model-selection guarantee.
For in-image copy, quote every string, assign its position and occurrence count,
and inspect each glyph after generation.

## Edit: change first, then preserve

When the base already has the right subject and layout, pass that image again
and describe the specific change first. Follow with the attributes that must
remain. A full replacement scene prompt can restage the picture; a vague
instruction such as “more realistic” does not identify the failed feature.

```text
Change the jacket fabric to dark indigo denim with a visible diagonal weave.
Keep the same person, face, hair, pose, jacket cut, camera angle, crop, room,
and light direction. Change only the fabric and its material highlights.
```

Use `edit --model grok --image approved.png` with the desired aspect and detail
settings. Inspect face, silhouette, texture placement, and counts independently.
If the wrong object or major layout persists, revise the subject description
and return to the approved base instead of chaining unsuccessful edits.

## Reframe an approved image

Change the aspect through `--aspect`; describe how the composition should
occupy that frame. Distinguish elements that may move from properties to keep.

```text
Recompose image 1 into a 16:9 banner. Place the same person in the left third,
keeping their face, outfit, pose, and apparent scale consistent with the source.
Extend the existing room across the right side with matching perspective and
light. Leave the right half as a quiet wall area for a title to be added later.
Keep one person, fully recognizable, and do not add lettering or extra props.
```

Run with `edit --model grok --image approved.png --aspect 16:9
--resolution 2K --quality medium`. This is generative recomposition, not a
pixel-preserving crop or a mask operation. Inspect the new edges, subject scale,
perspective, and reserved title space.

For multiple references, assign each a role in `--image` order, for example
approved composition, identity, product. State which governs any conflict;
three total is the ceiling, including the approved base. Add original identity
or product references when they address drift, not automatically on every call.

## Evidence and sources

OpenRouter controls were checked on 2026-11-05. Earlier application notes from
2026-11-04 reported 2048×2048 at 1:1 and 1776×2368 at 3:4 using the 2K setting.
These are observed dimensions, not fixed edge limits or proof of internal
rendering detail. Short Chinese copy and a two-reference edit worked in that
small probe; this does not establish reliability or a cross-model ranking.
The recipes above are application guidance, not newly executed visual tests.

- [OpenRouter model](https://openrouter.ai/x-ai/grok-imagine-image-2.0)
  and [endpoint descriptor](https://openrouter.ai/api/v1/images/models/x-ai/grok-imagine-image-2.0/endpoints)
- [xAI prompting guide](https://docs.x.ai/developers/model-capabilities/images/prompting-guide)
  and [generation controls](https://docs.x.ai/developers/model-capabilities/images/generation)

For budget decisions, use current endpoint rates and actual `usage.cost`;
follow [model-routing.md](model-routing.md). Application scenarios live in
[evals.json](../evals/evals.json).
