#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.27.0",
#   "pillow>=10.0.0",
# ]
# ///
"""Generate, edit, outpaint, and batch-generate images with Seedream 5.0 Pro (default) / 5.0 Flash
via the Volcengine Ark API (one shared Pro/Flash endpoint).

Subcommands:
  generate         Create a new image from a text prompt (default: Pro / 2K / URL download).
  edit             Modify an image — supports marker-based region edits (colored-rect protocol),
                   reference-based style transfer, character consistency, and outpainting.
  generate-batch   Run many generation jobs from a JSONL file.
  decompose        Extract a base image and transparent foreground layers.
  list-models      Print the known model table and exit.

API docs:
  Seedream 5.0 Pro: https://www.volcengine.com/docs/82379/1824121
  API reference:   https://www.volcengine.com/docs/82379/1541523

Examples live in SKILL.md.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import datetime as dt
import getpass
from io import BytesIO
import json
import math
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, NamedTuple, Optional

import httpx
from PIL import Image, ImageDraw, ImageOps


# ---------------------------------------------------------------------------
# Model registry — add models here; everything else (validation, body shaping)
# derives from the capability dict.
# ---------------------------------------------------------------------------

MODEL_PRO = "doubao-seedream-5-0-pro-260628"
MODEL_FLASH = "doubao-seedream-5-0-flash-260915"
MODEL_PRO_ALIASES = {"pro", "seedream-pro", "5-pro", "seedream-5-pro", "doubao-seedream-5-0-pro"}
MODEL_FLASH_ALIASES = {"flash", "seedream-flash", "5-flash", "seedream-5-flash", "doubao-seedream-5-0-flash"}
RETIRED_MODELS = {
    "lite", "seedream-lite", "5-lite", "seedream-5-lite", "doubao-seedream-5-0",
    "doubao-seedream-5-0-lite", "doubao-seedream-5-0-260128", "doubao-seedream-5-0-lite-260128",
}
_COMMON_CAPS: dict[str, Any] = {
    "size_strings": {"1K", "1.5K", "2K"},
    "pixel_min": 921_600,
    "pixel_max": 4_624_220,
    "aspect_max": 16,
    "default_size": "2K",
    "max_refs": 10,
}
MODELS: dict[str, dict[str, Any]] = {
    MODEL_PRO: {
        **_COMMON_CAPS,
        "aliases": MODEL_PRO_ALIASES,
        "label": "Seedream 5.0 Pro (2026-06-28 build)",
        "optimize_modes": {"standard", "fast"},
        "price_per_image": "2026-10-24 list: generation <=2.61MP CNY0.30 / larger CNY0.60; layers CNY0.15/0.30",
        "notes": "Default quality model; standard/fast, coordinate/marker edits, alpha-image editing and layer decomposition.",
    },
    MODEL_FLASH: {
        **_COMMON_CAPS,
        "aliases": MODEL_FLASH_ALIASES,
        "label": "Seedream 5.0 Flash (2026-09-15 build)",
        "optimize_modes": {"standard"},
        "price_per_image": "2026-10-24 list: CNY0.12/output image; input images free",
        "notes": "Lower-latency/cost model; same generation/edit/layer API, standard mode only.",
    },
}

DEFAULT_MODEL = MODEL_PRO
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_OUTPUT_DIR = "output/seedream-image-gen"
DEFAULT_OUTPUT_FORMAT = "png"
DEFAULT_TIMEOUT = 300
DEFAULT_CONCURRENCY = 3
DEFAULT_MAX_N = 4
MAX_RETRIES = 8
RETRY_BACKOFF = (2.0, 4.0, 8.0, 16.0, 30.0, 30.0, 30.0, 30.0)
MAX_REFERENCE_BYTES = 30 * 1024 * 1024
MAX_PROMPT_CHARS = 6_000
ALLOWED_OUTPUT_FORMATS = ("png", "jpeg", "jpg")

# Automatic marker-cleanup suffix appended after the user's edit prompt (unless
# --no-marker-cleanup-prompt is passed). Selected by prompt language heuristic.
MARKER_CLEANUP_ZH = "图中彩色方框/圆圈/涂写是我手工标出的编辑区域标记，请严格按上面的描述修改标记区域内的内容，标记区域之外的像素尽量保持不变，完成后清除所有彩色标记线条与填充。"
MARKER_CLEANUP_EN = "The colored rectangles/circles/scribbles in the image are edit markers I drew by hand. Apply the change described above strictly inside the marked regions, keep pixels outside the markers unchanged, and remove all colored marks once done."

# Outpaint auto-prompt suffix (Chinese-first, since Pro prefers Chinese prompts).
OUTPAINT_FILL_ZH = "画布中央是原图片，请自然延伸填充四周的空白区域，使整张图变成一张完整的{aspect_word}图片，延续原有的风格、光照、色调与材质，不要让中心与新填充区域有可见接缝。"
OUTPAINT_FILL_EN = "The center of this canvas is the original image. Naturally extend and fill the surrounding blank areas to make one complete {aspect_word} image, matching the original style, lighting, palette and materials. No visible seam between center and extended regions."


class ImageOutput(NamedTuple):
    content: bytes
    size: Optional[str] = None
    output_format: Optional[str] = None
    z_index: Optional[int] = None
    bounding_box: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _load_dotenv() -> None:
    """Load .env from cwd, only setting keys not already in the environment."""
    env_path = Path.cwd() / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in {"'", '"'}:
            val = val[1:-1]
        if key and key not in os.environ and val:
            os.environ[key] = val


def _die(message: str, code: int = 1) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def _warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def _info(message: str) -> None:
    print(message, file=sys.stderr)


def _slugify(value: str, max_len: int = 60) -> str:
    """Turn a prompt snippet into a safe filename component."""
    value = value.strip().lower()
    value = re.sub(r"[^\w一-鿿]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value[:max_len] if value else "image"


def _now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _now_slug() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def _looks_chinese(text: str) -> bool:
    """Rough CJK-detection for choosing between zh/en cleanup prompts."""
    cjk = sum(1 for ch in text if "一" <= ch <= "鿿")
    return cjk >= 2


# ---------------------------------------------------------------------------
# Model resolution
# ---------------------------------------------------------------------------


def _resolve_model(model_arg: str) -> tuple[str, dict[str, Any]]:
    """Map user-supplied --model (alias or full id) to (canonical_id, capabilities)."""
    if not model_arg:
        return DEFAULT_MODEL, MODELS[DEFAULT_MODEL]

    if model_arg.lower().strip() in RETIRED_MODELS:
        _die("Seedream Lite is retired from this skill. Choose --model flash or --model pro explicitly; no automatic remapping.")

    # Exact id match
    if model_arg in MODELS:
        return model_arg, MODELS[model_arg]

    # Alias match
    needle = model_arg.lower().strip()
    for mid, caps in MODELS.items():
        if needle in caps["aliases"] or needle == mid.lower():
            return mid, caps

    # Pass through unknown model id (user might be using a fresh dated version we
    # haven't registered) — apply Pro defaults but warn.
    _warn(
        f"Unknown model id '{model_arg}'. Using Pro-capability defaults; "
        f"if this is a newer dated Pro build, things should work. Pass the full id "
        f"silently if you know what you're doing."
    )
    return model_arg, MODELS[DEFAULT_MODEL]


def _model_is_pro(model_id: str) -> bool:
    return model_id == MODEL_PRO or model_id in MODELS.get(MODEL_PRO, {}).get("aliases", set())


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def _get_api_settings() -> tuple[str, str]:
    """Return (api_key, base_url)."""
    api_key = os.getenv("ARK_API_KEY")
    base_url = os.getenv("ARK_BASE_URL") or os.getenv("MODEL_IMAGE_API_BASE") or DEFAULT_BASE_URL

    if not api_key:
        if sys.stdin.isatty() and sys.stdout.isatty():
            try:
                api_key = getpass.getpass(
                    "ARK_API_KEY is missing. Enter your Volcengine Ark API key: "
                ).strip()
            except (EOFError, KeyboardInterrupt):
                api_key = None
        if not api_key:
            _die(
                "ARK_API_KEY is required. Set it in your shell or .env, for example:\n"
                "  export ARK_API_KEY='your-key-here'\n"
                "  Get your key at: https://console.volcengine.com/ark/region:ark+cn-beijing/apikey"
            )

    return api_key, base_url.rstrip("/")


# ---------------------------------------------------------------------------
# Size parsing & model-aware validation
# ---------------------------------------------------------------------------


_SIZE_STRING_PIXELS: dict[str, int] = {
    # Resolutions here are nominal buckets — the server picks the exact pixel
    # dimensions. We only need total pixels for client-side range validation.
    "1K": 1_048_576,   # ~1MP, 1024²
    "1.5K": 2_359_296,
    "2K": 4_194_304,   # ~4MP, 2048²
    "3K": 9_437_184,   # ~9MP, 3072²
    "4K": 16_777_216,  # 16MP, 4096²
}


def _apply_size_shortcuts(
    size: Optional[str], wechat_header: bool, square: bool, wide: bool,
    portrait: bool, landscape: bool, phone: bool, caps: dict[str, Any],
) -> str:
    """Both active models share the same explicit-size bounds and shortcuts."""
    if phone:
        return "1152x2048"
    if wechat_header or wide:
        return "1792x1024"
    if square:
        return "1024x1024"
    if portrait:
        return "1536x2048"
    if landscape:
        return "2048x1152"
    return size or caps["default_size"]


def _validate_size(
    size: str,
    caps: dict[str, Any],
    model_id: str,
    *,
    enforce_min: bool = True,
) -> tuple[int, int]:
    """Validate --size against model capabilities. Returns (width, height) for WxH sizes,
    or (0, 0) for preset strings (the server resolves those).

    When enforce_min is False, sizes below pixel_min are returned so the caller can
    auto-upscale; aspect and pixel_max are still enforced.
    """
    size_upper = size.upper()
    if size_upper in caps["size_strings"]:
        return (0, 0)  # preset, server resolves

    # Common shortcuts
    if size_upper == "1K" and size_upper not in caps["size_strings"]:
        _die(
            f"Size '1K' is not supported by model {model_id}. "
            f"Allowed presets: {sorted(caps['size_strings'])}. "
            f"Use an explicit WxH (e.g. 2560x1440) or pick a larger preset."
        )
    if size_upper in {"3K", "4K"} and size_upper not in caps["size_strings"]:
        _die(
            f"Size '{size_upper}' is not supported by model {model_id}. "
            f"Pro/Flash top out at 2K (~4.6MP method-1 pixel cap). Allowed presets: {sorted(caps['size_strings'])}."
        )

    m = re.fullmatch(r"(\d{3,5})x(\d{3,5})", size)
    if not m:
        _die(
            f"Invalid size '{size}'. Use '1K'/'1.5K'/'2K' (subject to model), or WIDTHxHEIGHT "
            f"(e.g. '1024x1024', '1792x1024', '2560x1440')."
        )

    w, h = int(m.group(1)), int(m.group(2))
    total = w * h
    aspect = max(w, h) / min(w, h)

    if total < caps["pixel_min"] and enforce_min:
        _die(
            f"Size {size}: {total:,} pixels is below the {caps['pixel_min']:,} pixel floor "
            f"for {model_id}. {caps.get('size_floor_hint', '')}"
            f"Pass a larger size, or omit --no-auto-upscale to generate larger and downscale."
        )
    if total > caps["pixel_max"]:
        _die(
            f"Size {size}: {total:,} pixels exceeds the {caps['pixel_max']:,} pixel cap "
            f"for {model_id}."
        )
    if aspect > caps["aspect_max"]:
        _die(f"Size {size}: aspect ratio {aspect:.1f}:1 exceeds maximum {caps['aspect_max']}:1.")

    return (w, h)


def _smallest_valid_size(
    w: int,
    h: int,
    pixel_min: int,
    pixel_max: int,
) -> tuple[int, int]:
    """Smallest same-aspect WxH with total pixels >= pixel_min.

    Rounds each side up to a multiple of 8 while preserving aspect as closely as
    possible (e.g. 1500x600 → 1520x608). Falls back to a clean integer scale
    (2x/3x/…) when the 8-aligned size would exceed pixel_max.
    pixel_min is 921_600 for Pro (official 1280×720 / ~0.92MP floor) — see MODELS.
    """
    if w * h >= pixel_min:
        return w, h

    factor = math.sqrt(pixel_min / (w * h))
    nw = math.ceil(w * factor / 8) * 8
    nh = math.ceil(h * factor / 8) * 8
    while nw * nh < pixel_min:
        if (nw + 8) / w <= (nh + 8) / h:
            nw += 8
        else:
            nh += 8
    if pixel_min <= nw * nh <= pixel_max:
        return nw, nh

    for scale in range(2, 9):
        iw, ih = w * scale, h * scale
        if pixel_min <= iw * ih <= pixel_max:
            return iw, ih

    _die(
        f"Cannot auto-upscale {w}x{h} to reach the {pixel_min:,} pixel floor "
        f"without exceeding the {pixel_max:,} pixel cap. Pick a different size."
    )
    return w, h  # unreachable


def _maybe_downscale(
    img_bytes: bytes,
    downscale_to: Optional[tuple[int, int]],
    output_format: str,
) -> bytes:
    """LANCZOS-downscale API output to the exact user-requested size, if any."""
    if not downscale_to:
        return img_bytes
    from io import BytesIO

    tw, th = downscale_to
    with Image.open(BytesIO(img_bytes)) as im:
        im.load()
        resized = im.resize((tw, th), Image.Resampling.LANCZOS)
        buf = BytesIO()
        fmt = "JPEG" if output_format == "jpeg" else "PNG"
        if fmt == "JPEG":
            if resized.mode in ("RGBA", "P", "LA"):
                resized = resized.convert("RGB")
            resized.save(buf, format=fmt, quality=95)
        else:
            if resized.mode == "P":
                resized = resized.convert("RGBA")
            resized.save(buf, format=fmt)
        return buf.getvalue()


# ---------------------------------------------------------------------------
# Reference image handling (encoding + marker annotation + outpaint padding)
# ---------------------------------------------------------------------------


def _is_url(path: str) -> bool:
    return path.startswith(("http://", "https://"))


def _validate_transparent_input(paths: list[str], output_format: str) -> None:
    if len(paths) != 1:
        _die("Transparent editing requires exactly one alpha-bearing reference image.")
    if output_format != "png":
        _die("Transparent editing requires PNG output, not JPEG.")
    if not _is_url(paths[0]):
        try:
            with Image.open(Path(paths[0]).expanduser()) as image:
                if "A" not in image.getbands() and "transparency" not in image.info:
                    _die("Transparent editing requires an input image with an alpha channel.")
        except OSError as error:
            _die(f"Cannot read transparent reference: {error.__class__.__name__}")


def _encode_local_image(path: Path) -> str:
    """Base64-encode a local image file as data URL."""
    if not path.is_file():
        _die(f"Reference image not found: {path}")

    size = path.stat().st_size
    if size > MAX_REFERENCE_BYTES:
        _warn(f"Reference image exceeds 30MB limit: {path} ({size:,} bytes)")

    ext = path.suffix.lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/{ext};base64,{b64}"


def _encode_reference(path_or_url: str) -> str:
    if _is_url(path_or_url):
        return path_or_url
    p = Path(path_or_url).expanduser().resolve()
    return _encode_local_image(p)


def _resolve_reference_images(paths: list[str]) -> list[str]:
    return [_encode_reference(p) for p in paths]


# ---- Parsing marker rect strings ------------------------------------------------

_RECT_PERCENT = re.compile(r"^\s*(\d+(?:\.\d+)?)%\s*,\s*(\d+(?:\.\d+)?)%\s*,\s*(\d+(?:\.\d+)?)%\s*,\s*(\d+(?:\.\d+)?)%\s*$")
_RECT_PIXEL = re.compile(r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$")


def _parse_marker_rect(spec: str) -> tuple[float, float, float, float, bool]:
    """Parse an --marker-rect spec. Returns (x, y, w, h, is_percent).
    Coordinates are left/top offsets + width/height, consistent with Pillow and
    most graphics tools. Percent values are relative to image dimensions.
    """
    spec = spec.strip()
    mp = _RECT_PERCENT.match(spec)
    if mp:
        return (float(mp.group(1)), float(mp.group(2)), float(mp.group(3)), float(mp.group(4)), True)
    mpx = _RECT_PIXEL.match(spec)
    if mpx:
        return (float(mpx.group(1)), float(mpx.group(2)), float(mpx.group(3)), float(mpx.group(4)), False)
    _die(
        f"Invalid marker rect '{spec}'. Use X,Y,W,H in pixels (e.g. 100,200,800,300) "
        f"or percent (e.g. 10%,20%,60%,15%)."
    )
    return (0, 0, 0, 0, False)  # unreachable


def _parse_color(spec: str) -> tuple[int, int, int]:
    """Parse #RRGGBB (with or without leading #) into (r,g,b)."""
    s = spec.strip().lstrip("#")
    if len(s) != 6:
        _die(f"Invalid marker color '{spec}'. Use #RRGGBB (e.g. #ff0000).")
    try:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except ValueError:
        _die(f"Invalid marker color '{spec}'. Use #RRGGBB (e.g. #ff0000).")
        return (0, 0, 0)


