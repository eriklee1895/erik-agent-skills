# Prompting Nano Banana 2 (`banana`)

Model: `google/gemini-3.1-flash-image` — Gemini 3.1 Flash Image, a.k.a. Nano
Banana 2. This is the only one of the three models whose prompting craft is not
documented elsewhere in the repo, so it lives here.

## What this model is good at

- **Multi-image fusion**: up to 14 reference images in one call. It handles
  "take the person from image 1, the location from image 2, the product from
  image 3" more naturally than single-pass models, with fewer identity crashes.
- **Grounding and instruction following**: long, specific natural-language scene
  descriptions are followed closely; real-world objects, materials, and text in
  scenes tend to look correct rather than invented.
- **Conversational edits**: describe the change in plain language ("swap the
  sign's date, keep everything else") and it preserves the rest of the image —
  this edit style originates from the consumer product and works well.
- **Extreme formats, natively**: ratios including 8:1 / 1:8 / 4:1, and genuine
  4K. Local verification confirmed a 21:9 request returned a native
  6336×2688 image with real detail density (not upscaled).

## Parameter model (different dialect from GPT)

| Lever | Values | Notes |
|---|---|---|
| `--resolution` | 512 / 1K / 2K / 4K | replaces "quality"; pick the pixel budget directly |
| `--aspect` | incl. 8:1, 4:1, 21:9, 1:1 | no `auto` — choose a shape |
| references | up to 14 | repeated `--image` |
| n | always 1 | no variants per call — rerun for alternatives |

There is **no `quality`, no background control, and no transparency** on the
dedicated endpoint; the CLI rejects those flags rather than silently ignoring
them. Note the dedicated images endpoint is not streaming, but the same model
via `chat/completions` (with image modality) can stream tokens — a different
path with a different response shape.

## Prompting patterns that work

**Fusion with many references — number every image and state its role:**

```text
Image 1 is the person; image 2 is the building entrance; image 3 is the jacket.
Place the same person from image 1, wearing the jacket from image 3, standing at
the entrance in image 2. Match the light direction of image 2 and keep the
person's face identical to image 1.
```

Role-labeling matters more the more images you supply — without it the model has
to guess which reference supplies identity vs style vs background.

**Conversational edit — one change, then say what stays:**

```text
Change the date on the sign from "3月15日" to "4月8日", same font, size and
color. Keep the sign's position, the wall, the lighting and every other pixel
unchanged.
```

**Ultra-wide / ultra-tall — describe zones, not one centered subject:**

For 8:1 or 21:9, an image built around a single centered subject wastes the
format. Describe content across the width ("left: …; center: …; right: …") so the
canvas is actually used.

## When NOT to use banana — pick a GPT model instead

- **Exact typography as the deliverable** (many verbatim labels, precise counts,
  strict hierarchy): sunburst is more reliable.
- **Transparent PNG**: impossible on banana — no alpha control. Use
  sunburst/flare with `--background transparent`.
- **Multiple variants in one call**: banana returns one image; the GPT models
  return up to 10 via `--n`.

## Variance: review critical content

Nano Banana 2 has noticeable per-call variance. In same-day side-by-side
probes, one run rendered all fixed Chinese text flawlessly while another
duplicated a phrase ("时代时代") and a 国风 prompt picked up stray gibberish
small characters. Treat any single output as one sample, not a guarantee:

- For text/critical deliverables, read every string in the result.
- If a result needs another attempt, account for the extra generation cost.
- Treat ratio/resolution as best effort; accept provider dimensions unless the
  user explicitly requires exact pixels.
- When the brief is fixed across many images, batch one-job-per-line and
  expect to regenerate a fraction of them.

## Workarounds

- Need transparency: generate the subject on a clean flat background and run a
  downstream cutout (e.g. rembg). Edges will be cutout-quality, not native
  soft-alpha — prefer a GPT model when the edge matters.
- Need several candidates: issue separate calls (a batch JSONL runs one job
  at a time).
