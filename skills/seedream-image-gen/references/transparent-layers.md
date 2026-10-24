# Transparent editing and native layer decomposition

The official [Pro/Flash tutorial](https://www.volcengine.com/docs/ark/seedream-5-0-pro) and [API](https://www.volcengine.com/docs/ark/image-generation-api), checked 2026-10-24, expose both functions on the common Images API. Earlier skill guidance that these capabilities were limited to a demo UI is superseded.

## Preserve alpha while editing

`edit --background transparent --output-format png` requires one alpha-bearing reference. A text-only request or a JPEG reference does not meet the contract. The current local outpaint canvas is opaque and cannot use this mode. URL references are validated by the service; local files are checked before generation.

A typical workflow is: decompose an opaque poster → edit one returned PNG layer while preserving alpha → place the edited layer back into the base using its saved bounding box.

## Extract layers

```bash
uv run scripts/seedream_image_gen.py decompose --model flash \
  --reference-image poster.png --size 1.5K --out-dir output/layers \
  --prompt '只拆出杯子和顶部标题，其余内容保留在底图。'
```

Omit the prompt for automatic element selection. For crowded scenes, specify objects plus `<bbox>` tags; edit/decomposition prompt tags use normalized 0–999 coordinates. A requested count in prose is not a hard API output limit. The service may return one base and up to sixteen layers, each billed as an output.

The source must be one PNG/JPEG, ≤30MB, 262,144–36M pixels and aspect ratio at most 16:1. `size` is auto/1K/1.5K/2K. `auto` does not promise to preserve tiny elements at their exact original pixels; consult the native size rules.

`--output-format` selects the base encoding only. Foreground layers are always PNG. The CLI saves actual per-image encoding and dimensions, so a JPEG base and small alpha crops retain their own formats instead of all being resized to the canvas size.

## Manifest and coordinates

`layers.json` contains model, extraction prompt, size tier, usage, API time and a `layers` array. Each entry has a local `file`, z-index, actual size/format, reported size and the available bbox/name/description. No response URL, data URL or credential is saved.

- z-index zero is the base; larger indices are above it.
- `bounding_box.absolute` uses **output-base pixels**, formatted [left, top, right, bottom]. It need not use the original input's canvas dimensions.
- `bounding_box.normalized` uses **0–1000**, not edit prompt tags' 0–999. Scale these bounds against a target canvas if it changes size.
- Cropped PNG dimensions need not equal bbox dimensions. Resize to the bbox before placement.

Example local reconstruction, run from the output folder:

```python
import json
from PIL import Image

manifest = json.load(open("layers.json", encoding="utf-8"))
items = sorted(manifest["layers"], key=lambda item: item["z_index"])
base = Image.open(items[0]["file"]).convert("RGBA")
for item in items[1:]:
    left, top, right, bottom = item["bounding_box"]["absolute"]
    layer = Image.open(item["file"]).convert("RGBA")
    layer = layer.resize((right - left, bottom - top), Image.Resampling.LANCZOS)
    base.alpha_composite(layer, (left, top))
base.save("recomposed.png")
```

This reconstructs the returned generated base and layers. It does not establish pixel-identical recovery of the input: removal/inpainting and extracted edges can differ. Judge edge quality, semantic selection and reconstruction on the actual sample.

Use a fresh output directory, or explicitly allow replacement with `--force`. A lost response or download failure must not trigger a second paid decomposition automatically. Decomposition is an API multi-output mode, so the single-image guarantee for ordinary generation does not apply to it.