def _apply_markers(src_path: Path, rects: list[tuple[float, float, float, float, bool]],
                   colors: list[tuple[int, int, int]], fill_alpha: int, stroke_width: int,
                   *, preserve_alpha: bool = False) -> bytes:
    """Draw semi-transparent rectangles on a copy of the source image and return
    the annotated image as PNG bytes.

    `colors` is parallel to `rects` so each region can be its own color (red/blue/green for
    multi-region prompts like "红框替换标题，蓝框改帽子"). When a single color is supplied
    (legacy --marker-color without repeats), all rects use that color. Transparent edits
    retain alpha, including visible marker overlays on otherwise empty pixels.
    """
    img = Image.open(src_path).convert("RGBA")
    # Honor EXIF orientation (phone photos may be stored rotated; transpose so
    # pixel coordinates match what the user sees on screen).
    img = ImageOps.exif_transpose(img)
    W, H = img.size

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # If caller gave one color for many rects, repeat it; if they gave one per rect, zip.
    if len(colors) == 1:
        colors = colors * len(rects)
    elif len(colors) < len(rects):
        colors = colors + [colors[-1]] * (len(rects) - len(colors))

    for (x, y, w, h, is_percent), color in zip(rects, colors):
        if is_percent:
            x_px = int(round(x / 100.0 * W))
            y_px = int(round(y / 100.0 * H))
            w_px = int(round(w / 100.0 * W))
            h_px = int(round(h / 100.0 * H))
        else:
            x_px, y_px, w_px, h_px = int(x), int(y), int(w), int(h)

        box = [x_px, y_px, x_px + w_px, y_px + h_px]
        fill_rgba = (*color, fill_alpha)
        draw.rectangle(box, fill=fill_rgba, outline=color, width=stroke_width)

    combined = Image.alpha_composite(img, overlay)
    if not preserve_alpha:
        combined = combined.convert("RGB")
    buf = _BytesIO()
    combined.save(buf, format="PNG")
    return buf.getvalue()


