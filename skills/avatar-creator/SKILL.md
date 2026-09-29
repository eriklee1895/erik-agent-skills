---
name: avatar-creator
description: Use when creating or editing static avatar images, distinct-character families, same-character image sets, or looping avatar GIF/MP4 assets (头像、套图、动图). Includes 3D-rendered image styles; excludes Three.js pages, orbitable models, and interactive avatar runtimes.
---

# Avatar Creator

Create raster avatar images and looping media with consistent identity and
conditional human selection. Use the user's request and confirmed context before
asking. Interactive 3D runtimes are outside this skill's scope; do not build or
orchestrate them, or substitute a rendered image/video for requested interaction.

## Resolve only consequential gaps

| Request | Decision |
| --- | --- |
| One image or a precise edit | Produce it directly when the brief is sufficient. |
| An unspecified set | First distinguish different characters from variants of one character. |
| Different characters | Vary structure while retaining a shared style. |
| One character in several states | Lock identity; vary only the requested expressions, outfits, poses, or scenes. |
| Unspecified avatar asset | Clarify single image, image set, or animated media only when context does not resolve it. |
| Established character + “做动图” | Run the bundled fixed animation preset directly. |
| Explicit GIF/video | Use the fixed animation preset when it meets the request. |

Ask one focused question about the current branch, with a few choices when
helpful. For “一套 avatar”: “你想要多个不同角色供挑选，还是同一角色的表情、换装或场景套图？”
Use an available question tool or ordinary conversation; do not require a
particular harness UI. Do not ask about providers or every export parameter
upfront. Infer noncritical defaults and state them briefly. If the user delegates
all choices, choose a reasonable interpretation and proceed within that scope.

## Preserve decisions and selection boundaries

For multi-stage work, keep a short `avatar-brief.md` beside outputs: route,
reference roles, identity invariants, allowed variations, count/layout, export
constraints, selected candidate/file, completed artifacts, pending selection,
and generation attempts used/remaining when a limit exists. Distinguish confirmed
choices from assumptions. Simple edits need no brief file.

- An approved reference goes directly into production; do not reopen selection.
- When exploration is requested, make a small numbered candidate set. Wait before
  expansion if the user asked to choose; otherwise honor delegated selection.
- Reuse the selected master for every variant. Resume existing work on “继续”.
- Revisions change the affected constraints, not the entire approved brief.
- Honor existing attempt/cost limits across turns. Stop when exhausted and report
  failed results; delegated selection does not authorize unlimited retries.

## Produce the artifact

Read only the relevant reference:

- [Images and identity](references/images-and-identity.md): single images,
  distinct-character sheets, same-character sets, optional plush styling.
- [Motion and delivery](references/motion-and-delivery.md): the bundled fixed
  animation recipe, task recovery, and exports.

Discover available generation skills/tools and follow their current contracts.
Honor explicit provider choices and existing authorization. Images can use an
available image tool or `gpt-image-api` / `seedream-image-gen`; animated media uses
this skill's `scripts/animate_avatar.py`. The animation route needs no other
skill. Resolve image-generation skill locations through the environment, not
assumed sibling paths. Load only the
selected capability. Missing tools or credentials require a precise blocker;
do not silently install, switch an explicit provider, or substitute prompts for
requested finished media.

The bundled animation uses one image for both endpoints and a verbatim fixed
prompt (wave, turn, approach, return), with a fixed model and 10-second duration.
Do not rewrite this prompt or add character-specific motion instructions. If
explicit user constraints conflict with this preset, explain the mismatch before
generating; do not silently substitute another prompt, provider, or duration.

Inspect actual outputs against the brief. Deliver previews and usable file paths,
including separate files when requested. State any unverified identity fidelity,
loop continuity, or transparency; an API success alone is not visual acceptance.
