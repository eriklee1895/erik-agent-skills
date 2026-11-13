# Seedream 5.5 transparency, decomposition and rich-text OCR

Verified against the official [5.5 tutorial](https://console.volcengine.com/ark/region:cn-beijing/docs/seedream-5-5), [Images API](https://console.volcengine.com/ark/region:cn-beijing/docs/image-generation-api) and [OCR fonts](https://console.volcengine.com/ark/region:cn-beijing/docs/ocr-supported-fonts), 2026-11-14. [Live benchmark](../evals/seedream55-benchmark.md) distinguishes observed behavior from documented limits.

## Native RGBA generation

5.5 can generate RGBA from text, one ordinary RGB/alpha reference, or up to ten references. Send `background: transparent` and `output_format: png`. No decomposition step is required for a single isolated subject. Explicitly describe which elements remain and which background disappears; include a shadow only if desired. Default `auto` is model-chosen; use explicit transparent mode when alpha is required.

Decode the downloaded PNG and inspect its alpha range, fully transparent fraction and partial-alpha fraction. Composite onto light and dark backgrounds. A PNG/checkerboard preview or partial-alpha edge alone cannot prove physically plausible glass, smoke or shadow. Generative extraction may change a subject; compare identity and contours with the input.

Legacy 5.0 Pro/Flash only support transparent editing with exactly one alpha-bearing input. The CLI retains that validation for those models.

## Decomposition request

```json
{
  "model": "doubao-seedream-5-5-261028",
  "image": "https://example.com/poster.png",
  "layer_decomposition": true,
  "layer_decomposition_options": {"max_images": 20, "text_recognition": true},
  "size": "auto",
  "output_format": "png",
  "watermark": false
}
```

`prompt` is optional; omit it for automatic splitting or name elements to extract. Spatial tags can identify subjects. Do not pass `background` in decomposition mode. This is one source image to a base plus transparent foregrounds; a prompt requesting a “layer illustration” in ordinary generation does not invoke it.

- `max_images`: 2–100, default 30, including the base. It is an upper bound, not a guaranteed layer count. The API reserves IPM using this value and releases unused quota; this is separate from monetary billing.
- `text_recognition`: false by default; true adds rich-text OCR to eligible text layers. 5.5 only.
- Input: one PNG/JPEG, ≤30 MB, 262,144–36M pixels, aspect at most 16:1.
- `size`: auto/1K/1.5K/2K. The base follows the source aspect; foreground crops can be enlarged independently. Their dimensions need not match their bbox dimensions.
- `output_format` chooses the base encoding only; foregrounds remain PNG. One failed output makes the server request fail as a whole.

Use a fresh output folder or explicit `--force`. A missing response or failed download does not authorize another paid decomposition automatically.

## Manifest and coordinates

`layers.json` preserves request model/options, timing/usage and a `layers` array with local `file`, `z_index`, decoded size/format, reported size and available `bounding_box`, `name`, `description`, `background`, `text_recognition`. It excludes signed URLs and base64.

- z-index 0 is the base; foregrounds are stacked in ascending z-index, up to 99.
- `bounding_box.absolute` = `[left, top, right, bottom]` in **output-base pixels**, not original-source pixels or crop pixels.
- `bounding_box.normalized` = matching bounds in **0–1000**. Prompt `<bbox>` tags instead use 0–999.
- Both layer and OCR line boxes use the base coordinate system. Scale them if the target canvas changes.

Reconstruction from the manifest, run in the output folder:

```python
import json
from PIL import Image

manifest = json.load(open("layers.json", encoding="utf-8"))
items = sorted(manifest["layers"], key=lambda item: item["z_index"])
base = Image.open(items[0]["file"]).convert("RGBA")
for item in items[1:]:
    left, top, right, bottom = item["bounding_box"]["absolute"]
    crop = Image.open(item["file"]).convert("RGBA")
    crop = crop.resize((right - left, bottom - top), Image.Resampling.LANCZOS)
    base.alpha_composite(crop, (left, top))
base.save("recomposed.png")
```

This reconstructs generated layers, not pixel-identical recovery of the source. Check inpainted background, inter-object shadows, halos, haze and occlusions. PSD packaging and native editable text objects require a downstream tool.

## Select and classify layers

The Ark schema supplies semantic `name` / `description`, not a documented `layer_type` or `role` enum. Use `z_index=0` for the base; `text_recognition` identifies an OCR-bearing regular-text layer. For other layers, inspect the crop plus its name/description to decide whether it is a subject, decoration, raster text or a mixed group. **Missing OCR does not prove absence of text**: artistic lettering or text embedded in an object can remain raster-only. Preserve the original metadata and treat application-level categories as derived labels, not model fields.

## OCR structure and text replacement

Each eligible `data[]` / manifest layer can contain:

```json
{
  "text_recognition": {
    "text": "GREEN STUDIO\nOPEN DAY",
    "lines": [{
      "bounding_box": {"absolute": [90, 80, 780, 155], "normalized": [59, 78, 508, 151]},
      "runs": [{
        "text": "GREEN STUDIO",
        "style": {
          "similar_font_family": "Arial", "foreground_color": "#173E36",
          "bold": false, "italic": false, "underline": false,
          "strikethrough": false, "shadow": false, "translucent": false
        }
      }]
    }]
  }
}
```

`text` joins lines in reading order; each line contains style-consistent runs. `similar_font_family` is an approximate visual match, or `unknown`; `foreground_color` is uppercase `#RRGGBB` without alpha. The six booleans represent bold, italic, underline, strikethrough, shadow and translucent ink. Rotating a line does not imply italic; pale opaque ink does not imply translucent.

The [font catalog](https://console.volcengine.com/ark/region:cn-beijing/docs/ocr-supported-fonts) lists 101 Chinese and 127 foreign fonts. Recognition does not supply font files or a license. Font size, exact glyph metrics, baseline, tracking and a numeric ink-opacity value are not supplied by this schema. Do not invent them.

For local copy changes:

1. Find the intended text layer by OCR content and inspect its crop. Check for other objects/text sharing it.
2. Compose the base and other layers, omitting the text layer being replaced. If one layer contains several lines, re-render every retained line from that layer too.
3. Use an installed/provided font matching `similar_font_family`, or choose a disclosed substitute. Use each line's **base-coordinate bbox**, not the crop's own top-left, and fit replacement text into it. Render each run's supported style; treat unknown properties as approximation.
4. Inspect accents, scripts, line breaks, overflow, style and text correctness at final size. This changes local text without another generation call. Do not promise exact design-file recovery.

Generative localization remains available via `edit`, but preservation is probabilistic. For several markets, derive each from the same accepted original instead of chaining translations of prior markets.