# Outpaint directions → (left, top, right, bottom) pixel paddings.
_OUTPAINT_DIRS = {"left", "right", "top", "bottom", "up", "down", "l", "r", "t", "b"}


def _parse_outpaint(spec: str) -> tuple[str, int]:
    if ":" not in spec:
        _die(f"Invalid --outpaint '{spec}'. Use direction:pixels (e.g. left:400, right:400).")
    d, px = spec.split(":", 1)
    d = d.strip().lower()
    if d not in _OUTPAINT_DIRS:
        _die(f"Invalid outpaint direction '{d}'. Use left/right/top/bottom (or l/r/t/b).")
    try:
        n = int(px)
    except ValueError:
        _die(f"Invalid pixel count '{px}' in --outpaint {spec}.")
    if n <= 0 or n > 8192:
        _die(f"Outpaint pixel count out of range (1-8192): {n}")
    # canonicalize
    if d == "up": d = "top"
    if d == "down": d = "bottom"
    if d == "l": d = "left"
    if d == "r": d = "right"
    if d == "t": d = "top"
    if d == "b": d = "bottom"
    return (d, n)


def _apply_outpaint(src_path: Path, paddings: dict[str, int]) -> tuple[bytes, str, tuple[int, int]]:
    """Create a larger canvas, paste the source in the center (offset per paddings),
    fill the new area with a neutral color sampled from the image edge average,
    return PNG bytes + an aspect-word hint for the auto-prompt.
    """
    img = Image.open(src_path).convert("RGB")
    img = ImageOps.exif_transpose(img)
    W, H = img.size
    pl = paddings.get("left", 0)
    pr = paddings.get("right", 0)
    pt = paddings.get("top", 0)
    pb = paddings.get("bottom", 0)

    new_W = W + pl + pr
    new_H = H + pt + pb

    # Sample a neutral background color from a 20px edge strip — good enough as
    # a seam-masking base; the model will repaint the padded area anyway.
    import statistics
    edge_pixels: list[tuple[int, int, int]] = []
    # top edge
    edge_pixels.extend([img.getpixel((x, 0)) for x in range(0, W, max(1, W // 50))])
    edge_pixels.extend([img.getpixel((x, H - 1)) for x in range(0, W, max(1, W // 50))])
    edge_pixels.extend([img.getpixel((0, y)) for y in range(0, H, max(1, H // 50))])
    edge_pixels.extend([img.getpixel((W - 1, y)) for y in range(0, H, max(1, H // 50))])
    avgr = int(statistics.mean(p[0] for p in edge_pixels))
    avgg = int(statistics.mean(p[1] for p in edge_pixels))
    avgb = int(statistics.mean(p[2] for p in edge_pixels))

    canvas = Image.new("RGB", (new_W, new_H), (avgr, avgg, avgb))
    canvas.paste(img, (pl, pt))

    buf = _BytesIO()
    canvas.save(buf, format="PNG")

    aspect = new_W / new_H
    if aspect > 1.5:
        word = "横版 16:9"
    elif aspect < 0.75:
        word = "竖版 9:16"
    else:
        word = f"{new_W}×{new_H}"

    return (buf.getvalue(), word, (new_W, new_H))


# Lazy import alias so we can construct BytesIO at module level without an extra
# import line in each helper.
from io import BytesIO as _BytesIO  # noqa: E402


def _encode_png_bytes(png_bytes: bytes, ext: str = "png") -> str:
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/{ext};base64,{b64}"


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------


def _read_prompt(prompt: Optional[str], prompt_file: Optional[str]) -> str:
    if prompt and prompt_file:
        _die("Use --prompt or --prompt-file, not both.")
    if prompt_file:
        p = Path(prompt_file)
        if not p.is_file():
            _die(f"Prompt file not found: {p}")
        return p.read_text(encoding="utf-8").strip()
    if prompt:
        return prompt.strip()
    _die("Missing prompt. Use --prompt or --prompt-file.")
    return ""  # unreachable


def _append_suffix(prompt: str, suffix: str) -> str:
    sep = "\n\n" if prompt and not prompt.endswith(("\n", "。", ".", "!", "?", "！", "？")) else ""
    return f"{prompt}{sep}{suffix}".strip()


# ---------------------------------------------------------------------------
# Request body shaping
# ---------------------------------------------------------------------------


def _build_request_body(
    *, model: str, caps: dict[str, Any], prompt: str, size: str,
    output_format: str, watermark: bool, reference_images: Optional[list[str]],
    optimize_prompt: Optional[str],
    background: str = "opaque", layer_decomposition: bool = False,
) -> dict[str, Any]:
    mode = optimize_prompt or "standard"
    if mode not in caps["optimize_modes"]:
        _die(f"Prompt mode {mode!r} is not supported by {model}; supported: {sorted(caps['optimize_modes'])}.")
    if not layer_decomposition and not prompt:
        _die("A prompt is required for generation/editing.")
    body: dict[str, Any] = {
        "model": model, "size": size, "output_format": output_format,
        "watermark": watermark, "optimize_prompt_options": {"mode": mode},
    }
    if prompt:
        body["prompt"] = prompt
    if reference_images:
        limit = 1 if layer_decomposition else caps["max_refs"]
        if len(reference_images) > limit:
            _die(f"{model} accepts at most {limit} reference image(s) for this operation.")
        body["image"] = reference_images[0] if len(reference_images) == 1 else reference_images
    if layer_decomposition:
        if not reference_images:
            _die("Layer decomposition requires one reference image.")
        body["layer_decomposition"] = True
    else:
        body["background"] = background
    return body


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _make_output_path(
    prompt: str,
    out: Optional[str],
    out_dir: str,
    output_format: str,
    index: int = 0,
) -> Path:
    ext = "jpg" if output_format == "jpeg" else output_format
    if out:
        p = Path(out).expanduser().resolve()
        if p.suffix == "":
            p = p.with_suffix(f".{ext}")
        return p

    d = Path(out_dir).expanduser().resolve()
    d.mkdir(parents=True, exist_ok=True)
    ts = _now_slug()
    slug = _slugify(prompt, max_len=40)
    stem = f"{ts}-{slug}" if index == 0 else f"{ts}-{slug}-{index + 1}"
    return d / f"{stem}.{ext}"


def _write_metadata(
    image_path: Path,
    *,
    prompt: str,
    model: str,
    size: str,
    output_format: str,
    watermark: bool,
    web_search: bool,
    reference_count: int,
    optimize_prompt: Optional[str],
    base_url: str,
    dry_run: bool,
    background: str = "opaque",
    marker_rects: Optional[list[str]] = None,
    outpaint_specs: Optional[list[str]] = None,
    reported_size: Optional[str] = None,
    elapsed_ms: Optional[int] = None,
    revised_prompt: Optional[str] = None,
    usage: Optional[dict] = None,
) -> None:
    # Resolve model label for friendlier metadata
    caps = MODELS.get(model, {}).get("label", model)
    meta: dict[str, Any] = {
        "prompt": prompt,
        "model": model,
        "model_label": caps,
        "size": size,
        "output_format": output_format,
        "watermark": watermark,
        "web_search": False,
        "background": background,
        "optimize_prompt": optimize_prompt,
        "reference_images_count": reference_count,
        # Don't persist data URLs — they're huge and can contain secrets-adjacent material
        "reference_images_are_data_urls": None,  # populated below only when refs exist
        "marker_rects": marker_rects or [],
        "outpaint": outpaint_specs or [],
        "base_url": base_url,
        "image_path": str(image_path),
        "created_at": _now_iso(),
        "dry_run": dry_run,
    }
    # Callers pass reference_count explicitly so we don't confuse "single string data URL"
    # (which would give a byte-length len() in Python) with 1 image.
    if reported_size:
        meta["reported_size"] = reported_size
    if elapsed_ms is not None:
        meta["elapsed_ms"] = elapsed_ms
    if revised_prompt:
        meta["revised_prompt"] = revised_prompt
    if usage:
        meta["usage"] = usage

    meta_path = image_path.with_suffix(".json")
    try:
        with meta_path.open("x" if dry_run else "w", encoding="utf-8") as handle:
            json.dump(meta, handle, ensure_ascii=False, indent=2)
    except FileExistsError:
        if not dry_run:
            raise
        _info(f"Dry-run metadata skipped; existing file preserved: {meta_path}")
        return
    print(f"Metadata: {meta_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Error classification + retry
# ---------------------------------------------------------------------------


def _is_retryable(status_code: int) -> bool:
    return status_code in (429, 500, 502, 503, 504)


class _APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str,
                 retry_after: Optional[float] = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retry_after = retry_after


async def _call_api(
    client: httpx.AsyncClient,
    body: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    base = str(client.base_url).rstrip("/")
    url = f"{base}/images/generations"
    t0 = time.monotonic()
    response = await client.post(url, json=body, timeout=float(timeout))
    elapsed_ms = int((time.monotonic() - t0) * 1000)

    print(f"HTTP {response.status_code} ({elapsed_ms} ms)", file=sys.stderr)

    # Retry-after header
    retry_after: Optional[float] = None
    ra = response.headers.get("retry-after")
    if ra is not None:
        try:
            retry_after = float(ra)
        except ValueError:
            retry_after = None

    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        text = response.text[:500]
        print(f"Unexpected response (non-JSON): {text}", file=sys.stderr)
        raise _APIError(response.status_code, "NonJSONResponse", text, retry_after)

    try:
        data = response.json()
    except Exception:
        text = response.text[:500]
        print(f"Failed to parse JSON response: {text}", file=sys.stderr)
        raise _APIError(response.status_code, "JSONParseError", text, retry_after)

    if not response.is_success:
        error_info = data.get("error", {})
        code = error_info.get("code", f"HTTP {response.status_code}")
        message = error_info.get("message", str(data))
        raise _APIError(response.status_code, code, message, retry_after)

    # Attach elapsed time for metadata
    data["_elapsed_ms"] = elapsed_ms
    return data


async def _download_image(client: httpx.AsyncClient, url: str, timeout: int) -> bytes:
    """Download the generated image with its own retry/backoff.

    Separate from _call_api's retry loop on purpose: a transient failure here
    (the generation call already succeeded and was already paid for) should
    retry just the cheap download, not redo the whole generation.
    """
    last_error: Optional[Exception] = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = await client.get(url, timeout=float(timeout))
            response.raise_for_status()
            return response.content
        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as e:
            last_error = e
            if attempt < MAX_RETRIES:
                delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(
                    f"Image download failed ({e.__class__.__name__}), retrying in "
                    f"{delay:.0f}s (attempt {attempt+1}/{MAX_RETRIES})...",
                    file=sys.stderr,
                )
                await asyncio.sleep(delay)
    raise _APIError(0, "DownloadFailed", "Generation succeeded but image download failed after retries; generation will not be replayed.") from last_error


async def _generate_single(
    client: httpx.AsyncClient, body: dict[str, Any], timeout: int,
) -> tuple[list[ImageOutput], Optional[str], Optional[dict], Optional[str], Optional[int]]:
    data = await _call_api(client, body, timeout)
    images: list[ImageOutput] = []
    revised_prompt = None
    for item in data.get("data") or []:
        if item.get("error"):
            error = item["error"]
            raise _APIError(200, error.get("code", "ImageError"), error.get("message", "Image generation failed."))
        if item.get("url"):
            content = await _download_image(client, item["url"], timeout)
        elif item.get("b64_json"):
            content = base64.b64decode(item["b64_json"])
        else:
            raise _APIError(200, "MissingImage", "API result contains no downloadable image.")
        images.append(ImageOutput(content, item.get("size"), item.get("output_format"),
                                  item.get("z_index"), item.get("bounding_box"),
                                  item.get("name"), item.get("description")))
        revised_prompt = item.get("revised_prompt") or revised_prompt
    if not images:
        raise _APIError(200, "EmptyImages", "API returned no images; generation will not be replayed.")
    return images, revised_prompt, data.get("usage"), images[0].size, data.get("_elapsed_ms")


async def _generate_with_retry(
    api_key: str,
    base_url: str,
    body: dict[str, Any],
    timeout: int,
) -> tuple[list[ImageOutput], Optional[str], Optional[dict], Optional[str], Optional[int]]:
    last_error: Optional[_APIError] = None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(base_url=base_url, headers=headers) as client:
                return await _generate_single(client, body, timeout)
        except (httpx.TimeoutException, httpx.TransportError) as e:
            raise _APIError(0, "OutcomeUnknown", "Generation submission outcome is unknown after a transport failure; not automatically replaying the paid request.") from e
        except _APIError as e:
            last_error = e
            if _is_retryable(e.status_code) and attempt < MAX_RETRIES:
                if e.retry_after and e.retry_after > 0:
                    delay = min(e.retry_after, 60.0)
                else:
                    delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(
                    f"API error {e.status_code} ({e.code}), retrying in {delay:.0f}s "
                    f"(attempt {attempt+1}/{MAX_RETRIES})...",
                    file=sys.stderr,
                )
                await asyncio.sleep(delay)
            else:
                raise

    raise last_error  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Subcommand: list-models
# ---------------------------------------------------------------------------


def _cmd_list_models(_args: argparse.Namespace) -> int:
    print("Seedream models known to this skill:\n")
    for mid, caps in MODELS.items():
        print(f"  {mid}")
        print(f"    Label:        {caps['label']}")
        print(f"    Aliases:      {', '.join(sorted(caps['aliases']))}")
        print(f"    Default size: {caps['default_size']}")
        print(f"    Preset sizes: {', '.join(sorted(caps['size_strings']))}")
        print(f"    Pixel range:  {caps['pixel_min']:,} – {caps['pixel_max']:,}")
        print(f"    Max refs:     {caps['max_refs']}")
        print("    Modes:        single image, alpha editing, layer decomposition")
        print(f"    Opt modes:    {', '.join(sorted(caps['optimize_modes']))}")
        print(f"    Price:        {caps['price_per_image']}")
        print(f"    Notes:        {caps['notes']}")
        print()
    print("Default model: " + DEFAULT_MODEL)
    print()
    print("Use --model <id> (or pro/flash alias) to override. Any other model id is passed through")
    print("verbatim with Pro-capability defaults (useful for fresh dated Pro builds).")
    return 0


# ---------------------------------------------------------------------------
# Common setup used by generate/edit/batch
# ---------------------------------------------------------------------------


def _add_common_gen_args(p: argparse.ArgumentParser, *, include_variants: bool) -> None:
    """Args shared by generate, edit, and batch (latter uses a subset)."""
    p.add_argument("--model", default=DEFAULT_MODEL,
                   help=f"Model id or alias (pro|flash). Default: {DEFAULT_MODEL}.")
    p.add_argument("--size", default=None,
                   help="Image size preset (1K/1.5K/2K) or WIDTHxHEIGHT "
                        "(e.g. 1792x1024). Default: 2K on both models.")
    p.add_argument("--output-format", default=DEFAULT_OUTPUT_FORMAT, choices=list(ALLOWED_OUTPUT_FORMATS),
                   help=f"Output image format (default: {DEFAULT_OUTPUT_FORMAT}).")
    p.add_argument("--wechat-header", action="store_true",
                   help="Shorthand for --size 1792x1024 (wide cover). "
                        "Alias: --wide.")
    p.add_argument("--wide", action="store_true",
                   help="Shorthand for --size 1792x1024 (wide cover/banner). "
                        "Alias of --wechat-header.")
    p.add_argument("--square", action="store_true",
                   help="Shorthand for square output (1024x1024).")
    p.add_argument("--portrait", action="store_true",
                   help="Shorthand for 3:4 vertical output (1536x2048).")
    p.add_argument("--landscape", action="store_true",
                   help="Shorthand for 16:9 horizontal output (2048x1152).")
    p.add_argument("--phone", "--stories", "--wechat", action="store_true",
                   help="Shorthand for 9:16 phone/Stories/WeChat-UI vertical output "
                        "(1152x2048). Aliases: --stories, --wechat.")
    p.add_argument("--background", choices=["opaque", "transparent"], default="opaque",
                   help="Transparent requires exactly one alpha-bearing input and PNG output.")
    p.add_argument("--watermark", action="store_true",
                   help="Include Seedream watermark (default: off).")
    p.add_argument("--optimize-prompt", choices=["standard", "fast"], default=None,
                   help="Prompt optimization: Pro standard/fast; Flash standard only.")
    p.add_argument("--no-auto-upscale", action="store_true",
                   help="Disable auto-upscale for WxH sizes below the model's pixel floor "
                        "(Pro ~0.92MP / 921600). Default: generate at the smallest valid "
                        "same-aspect size, then LANCZOS-downscale to the requested size.")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                   help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT}).")
    p.add_argument("--dry-run", action="store_true",
                   help="Print the request body and exit without calling the API.")
    p.add_argument("--force", action="store_true",
                   help="Overwrite existing output files.")
    if include_variants:
        p.add_argument("--n", type=int, default=1,
                       help=f"Number of independent images to generate (1-{DEFAULT_MAX_N}, default: 1).")



def _resolve_common(args: argparse.Namespace, *, require_prompt: bool = True) -> dict[str, Any]:
    """Resolve model, size, prompt, and edit-preprocess (markers/outpaint)
    from argparse args. Returns a dict with everything needed to build the body.
    """
    model_id, caps = _resolve_model(args.model)

    # Resolve size (convenience flags → explicit string; model-aware)
    size = _apply_size_shortcuts(
        args.size, args.wechat_header, args.square, args.wide, args.portrait, args.landscape,
        getattr(args, "phone", False), caps,
    )
    requested_size = size
    auto_upscale = not bool(getattr(args, "no_auto_upscale", False))
    wh = _validate_size(size, caps, model_id, enforce_min=not auto_upscale)
    downscale_to: Optional[tuple[int, int]] = None
    if wh != (0, 0) and wh[0] * wh[1] < caps["pixel_min"]:
        # Below model floor (Pro pixel_min=921_600 ≈ 0.92MP). Generate larger, then downscale.
        api_w, api_h = _smallest_valid_size(wh[0], wh[1], caps["pixel_min"], caps["pixel_max"])
        _info(
            f"Size {wh[0]}x{wh[1]} ({wh[0]*wh[1]:,} px) is below the "
            f"{caps['pixel_min']:,} px floor; generating at {api_w}x{api_h} then "
            f"downscaling to {wh[0]}x{wh[1]}."
        )
        size = f"{api_w}x{api_h}"
        downscale_to = wh

    background = getattr(args, "background", "opaque")
    if background == "transparent":
        refs_for_alpha = list(getattr(args, "reference_image", []) or [])
        _validate_transparent_input(refs_for_alpha, args.output_format)
        if getattr(args, "outpaint", None):
            _die("Transparent editing cannot use the opaque outpaint canvas; edit an alpha layer directly.")

    # Prompt
    prompt = _read_prompt(getattr(args, "prompt", None), getattr(args, "prompt_file", None)) \
        if require_prompt else ""
    if len(prompt) > MAX_PROMPT_CHARS:
        _warn("Very long prompt: the official guide recommends concise prompts (about 300 Chinese characters or 600 English words).")

    # Reference images (used by both generate (optional) and edit (required))
    ref_paths = list(getattr(args, "reference_image", []) or [])
    marker_specs = list(getattr(args, "marker_rect", []) or [])
    outpaint_specs = list(getattr(args, "outpaint", []) or [])

    annotated_path: Optional[Path] = None
    outpaint_canvas_png: Optional[bytes] = None
    outpaint_aspect_word: Optional[str] = None

    # Outpaint first (it extends the canvas before markers are drawn), then markers.
    if outpaint_specs:
        if not ref_paths:
            _die("--outpaint requires a --reference-image to extend.")
        if len(ref_paths) != 1:
            _die("--outpaint works with exactly one reference image.")
        paddings: dict[str, int] = {}
        for spec in outpaint_specs:
            d, n = _parse_outpaint(spec)
            paddings[d] = paddings.get(d, 0) + n
        src = Path(ref_paths[0]).expanduser().resolve()
        png_bytes, aspect_word, new_dims = _apply_outpaint(src, paddings)
        outpaint_canvas_png = png_bytes
        outpaint_aspect_word = aspect_word
        prompt = _append_suffix(
            prompt,
            (OUTPAINT_FILL_ZH if _looks_chinese(prompt) else OUTPAINT_FILL_EN).format(aspect_word=aspect_word),
        )

    # Marker rectangles — draw on the reference image and append cleanup suffix.
    if marker_specs:
        if not ref_paths:
            _die("--marker-rect requires at least one --reference-image to annotate.")
        # Markers always annotate the first reference; additional refs are passed as-is.
        src_primary = ref_paths[0]
        if outpaint_canvas_png is not None:
            # We already padded; write to a temp file so we can draw markers on it,
            # then delete after encoding.
            _tmp = tempfile.NamedTemporaryFile(suffix=".marker-tmp.png", delete=False)
            try:
                _tmp.write(outpaint_canvas_png)
                _tmp.close()
                src_for_markers = Path(_tmp.name)
            except Exception:
                Path(_tmp.name).unlink(missing_ok=True)
                raise
            outpaint_canvas_png = None  # no longer needed separately
        elif _is_url(src_primary):
            _die("--marker-rect needs a local reference image (URLs cannot be annotated client-side).")
        else:
            src_for_markers = Path(src_primary).expanduser().resolve()

        rects = [_parse_marker_rect(s) for s in marker_specs]
        raw_colors = list(getattr(args, "marker_color", None) or [])
        if not raw_colors:
            raw_colors = ["#ff0000"]
        colors = [_parse_color(c) for c in raw_colors]
        fill_alpha = int(getattr(args, "marker_alpha", 80))
        stroke_width = int(getattr(args, "marker_stroke", 3))
        annotated_png = _apply_markers(
            src_for_markers, rects, colors, fill_alpha, stroke_width,
            preserve_alpha=background == "transparent",
        )
        # Clean up outpaint+marker temp file if we created one
        if outpaint_canvas_png is None and src_for_markers != Path(src_primary).expanduser().resolve():
            try:
                Path(src_for_markers).unlink(missing_ok=True)
            except OSError:
                pass

        # Save annotated image next to output for inspection
        out_dir = Path(getattr(args, "out_dir", DEFAULT_OUTPUT_DIR)).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        annotated_path = out_dir / f"{_now_slug()}-annotated.png"
        annotated_path.write_bytes(annotated_png)
        _info(f"Marker-annotated image saved for inspection: {annotated_path}")

        # Replace the primary reference with the annotated PNG
        if ref_paths[0] == src_primary:
            ref_paths = [str(annotated_path)] + ref_paths[1:]
        else:
            ref_paths[0] = str(annotated_path)

        # Append cleanup prompt unless disabled
        if not getattr(args, "no_marker_cleanup_prompt", False):
            cleanup = MARKER_CLEANUP_ZH if _looks_chinese(prompt) else MARKER_CLEANUP_EN
            prompt = _append_suffix(prompt, cleanup)

    # Encode reference images (or the outpaint canvas if outpaint was applied without markers)
    refs: Optional[list[str]] = None
    if ref_paths:
        refs = _resolve_reference_images(ref_paths)
    elif outpaint_canvas_png is not None:
        # Outpaint without markers: send padded canvas directly
        refs = [_encode_png_bytes(outpaint_canvas_png)]
        if not prompt.endswith(OUTPAINT_FILL_ZH[-20:]) and not prompt.endswith(OUTPAINT_FILL_EN[-20:]):
            prompt = _append_suffix(
                prompt,
                (OUTPAINT_FILL_ZH if _looks_chinese(prompt) else OUTPAINT_FILL_EN).format(
                    aspect_word=outpaint_aspect_word or "扩展"
                ),
            )

    # N
    n = getattr(args, "n", 1)
    if n < 1 or n > DEFAULT_MAX_N:
        _die(f"--n must be 1-{DEFAULT_MAX_N} (got {n}).")

    output_format = args.output_format
    if output_format == "jpg":
        output_format = "jpeg"

    return {
        "model_id": model_id,
        "caps": caps,
        "prompt": prompt,
        "size": size,
        "requested_size": requested_size,
        "output_format": output_format,
        "watermark": bool(args.watermark),
        "web_search": False,
        "background": background,
        "optimize_prompt": args.optimize_prompt,
        "downscale_to": downscale_to,
        "reference_images": refs,
        "reference_image_paths": list(getattr(args, "reference_image", []) or []),
        "reference_count": len(ref_paths),
        "marker_specs": marker_specs,
        "outpaint_specs": outpaint_specs,
        "annotated_path": str(annotated_path) if annotated_path else None,
        "n": n,
        "timeout": int(args.timeout),
        "dry_run": bool(args.dry_run),
        "force": bool(args.force),
    }


# ---------------------------------------------------------------------------
# Subcommand: generate
# ---------------------------------------------------------------------------


def _add_generate_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("generate", help="Create a new image from a text prompt.")
    p.add_argument("--prompt", "-p", help="Text description for the image.")
    p.add_argument("--prompt-file", help="Read prompt from a UTF-8 file.")
    p.add_argument("--reference-image", action="append", default=[],
                   help="Reference image path or URL (repeatable; max 10 on Pro/Flash).")
    p.add_argument("--out", help="Output file path (default: <out-dir>/<ts>-<slug>.<ext>).")
    p.add_argument("--out-dir", default=DEFAULT_OUTPUT_DIR,
                   help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).")
    _add_common_gen_args(p, include_variants=True)
    p.set_defaults(func=_cmd_generate)


def _cmd_generate(args: argparse.Namespace) -> int:
    r = _resolve_common(args, require_prompt=True)
    body = _build_request_body(
        model=r["model_id"], caps=r["caps"], prompt=r["prompt"], size=r["size"],
        output_format=r["output_format"], watermark=r["watermark"],
        reference_images=r["reference_images"], optimize_prompt=r["optimize_prompt"],
        background=r["background"],
    )

    out = getattr(args, "out", None)
    out_dir = getattr(args, "out_dir", DEFAULT_OUTPUT_DIR)
    out_dir_resolved = str(Path(out_dir).expanduser().resolve())
    _info(f"Output dir: {out_dir_resolved}")

    if r["dry_run"]:
        print(json.dumps(body, ensure_ascii=False, indent=2))
        # Best-effort dry-run metadata path
        image_path = _make_output_path(r["prompt"], out, out_dir, r["output_format"])
        _write_metadata(
            image_path, prompt=r["prompt"], model=r["model_id"], size=r["requested_size"],
            output_format=r["output_format"], watermark=r["watermark"], web_search=r["web_search"],
            reference_count=len(r.get("reference_image_paths", []) or []) or (1 if r["reference_images"] else 0),
            optimize_prompt=body.get("optimize_prompt_options", {}).get("mode"),
            base_url=DEFAULT_BASE_URL, dry_run=True,
            marker_rects=r["marker_specs"],
            outpaint_specs=r["outpaint_specs"],
            background=r["background"],
        )
        return 0

    if r["n"] > 1:
        return asyncio.run(_generate_concurrent(args, body, r, out, out_dir))
    return asyncio.run(_generate_one(args, body, r, out, out_dir))


async def _generate_one(
    args: argparse.Namespace,
    body: dict[str, Any],
    r: dict[str, Any],
    out: Optional[str],
    out_dir: str,
) -> int:
    api_key, base_url = _get_api_settings()
    t0 = time.monotonic()
    try:
        images, revised_prompt, usage, reported_size, _call_ms = await _generate_with_retry(
            api_key, base_url, body, r["timeout"],
        )
    except _APIError as e:
        _die(f"API error {e.status_code}: {e.code} — {e.message}")
    elapsed_ms = int((time.monotonic() - t0) * 1000)

    for idx, asset in enumerate(images):
        img_bytes = asset.content
        image_path = _make_output_path(r["prompt"], out, out_dir, r["output_format"], idx)
        if image_path.exists() and not r["force"]:
            _die(f"Output already exists: {image_path} (use --force to overwrite)")
        image_path.parent.mkdir(parents=True, exist_ok=True)
        img_bytes = _maybe_downscale(img_bytes, r.get("downscale_to"), r["output_format"])
        image_path.write_bytes(img_bytes)
        print(f"Image: {image_path}")

        meta_size = (
            f"{r['downscale_to'][0]}x{r['downscale_to'][1]}"
            if r.get("downscale_to") else r["size"]
        )
        _write_metadata(
            image_path,
            prompt=r["prompt"], model=r["model_id"], size=meta_size,
            output_format=r["output_format"], watermark=r["watermark"],
            web_search=r["web_search"], reference_count=r["reference_count"],
            optimize_prompt=body.get("optimize_prompt_options", {}).get("mode"), base_url=base_url, dry_run=False,
            marker_rects=r["marker_specs"], outpaint_specs=r["outpaint_specs"],
            reported_size=reported_size, elapsed_ms=elapsed_ms,
            revised_prompt=revised_prompt, usage=usage,
            background=r["background"],
        )

    return 0


async def _generate_concurrent(
    args: argparse.Namespace,
    body: dict[str, Any],
    r: dict[str, Any],
    out: Optional[str],
    out_dir: str,
) -> int:
    api_key, base_url = _get_api_settings()

    async def _run_one(i: int) -> tuple[int, list[ImageOutput], Optional[str], Optional[dict], Optional[str], Optional[int], Optional[str]]:
        t0 = time.monotonic()
        try:
            images, revised_prompt, usage, reported_size, _call_ms = await _generate_with_retry(
                api_key, base_url, body.copy(), r["timeout"],
            )
            return i, images, revised_prompt, usage, reported_size, int((time.monotonic() - t0) * 1000), None
        except _APIError as e:
            return i, [], None, None, None, None, str(e)

    tasks = [_run_one(i) for i in range(r["n"])]
    results = await asyncio.gather(*tasks)

    errors = 0
    for i, images, revised_prompt, usage, reported_size, elapsed_ms, error in results:
        if error:
            print(f"Error (variant {i+1}/{r['n']}): {error}", file=sys.stderr)
            errors += 1
            continue
        for j, asset in enumerate(images):
            img_bytes = asset.content
            image_path = _make_output_path(
                r["prompt"], out, out_dir, r["output_format"], i * len(images) + j,
            )
            if image_path.exists() and not r["force"]:
                _warn(f"Output exists, skipping: {image_path}")
                continue
            image_path.parent.mkdir(parents=True, exist_ok=True)
            img_bytes = _maybe_downscale(img_bytes, r.get("downscale_to"), r["output_format"])
            image_path.write_bytes(img_bytes)
            print(f"Image: {image_path}")
            meta_size = (
                f"{r['downscale_to'][0]}x{r['downscale_to'][1]}"
                if r.get("downscale_to") else r["size"]
            )
            _write_metadata(
                image_path,
                prompt=r["prompt"], model=r["model_id"], size=meta_size,
                output_format=r["output_format"], watermark=r["watermark"],
                web_search=r["web_search"], reference_count=r["reference_count"],
                optimize_prompt=body.get("optimize_prompt_options", {}).get("mode"), base_url=base_url, dry_run=False,
                marker_rects=r["marker_specs"], outpaint_specs=r["outpaint_specs"],
                reported_size=reported_size, elapsed_ms=elapsed_ms,
                revised_prompt=revised_prompt, usage=usage,
                background=r["background"],
            )

    if errors == r["n"]:
        _die(f"All {r['n']} concurrent generations failed.")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: edit
# ---------------------------------------------------------------------------


def _add_edit_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "edit",
        help="Modify an image: marker-based region edit (draw a colored box and describe the "
             "change), style transfer, reference-based character consistency, or outpaint."
    )
    p.add_argument("--prompt", "-p", required=True, help="Description of what to change.")
    p.add_argument("--prompt-file", help="Read prompt from a UTF-8 file.")
    p.add_argument("--reference-image", action="append", required=True,
                   help="Reference/input image (repeatable; first image is the one being edited "
                        "when markers/outpaint are used).")
    p.add_argument("--marker-rect", action="append", default=[],
                   help="Mark a rectangular region to edit. Spec as X,Y,W,H in pixels "
                        "(e.g. 100,150,800,300) or percent (e.g. 10%%,15%%,60%%,20%%). "
                        "Repeat for multiple regions. Use with a natural-language prompt "
                        "like 'Red box: replace the title with \"新标题\"' and add --marker-color "
                        "for multi-color regions.")
    p.add_argument("--marker-color", action="append", default=None,
                   help="Marker rectangle color (#RRGGBB). Repeat once per --marker-rect for "
                        "multi-color regions (e.g. red for title, blue for cap, so you can write "
                        "'红框替换标题，蓝框改帽子'). Defaults to #ff0000 for all rects if omitted.")
    p.add_argument("--marker-alpha", type=int, default=80,
                   help="Marker fill alpha 0-255 (default 80).")
    p.add_argument("--marker-stroke", type=int, default=3,
                   help="Marker outline stroke width in px (default 3).")
    p.add_argument("--no-marker-cleanup-prompt", action="store_true",
                   help="Don't auto-append the 'remove the colored markers' suffix.")
    p.add_argument("--outpaint", action="append", default=[],
                   help="Outpaint (extend canvas). Format direction:pixels (e.g. left:400). "
                        "Direction: left/right/top/bottom. Repeat for multiple sides.")
    p.add_argument("--out", help="Output file path.")
    p.add_argument("--out-dir", default=DEFAULT_OUTPUT_DIR,
                   help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).")
    _add_common_gen_args(p, include_variants=False)
    p.set_defaults(func=_cmd_edit, n=1)


def _cmd_edit(args: argparse.Namespace) -> int:
    r = _resolve_common(args, require_prompt=True)
    body = _build_request_body(
        model=r["model_id"], caps=r["caps"], prompt=r["prompt"], size=r["size"],
        output_format=r["output_format"], watermark=r["watermark"],
        reference_images=r["reference_images"], optimize_prompt=r["optimize_prompt"],
        background=r["background"],
    )

    out = getattr(args, "out", None)
    out_dir = getattr(args, "out_dir", DEFAULT_OUTPUT_DIR)

    if r["dry_run"]:
        print(json.dumps(body, ensure_ascii=False, indent=2))
        image_path = _make_output_path(r["prompt"], out, out_dir, r["output_format"])
        _write_metadata(
            image_path, prompt=r["prompt"], model=r["model_id"], size=r["requested_size"],
            output_format=r["output_format"], watermark=r["watermark"], web_search=r["web_search"],
            reference_count=r["reference_count"],
            optimize_prompt=body.get("optimize_prompt_options", {}).get("mode"),
            base_url=DEFAULT_BASE_URL, dry_run=True,
            marker_rects=r["marker_specs"],
            outpaint_specs=r["outpaint_specs"],
            background=r["background"],
        )
        return 0

    return asyncio.run(_generate_one(args, body, r, out, out_dir))


# ---------------------------------------------------------------------------
# Subcommand: generate-batch
# ---------------------------------------------------------------------------


def _add_batch_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("generate-batch", help="Run many generation jobs from a JSONL file.")
    p.add_argument("--input", required=True, help="Path to JSONL file. Each line: bare string (prompt) "
                                                  "or JSON object (prompt + per-job overrides).")
    p.add_argument("--out-dir", default=f"{DEFAULT_OUTPUT_DIR}/batch",
                   help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}/batch).")
    p.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                   help=f"Max concurrent requests (default: {DEFAULT_CONCURRENCY}).")
    # Batch uses a subset of common args (no --n/--out per-job)
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Default model (default: {DEFAULT_MODEL}).")
    p.add_argument("--size", default=None, help="Default image size.")
    p.add_argument("--output-format", default=DEFAULT_OUTPUT_FORMAT, choices=list(ALLOWED_OUTPUT_FORMATS),
                   help=f"Default output format (default: {DEFAULT_OUTPUT_FORMAT}).")
    p.add_argument("--wechat-header", action="store_true", help="Default size 1792x1024. Alias: --wide.")
    p.add_argument("--wide", action="store_true", help="Default size 1792x1024 (alias of --wechat-header).")
    p.add_argument("--square", action="store_true", help="Default to square output.")
    p.add_argument("--portrait", action="store_true", help="Default to 3:4 vertical output.")
    p.add_argument("--landscape", action="store_true", help="Default to 16:9 horizontal output.")
    p.add_argument("--phone", "--stories", "--wechat", action="store_true",
                   help="Default to 9:16 phone/Stories/WeChat-UI output.")
    p.add_argument("--background", choices=["opaque", "transparent"], default="opaque",
                   help="Transparent requires exactly one alpha-bearing input and PNG output.")
    p.add_argument("--watermark", action="store_true", help="Default watermark on.")
    p.add_argument("--optimize-prompt", choices=["standard", "fast"], default=None,
                   help="Pro standard/fast; Flash standard only.")
    p.add_argument("--no-auto-upscale", action="store_true",
                   help="Disable auto-upscale for sizes below the model pixel floor.")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Timeout (default: {DEFAULT_TIMEOUT}).")
    p.add_argument("--dry-run", action="store_true", help="Print bodies and exit.")
    p.add_argument("--force", action="store_true", help="Overwrite existing outputs.")
    p.set_defaults(func=_cmd_batch)


def _parse_jsonl(path: str) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.is_file():
        _die(f"JSONL file not found: {p}")

    jobs: list[dict[str, Any]] = []
    for lineno, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            data = line.strip('"').strip("'").strip()

        if isinstance(data, str):
            jobs.append({"prompt": data})
        elif isinstance(data, dict):
            if "prompt" not in data:
                _warn(f"Line {lineno}: missing 'prompt' key, skipping.")
                continue
            jobs.append(data)
        else:
            _warn(f"Line {lineno}: unexpected type {type(data).__name__}, skipping.")

    if not jobs:
        _die(f"No valid jobs found in {path}.")
    print(f"Parsed {len(jobs)} job(s) from {path}", file=sys.stderr)
    return jobs


def _cmd_batch(args: argparse.Namespace) -> int:
    jobs = _parse_jsonl(args.input)
    if not args.dry_run:
        # Real workers need a key; previews do not call the API.
        _get_api_settings()

    bodies: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for i, job in enumerate(jobs):
        # Merge job onto a pseudo-argparse namespace so _resolve_common handles per-model logic
        class _NS:
            pass
        ns = _NS()
        ns.model = job.get("model", args.model)
        ns.size = job.get("size", args.size)
        ns.output_format = job.get("output_format", args.output_format)
        ns.wechat_header = bool(job.get("wechat_header", args.wechat_header))
        ns.wide = bool(job.get("wide", args.wide)) or ns.wechat_header
        ns.square = bool(job.get("square", args.square))
        ns.portrait = bool(job.get("portrait", args.portrait))
        ns.landscape = bool(job.get("landscape", args.landscape))
        ns.watermark = bool(job.get("watermark", args.watermark))
        ns.optimize_prompt = job.get("optimize_prompt", args.optimize_prompt)
        ns.background = job.get("background", args.background)
        ns.no_auto_upscale = bool(job.get("no_auto_upscale", getattr(args, "no_auto_upscale", False)))
        ns.reference_image = list(job.get("reference_image", []) or [])
        ns.marker_rect = list(job.get("marker_rects", []) or [])
        mc = job.get("marker_color", ["#ff0000"])
        ns.marker_color = list(mc) if isinstance(mc, list) else [mc]
        ns.marker_alpha = int(job.get("marker_alpha", 80))
        ns.marker_stroke = int(job.get("marker_stroke", 3))
        ns.no_marker_cleanup_prompt = bool(job.get("no_marker_cleanup_prompt", False))
        ns.outpaint = list(job.get("outpaint", []) or [])
        ns.prompt = job["prompt"]
        ns.prompt_file = None
        ns.out_dir = args.out_dir
        ns.n = 1
        ns.timeout = int(job.get("timeout", args.timeout))
        ns.dry_run = bool(args.dry_run)
        ns.force = bool(args.force)
        ns.out = None
        # Size shortcuts
        ns.phone = bool(job.get("phone", False))

        r = _resolve_common(ns, require_prompt=True)
        body = _build_request_body(
            model=r["model_id"], caps=r["caps"], prompt=r["prompt"], size=r["size"],
            output_format=r["output_format"], watermark=r["watermark"],
            reference_images=r["reference_images"], optimize_prompt=r["optimize_prompt"],
            background=r["background"],
        )
        bodies.append((job["prompt"], body, r))

    if args.dry_run:
        for i, (prompt, body, _r) in enumerate(bodies):
            print(f"\n--- Job {i+1} ---")
            print(json.dumps(body, ensure_ascii=False, indent=2))
        return 0

    return asyncio.run(_run_batch(args, bodies))


async def _run_batch(
    args: argparse.Namespace,
    bodies: list[tuple[str, dict[str, Any], dict[str, Any]]],
) -> int:
    sem = asyncio.Semaphore(args.concurrency)
    api_key, base_url = _get_api_settings()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    async def _run_job(index: int, prompt: str, body: dict[str, Any], r: dict[str, Any]) -> bool:
        async with sem:
            try:
                t0 = time.monotonic()
                images, revised_prompt, usage, reported_size, _call_ms = await _generate_with_retry(
                    api_key, base_url, body, r["timeout"],
                )
                elapsed_ms = int((time.monotonic() - t0) * 1000)
                for j, asset in enumerate(images):
                    img_bytes = asset.content
                    stem = _slugify(prompt, max_len=30)
                    ext = "jpg" if r["output_format"] == "jpeg" else r["output_format"]
                    image_path = out_dir / f"job-{index+1:03d}-{stem}-{j+1}.{ext}"
                    if image_path.exists() and not args.force:
                        _warn(f"Output exists, skipping: {image_path}")
                        continue
                    img_bytes = _maybe_downscale(img_bytes, r.get("downscale_to"), r["output_format"])
                    image_path.write_bytes(img_bytes)
                    print(f"[{index+1}/{len(bodies)}] Image: {image_path}")
                    meta_size = (
                        f"{r['downscale_to'][0]}x{r['downscale_to'][1]}"
                        if r.get("downscale_to") else body["size"]
                    )
                    _write_metadata(
                        image_path,
                        prompt=prompt, model=body["model"], size=meta_size,
                        output_format=r["output_format"], watermark=body.get("watermark", False),
                        web_search="tools" in body, reference_count=r["reference_count"],
                        optimize_prompt=body.get("optimize_prompt_options", {}).get("mode"),
                        base_url=base_url, dry_run=False,
                        marker_rects=r["marker_specs"], outpaint_specs=r["outpaint_specs"],
                        reported_size=reported_size, elapsed_ms=elapsed_ms,
                        revised_prompt=revised_prompt, usage=usage,
                        background=r["background"],
                    )
                return True
            except _APIError as e:
                print(f"[{index+1}/{len(bodies)}] Error: {e.code} — {e.message}", file=sys.stderr)
                return False

    tasks = [_run_job(i, prompt, body, r) for i, (prompt, body, r) in enumerate(bodies)]
    results = await asyncio.gather(*tasks)

    successes = sum(1 for r in results if r)
    failures = len(results) - successes
    print(f"\nBatch complete: {successes} success, {failures} failed", file=sys.stderr)
    return 0 if failures == 0 else 1


# ---------------------------------------------------------------------------
# Layer decomposition (same Images API, structured multi-image response)
# ---------------------------------------------------------------------------


def _add_decompose_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("decompose", help="Split one image into a base and transparent PNG layers.")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--reference-image", action="append", required=True,
                   help="Exactly one PNG/JPEG source; at least 512x512 total pixels.")
    p.add_argument("--prompt", "-p", help="Optional objects/regions to extract; omitted means automatic selection.")
    p.add_argument("--prompt-file")
    p.add_argument("--size", choices=["auto", "1K", "1.5K", "2K"], default="auto")
    p.add_argument("--output-format", choices=list(ALLOWED_OUTPUT_FORMATS), default="png",
                   help="Base format only; foreground layers are always PNG.")
    p.add_argument("--optimize-prompt", choices=["standard", "fast"], default=None)
    p.add_argument("--out-dir", help="Output folder; defaults to a fresh timestamped layers folder.")
    p.add_argument("--watermark", action="store_true")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=_cmd_decompose)


def _cmd_decompose(args: argparse.Namespace) -> int:
    model, caps = _resolve_model(args.model)
    paths = args.reference_image
    if len(paths) != 1:
        _die("Layer decomposition requires exactly one reference image.")
    source = paths[0]
    if not _is_url(source):
        path = Path(source).expanduser().resolve()
        if not path.is_file() or path.stat().st_size > MAX_REFERENCE_BYTES:
            _die("Layer source must be a local image no larger than 30MB.")
        try:
            with Image.open(path) as image:
                w, h = image.size
                if image.format not in {"PNG", "JPEG"}:
                    _die("Layer decomposition accepts PNG/JPEG input only.")
                if not (262_144 <= w * h <= 36_000_000) or max(w, h) / min(w, h) > 16:
                    _die("Layer source must contain 262144–36000000 pixels with aspect ratio at most 16:1.")
        except OSError as error:
            _die(f"Cannot read layer source: {error.__class__.__name__}")
    prompt = _read_prompt(args.prompt, args.prompt_file) if args.prompt or args.prompt_file else ""
    output_format = "jpeg" if args.output_format == "jpg" else args.output_format
    body = _build_request_body(
        model=model, caps=caps, prompt=prompt, size=args.size, output_format=output_format,
        watermark=args.watermark, reference_images=_resolve_reference_images(paths),
        optimize_prompt=args.optimize_prompt, layer_decomposition=True,
    )
    if args.dry_run:
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return 0
    label = "image" if _is_url(source) else _slugify(Path(source).stem)
    out_dir = Path(args.out_dir or f"{DEFAULT_OUTPUT_DIR}/layers/{_now_slug()}-{label}").expanduser().resolve()
    existing = list(out_dir.glob("base.*")) + list(out_dir.glob("layer-*.png")) + list(out_dir.glob("layers.json"))
    if existing and not args.force:
        _die("Layer outputs already exist; use a fresh --out-dir or --force.")
    return asyncio.run(_decompose(args, body, out_dir))


async def _decompose(args: argparse.Namespace, body: dict[str, Any], out_dir: Path) -> int:
    api_key, base_url = _get_api_settings()
    try:
        images, _revised_prompt, usage, _size, api_ms = await _generate_with_retry(
            api_key, base_url, body, args.timeout,
        )
    except _APIError as error:
        _die(f"Layer decomposition failed: {error.code} — {error.message}")
    indices = [image.z_index for image in images]
    if any(type(index) is not int for index in indices) or indices.count(0) != 1 or len(set(indices)) != len(indices):
        _die("Layer response is missing unique z_index values and one base; do not replay generation automatically.")
    if any(index < 0 or index > 16 for index in indices):
        _die("Layer response exceeds the documented index range; do not replay generation automatically.")
    planned = []
    for asset in sorted(images, key=lambda image: image.z_index):
        with Image.open(BytesIO(asset.content)) as decoded:
            width, height = decoded.size
            fmt = {"PNG": "png", "JPEG": "jpeg"}.get(decoded.format)
            if fmt is None or (asset.z_index > 0 and fmt != "png"):
                _die("Layer response has an unexpected encoding; generation will not be replayed.")
        ext = "jpg" if fmt == "jpeg" else fmt
        filename = f"base.{ext}" if asset.z_index == 0 else f"layer-{asset.z_index:03d}.png"
        path = out_dir / filename
        if path.exists() and not args.force:
            _die(f"Layer output already exists: {path}")
        record = {
            "file": filename, "z_index": asset.z_index, "output_format": fmt,
            "size": f"{width}x{height}", "reported_size": asset.size,
        }
        for field in ("bounding_box", "name", "description"):
            value = getattr(asset, field)
            if value is not None:
                record[field] = value
        planned.append((path, asset.content, record))
    out_dir.mkdir(parents=True, exist_ok=True)
    for path, content, _record in planned:
        path.write_bytes(content)
        print(f"Layer: {path}")
    manifest = {
        "model": body["model"], "prompt": body.get("prompt"), "size": body["size"],
        "layer_decomposition": True, "created_at": _now_iso(), "api_elapsed_ms": api_ms,
        "usage": {key: usage[key] for key in ("generated_images", "input_images", "output_tokens", "total_tokens")
                  if usage and key in usage},
        "layers": [record for _path, _content, record in planned],
    }
    (out_dir / "layers.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Manifest: {out_dir / 'layers.json'}")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    _load_dotenv()

    parser = argparse.ArgumentParser(
        description="Generate and edit images with Seedream 5.0 Pro (default) via Volcengine Ark API.\n"
                    "Pro ships SOTA Chinese+English text rendering and marker-based region editing.\n"
                    "Docs: https://www.volcengine.com/docs/82379/1824121",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommands.")
    _add_generate_parser(subparsers)
    _add_edit_parser(subparsers)
    _add_batch_parser(subparsers)
    _add_decompose_parser(subparsers)

    # list-models is simple enough to not need a full common-arg parser
    p_list = subparsers.add_parser("list-models", help="Print known model ids, capabilities, and pricing.")
    p_list.set_defaults(func=_cmd_list_models)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
