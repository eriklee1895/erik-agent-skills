# Character modeling from 2D references

Use the supplied illustration as the identity anchor. A generated turnaround is a
helper for hidden angles; it can invent details, so treat only visible source
features as facts.

## Read the reference before coding

Record the details that define recognition:

- outer silhouette and head-to-body proportions
- face placement, eye shape, mouth, markings, and expression
- hair, ears, horns, antennae, wings, tail, or other distinctive shapes
- clothing construction, accessory placement, palette, and material cues

If one image does not show a critical detail, keep it simple or ask for another
reference. Do not confidently invent a hidden logo, pattern, or identifying
feature from the generated back view.

## Build volume, then attach details

Start from the largest masses and work toward small features. Use ellipsoids for
rounded heads and bodies, curved tubes for antennae or tails, and extruded shapes
with thickness for wings, ears, fins, and other broad forms. Keep each animated
part in its own `THREE.Group`.

For a face on an ellipsoid with radii `rx`, `ry`, and `rz`, place a feature at
`z = centerZ + rz * sqrt(1 - (x/rx)^2 - (y/ry)^2)` when the expression is valid.
This keeps the feature on the curved front surface instead of floating in front
of it. Group the eyes and mouth under the head so they turn with it. Keep the
mouth on the surface and scale its opening from local microphone amplitude.

Check the model at front, three-quarter, and profile angles while building it.
The silhouette should change naturally as the camera orbits. Back and unseen
surfaces can be clean and restrained; they do not need invented decoration.

## Keep the image out of the model

Do not make the avatar a billboard, a thin front-facing shell, or a reference
image mapped onto a flat plane. Do not embed the source or turnaround image in
the delivered HTML unless the user asks for a visible reference card. Keep those
images as separate design files so the final HTML remains small and does not
carry an unnecessary copy of the user's artwork.

## Animate parts that exist

Return stable references for the root, head, eyes, mouth, and distinctive
moveable parts from `buildCharacter()`. Blend a small idle motion with a short
user-triggered gesture. Use restrained easing, reset each part to its neutral
pose, and honor `prefers-reduced-motion` for automatic motion. Manual controls
remain available when automatic motion is reduced.
