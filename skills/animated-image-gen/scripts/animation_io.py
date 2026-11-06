"""Frame, timeline and delivery-format operations shared by the skill commands."""

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time

import numpy as np
from PIL import Image, ImageSequence, features


@dataclass
class Animation:
    frames: list[Image.Image]
    durations: list[int]
    plays: int = 0


def validate(animation):
    if not animation.frames or len(animation.frames) != len(animation.durations):
        raise ValueError("Supply one positive duration for each frame.")
    size = animation.frames[0].size
    if any(frame.size != size for frame in animation.frames):
        raise ValueError("All frames must have the same dimensions. Resize or pad them first.")
    if any(not math.isfinite(value) or value <= 0 for value in animation.durations):
        raise ValueError("Frame durations must be finite and positive.")
    if not 0 <= animation.plays <= 65535:
        raise ValueError("Plays must be0 for infinite playback, or1–65535 total plays.")


def load_frames(path, default_delay=120):
    path = Path(path)
    if path.is_dir():
        files = sorted(path.glob("*.png"), key=lambda item: [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", item.name)])
        if not files:
            raise ValueError("The frame directory must contain PNG files.")
        frames = []
        for filename in files:
            with Image.open(filename) as image:
                frames.append(image.convert("RGBA"))
        manifest = path / "timeline.json"
        if manifest.is_file():
            data = json.loads(manifest.read_text())
            animation = Animation(frames, data["durations_ms"], data.get("plays", 0))
        else:
            animation = Animation(frames, [default_delay] * len(frames))
    else:
        frames, durations = [], []
        with Image.open(path) as image:
            container, loop = image.format, image.info.get("loop")
            for frame in ImageSequence.Iterator(image):
                frame.load()
                frames.append(frame.convert("RGBA").copy())
                durations.append(round(frame.info.get("duration", default_delay)))
        if container == "GIF":
            plays = 1 if loop is None else 0 if loop == 0 else loop + 1
        elif container == "WEBP":
            plays = 0 if loop == 0 else loop or 1
        else:
            plays = 0
        animation = Animation(frames, durations, plays)
    validate(animation)
    return animation


def split_sheet(image, grid, count, size, inset=0, resample=Image.Resampling.LANCZOS):
    columns, rows = grid
    if columns < 1 or rows < 1 or not 1 <= count <= columns * rows:
        raise ValueError("The grid must contain all requested poses.")
    width, height = image.size
    if inset < 0 or min(width / columns, height / rows) <= inset * 2:
        raise ValueError("Cell inset leaves an empty frame.")
    frames = []
    for index in range(count):
        column, row = index % columns, index // columns
        bounds = (round(column * width / columns) + inset, round(row * height / rows) + inset,
                  round((column + 1) * width / columns) - inset, round((row + 1) * height / rows) - inset)
        frames.append(image.crop(bounds).convert("RGBA").resize(size, resample))
    return frames


def timeline(count, *, duration_ms=None, fps=None, delays=None, format="webp"):
    if sum(value is not None for value in (duration_ms, fps, delays)) > 1:
        raise ValueError("Choose total duration, fps or explicit frame delays.")
    if count < 1:
        raise ValueError("The timeline needs at least one frame.")
    if delays is not None:
        if len(delays) != count:
            raise ValueError("Explicit delays must match the source pose count.")
        values = list(delays)
    elif duration_ms is not None:
        values = [duration_ms / count] * count
    elif fps is not None:
        if not math.isfinite(fps) or fps <= 0:
            raise ValueError("FPS must be finite and positive.")
        values = [1000 / fps] * count
    else:
        values = [120] * count
    if any(not math.isfinite(value) or value <= 0 for value in values):
        raise ValueError("Frame durations must be finite and positive.")
    unit = 10 if format == "gif" else 1
    result, total, encoded = [], 0.0, 0
    for value in values:
        total += value
        next_encoded = round(total / unit) * unit
        result.append(next_encoded - encoded)
        encoded = next_encoded
    if any(value < unit for value in result):
        raise ValueError(f"{format.upper()} needs at least{unit} ms for each encoded frame.")
    return result


def key_background(frame, color="green"):
    keys = {"green": (0, 255, 0), "magenta": (255, 0, 255), "cyan": (0, 255, 255)}
    if color not in keys:
        raise ValueError("Key color must be green, magenta or cyan.")
    rgba = np.asarray(frame.convert("RGBA")).copy()
    red, green, blue = [rgba[:, :, index].astype(float) for index in range(3)]
    excess = {"green": green - np.maximum(red, blue), "magenta": np.minimum(red, blue) - green,
              "cyan": np.minimum(green, blue) - red}[color]
    alpha = np.clip((100 - excess) / 75, 0, 1)
    rgba[:, :, 3] = np.minimum(rgba[:, :, 3], np.round(alpha * 255)).astype(np.uint8)
    partial = (alpha > 0) & (alpha < 1)
    safe_alpha = np.maximum(alpha[:, :, None], 0.01)
    unmatte = (rgba[:, :, :3].astype(float) - (1 - alpha[:, :, None]) * np.asarray(keys[color])) / safe_alpha
    rgba[:, :, :3][partial] = np.clip(unmatte[partial], 0, 255).astype(np.uint8)
    return Image.fromarray(rgba)


def align_base(frames):
    anchors, boxes = [], []
    for frame in frames:
        alpha = np.asarray(frame.convert("RGBA"))[:, :, 3]
        if not np.any(alpha == 0):
            raise ValueError("Base alignment needs an isolated subject on a transparent background.")
        ys, xs = np.where(alpha >= 128)
        if not len(ys):
            raise ValueError("Base alignment needs a visible foreground in every frame.")
        bottom = int(ys.max())
        band = ys >= bottom - max(2, round((bottom - int(ys.min()) + 1) * 0.1))
        anchors.append((float(xs[band].mean()), bottom))
        boxes.append((int(xs.min()), int(ys.min()), int(xs.max()) + 1, bottom + 1))
    result = []
    for frame, anchor, bounds in zip(frames, anchors, boxes):
        dx, dy = round(anchors[0][0] - anchor[0]), round(anchors[0][1] - anchor[1])
        if bounds[0] + dx < 0 or bounds[1] + dy < 0 or bounds[2] + dx > frame.width or bounds[3] + dy > frame.height:
            raise ValueError("Alignment would crop the subject. Pad the source frames first.")
        aligned = Image.new("RGBA", frame.size)
        aligned.alpha_composite(frame.convert("RGBA"), (dx, dy))
        result.append(aligned)
    return result


def save_frames(frames, directory, durations=None, plays=0):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for index, frame in enumerate(frames):
        frame.convert("RGBA").save(directory / f"frame-{index + 1:04d}.png")
    if durations is not None:
        validate(Animation(frames, durations, plays))
        write_json(directory / "timeline.json", {"durations_ms": durations, "plays": plays})


def contact_sheet(frames, path, columns=4):
    columns = min(columns, len(frames))
    rows = math.ceil(len(frames) / columns)
    image = Image.new("RGB", (columns * 192, rows * 212), "#e5e7eb")
    from PIL import ImageDraw, ImageOps
    draw = ImageDraw.Draw(image)
    for index, frame in enumerate(frames):
        x, y = index % columns * 192, index // columns * 212
        tile = Image.new("RGBA", frame.size, "#e5e7eb")
        tile.alpha_composite(frame.convert("RGBA"))
        tile = ImageOps.contain(tile.convert("RGB"), (192, 192))
        image.paste(tile, (x + (192 - tile.width) // 2, y))
        draw.text((x + 6, y + 194), f"Frame{index + 1}", fill="#1f2937")
    image.save(path)


def inspect_animation(path):
    path = Path(path)
    animation = load_frames(path)
    with Image.open(path) as image:
        container, raw_loop = image.format, image.info.get("loop")
    hashes, transparent, partial = [], [], []
    for frame in animation.frames:
        data = np.asarray(frame).copy()
        data[data[:, :, 3] == 0, :3] = 0
        hashes.append(hashlib.sha256(data.tobytes()).hexdigest())
        transparent.append(int(np.sum(data[:, :, 3] == 0)))
        partial.append(int(np.sum((data[:, :, 3] > 0) & (data[:, :, 3] < 255))))
    return {"path": str(path.resolve()), "format": container, "size": list(animation.frames[0].size),
            "decoded_frames": len(animation.frames), "unique_frames": len(set(hashes)),
            "durations_ms": animation.durations, "cycle_ms": sum(animation.durations),
            "plays": animation.plays, "container_loop": raw_loop, "bytes": path.stat().st_size,
            "transparent_pixels": transparent, "partial_alpha_pixels": partial}


def gif_frames(frames, colors):
    transparent = any(frame.getchannel("A").getextrema()[0] < 128 for frame in frames)
    sample = Image.new("RGB", (128 * len(frames), 128))
    for index, frame in enumerate(frames):
        sample.paste(frame.convert("RGB").resize((128, 128)), (128 * index, 0))
    palette = sample.quantize(colors=min(colors, 255) if transparent else colors, method=Image.Quantize.MEDIANCUT)
    result = []
    for frame in frames:
        quantized = frame.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE)
        if transparent:
            data = np.asarray(quantized).copy()
            data[np.asarray(frame.getchannel("A")) < 128] = 255
            quantized = Image.fromarray(data, mode="P")
            values = palette.getpalette()
            quantized.putpalette(values + [0] * (768 - len(values)))
        result.append(quantized)
    return result, transparent


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def validate_export_options(format, webp_mode, quality, colors, max_bytes, plays):
    if format not in {"gif", "webp"}:
        raise ValueError("Choose a WebP or GIF output.")
    if webp_mode not in {"lossy", "lossless"} or not 0 <= quality <= 100 or not 2 <= colors <= 256:
        raise ValueError("Use lossy/lossless WebP, quality 0–100 and colors 2–256.")
    if max_bytes is not None and max_bytes <= 0:
        raise ValueError("The byte limit must be positive.")
    if not isinstance(plays, int) or isinstance(plays, bool) or not 0 <= plays <= 65535:
        raise ValueError("Plays must be 0–65535, with 0 selecting infinite playback.")
    if format == "webp" and not features.check("webp"):
        raise ValueError("This Pillow installation needs WebP encoding support.")


def encode_animation(animation, output, *, webp_mode="lossy", quality=80, colors=128, max_bytes=None, force=False):
    validate(animation)
    output = Path(output)
    format = output.suffix.lower().lstrip(".")
    if format not in {"gif", "webp"}:
        raise ValueError("Choose a .webp or .gif output path.")
    if output.exists() and not force:
        raise FileExistsError(f"Output exists: {output}")
    sidecar = output.with_suffix(output.suffix + ".json")
    if sidecar.exists() and not force:
        raise FileExistsError(f"Metadata exists: {sidecar}")
    validate_export_options(format, webp_mode, quality, colors, max_bytes, animation.plays)
    output.parent.mkdir(parents=True, exist_ok=True)
    lock = output.with_name(output.name + ".lock")
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    temporary = None
    try:
        if output.exists() and not force:
            raise FileExistsError(f"Output exists: {output}")
        if sidecar.exists() and not force:
            raise FileExistsError(f"Metadata exists: {sidecar}")
        with tempfile.NamedTemporaryFile(dir=output.parent, suffix=output.suffix, delete=False) as handle:
            temporary = Path(handle.name)
        durations = timeline(len(animation.frames), delays=animation.durations, format=format)
        frames = [frame.convert("RGBA") for frame in animation.frames]
        candidates = [quality]
        if format == "gif":
            candidates = [value for value in [colors, 128, 64, 32] if value <= colors]
            candidates = list(dict.fromkeys(candidates)) if max_bytes else [colors]
        elif max_bytes and webp_mode == "lossy":
            candidates = list(range(quality, 29, -10)) or [quality]
        started = time.monotonic()
        for candidate in candidates:
            options = {"save_all": True, "duration": durations}
            if format == "gif":
                encoded, transparent = gif_frames(frames, candidate)
                options.update(disposal=2 if transparent else 1, optimize=False)
                if transparent:
                    options["transparency"] = 255
                if animation.plays != 1:
                    options["loop"] = 0 if animation.plays == 0 else animation.plays - 1
            else:
                encoded = frames
                options.update(loop=animation.plays, lossless=webp_mode == "lossless", quality=candidate,
                               method=4, alpha_quality=100, exact=True)
            encoded[0].save(temporary, format=format.upper(), append_images=encoded[1:], **options)
            if max_bytes is None or temporary.stat().st_size <= max_bytes:
                break
        if max_bytes is not None and temporary.stat().st_size > max_bytes:
            raise ValueError(f"Encoded image is{temporary.stat().st_size} bytes, above the{max_bytes} byte limit. Adjust dimensions or encoding settings.")
        metadata = inspect_animation(temporary)
        if metadata["unique_frames"] < 2:
            raise ValueError("The encoded output is a still image. Supply visible changes between frames.")
        if metadata["cycle_ms"] != sum(durations) or metadata["plays"] != animation.plays:
            raise ValueError("Decoded timing or repeat behavior differs from the planned animation.")
        if force:
            os.replace(temporary, output)
        else:
            os.link(temporary, output)
        metadata.update(path=str(output.resolve()), source_frame_count=len(frames), source_cycle_ms=sum(animation.durations),
                        encode_seconds=round(time.monotonic() - started, 3), webp_mode=webp_mode if format == "webp" else None,
                        encoding_quality=candidate if format == "webp" else None, palette_colors=candidate if format == "gif" else None)
        write_json(output.with_suffix(output.suffix + ".json"), metadata)
        return metadata
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        lock.unlink(missing_ok=True)
