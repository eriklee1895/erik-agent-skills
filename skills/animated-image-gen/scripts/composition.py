"""Portable local composition used by the measured creative templates."""

import math
import os
from pathlib import Path
import shutil
import subprocess
import unicodedata

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont
from fontTools.ttLib import TTFont


def checked_font(path, text, size):
    with TTFont(str(path), fontNumber=0, lazy=True) as source:
        cmap = source.getBestCmap() or {}
        missing = sorted({ord(char) for char in text if not char.isspace() and unicodedata.category(char) != "Cf"
                          and ord(char) not in cmap})
    if missing:
        codes = ", ".join(f"U+{value:04X}" for value in missing[:8])
        raise ValueError(f"The font lacks caption glyphs {codes}. Choose a font with the required characters.")
    return ImageFont.truetype(str(path), size)


def font_for(text, size, explicit=None):
    selected = explicit or os.getenv("ANIMATED_IMAGE_FONT")
    if selected:
        return checked_font(Path(selected).expanduser(), text, size)
    cjk = any("\u2e80" <= char <= "\u9fff" for char in text)
    candidates = [Path("/System/Library/Fonts/PingFang.ttc"), Path("/System/Library/Fonts/STHeiti Light.ttc"),
                  Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
                  Path(os.getenv("WINDIR", "C:/Windows")) / "Fonts/msyh.ttc"]
    candidates = list((Path.home() / "Library/Fonts").glob("MiSans-*bold.ttf")) + candidates
    matcher = shutil.which("fc-match")
    if matcher:
        try:
            result = subprocess.run([matcher, "-f", "%{file}", ":lang=zh" if cjk else "sans"], capture_output=True, text=True, timeout=3)
            if result.returncode == 0 and result.stdout:
                candidates.append(Path(result.stdout))
        except (OSError, subprocess.TimeoutExpired):
            pass
    for path in candidates:
        if path.is_file():
            try:
                return checked_font(path, text, size)
            except (OSError, ValueError):
                continue
    if cjk:
        raise ValueError("Set --font or ANIMATED_IMAGE_FONT to an installed CJK font file.")
    if any(ord(char) > 127 for char in text):
        raise ValueError("Set --font or ANIMATED_IMAGE_FONT to a font containing the caption characters.")
    return ImageFont.load_default(size=size)


def rectangle(spec, size):
    if len(spec) != 4 or any(not math.isfinite(value) for value in spec):
        raise ValueError("A local region uses normalized x,y,width,height.")
    x, y, width, height = spec
    if min(x, y) < 0 or min(width, height) <= 0 or x + width > 1 or y + height > 1:
        raise ValueError("The normalized region must fit inside the canvas.")
    return (round(x * size[0]), round(y * size[1]), round((x + width) * size[0]), round((y + height) * size[1]))


def static_composite(frames, region, static_image=None):
    base = (static_image or frames[0]).convert("RGBA")
    if abs(base.width / base.height - frames[0].width / frames[0].height) > 0.02:
        raise ValueError("Crop or pad the static image to the animation aspect ratio first.")
    base = base.resize(frames[0].size, Image.Resampling.LANCZOS)
    mask = Image.new("L", base.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(rectangle(region, base.size), radius=8, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(3))
    return [Image.composite(frame, base, mask) for frame in frames]


def overlay_plan(entries, size, count, font=None):
    if not isinstance(entries, list):
        raise ValueError("Overlays must be a JSON list.")
    plan = []
    for entry in entries:
        text = str(entry.get("text", ""))
        start, end = entry.get("start", 0), entry.get("end", count)
        if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= count:
            raise ValueError("Overlay start/end must select source frames, with end exclusive.")
        bounds = rectangle(entry["box"], size)
        left, top, right, bottom = bounds
        font_size = entry.get("font_size", max(12, round((bottom - top) * 0.48)))
        face = font_for(text, font_size, font) if text else None
        if face:
            box = face.getbbox(text)
            if box[2] - box[0] > right - left - 8 or box[3] - box[1] > bottom - top - 4:
                raise ValueError("Overlay text does not fit its box. Shorten the text, enlarge the box or reduce font_size.")
        fill, border = entry.get("fill"), entry.get("border")
        color = entry.get("color", "#243b35")
        for value in [fill, border, color]:
            if value:
                ImageColor.getcolor(value, "RGBA")
        plan.append((entry, text, start, end, bounds, face, fill, border, color))
    return plan


def overlays(frames, entries, font=None):
    result = [frame.copy().convert("RGBA") for frame in frames]
    for entry, text, start, end, bounds, face, fill, border, color in overlay_plan(entries, frames[0].size, len(frames), font):
        left, top, right, bottom = bounds
        for index in range(start, end):
            draw = ImageDraw.Draw(result[index])
            if fill or border:
                draw.rounded_rectangle(bounds, radius=entry.get("radius", 8), fill=fill, outline=border, width=2)
            if face:
                draw.text(((left + right) / 2, (top + bottom) / 2), text, font=face, fill=color, anchor="mm")
    return result


def breathing_frames(image, region, count=12, amplitude=1.0):
    if count < 3 or not 0 < amplitude <= 5:
        raise ValueError("Breathing needs at least3 frames and amplitude above0 through5 percent.")
    image = image.convert("RGBA")
    left, top, right, bottom = rectangle(region, image.size)
    center = ((left + right) / 2, (top + bottom) / 2)
    spread = ((right - left) / 3.2, (bottom - top) / 3.2)
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).ellipse((left, top, right, bottom), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2))
    frames = []
    for index in range(count):
        distance = image.height * amplitude / 100 * math.sin(index * math.tau / count)
        mesh = []
        for y in range(0, image.height, 24):
            for x in range(0, image.width, 24):
                x1, y1 = min(x + 24, image.width), min(y + 24, image.height)
                points = []
                for sx, sy in [(x, y), (x, y1), (x1, y1), (x1, y)]:
                    weight = math.exp(-((sx - center[0]) / spread[0]) ** 4 - ((sy - center[1]) / spread[1]) ** 4)
                    points.extend([sx, sy - distance * weight])
                mesh.append(((x, y, x1, y1), tuple(points)))
        warped = image.transform(image.size, Image.Transform.MESH, mesh, resample=Image.Resampling.BILINEAR)
        frames.append(Image.composite(warped, image, mask))
    return frames


def flow_frames(size=(1280, 720), mascot=None, font=None, language="en"):
    titles = ["USER", "AGENT", "TOOL", "RESULT"]
    subtitles = ["Start request", "Plan and combine", "Execute operation", "Return result"]
    captions = ["1  Receive request", "2  Plan next step", "3  Call tool", "4  Receive tool result", "5  Combine and check", "6  Deliver result"]
    if language == "zh":
        subtitles = ["发起请求", "规划与汇总", "执行操作", "返回结果"]
        captions = ["1  接收请求", "2  规划下一步", "3  调用工具", "4  接收工具结果", "5  汇总与检查", "6  输出结果"]
    face = font_for("".join(subtitles), 24, font)
    title_font = font_for("AGENT TOOL LOOP", 36, font)
    base = Image.new("RGBA", (1280, 720), "#f5f2ea")
    draw = ImageDraw.Draw(base)
    draw.text((65, 36), "AGENT TOOL LOOP", font=title_font, fill="#263c37")
    draw.text((65, 96), "Fixed-layout process illustration", font=font_for("Illustration", 22, font), fill="#64746c")
    nodes = [(65, 270, 275, 410), (445, 260, 680, 425), (935, 135, 1195, 275), (935, 455, 1195, 595)]
    paths = [[(275, 340), (445, 340)], [(680, 300), (805, 300), (805, 205), (935, 205)],
             [(935, 250), (845, 250), (845, 385), (680, 385)], [(680, 405), (785, 405), (785, 525), (935, 525)]]
    for points in paths:
        _arrow(draw, points, "#b2beb7")
    for index, bounds in enumerate(nodes):
        draw.rounded_rectangle(bounds, radius=22, fill="white", outline="#b8c5bd", width=2)
        center = (bounds[0] + bounds[2]) / 2
        draw.text((center, bounds[1] + 48), titles[index], font=font_for(titles[index], 28, font), fill="#263c37", anchor="mm")
        draw.text((center, bounds[1] + 96), subtitles[index], font=face, fill="#64746c", anchor="mm")
    if mascot is not None:
        base.alpha_composite(mascot.convert("RGBA").resize((106, 106), Image.Resampling.LANCZOS), (510, 145))
    phases = [(0, 1), (None, 1), (1, 2), (2, 1), (None, 1), (3, 3)]
    frames = []
    for phase, (path_index, node) in enumerate(phases):
        for tick in range(8):
            frame = base.copy()
            draw = ImageDraw.Draw(frame)
            bounds = nodes[node]
            draw.rounded_rectangle((bounds[0] - 4, bounds[1] - 4, bounds[2] + 4, bounds[3] + 4), radius=26, outline="#087f79", width=5)
            if path_index is not None:
                points = paths[path_index]
                _arrow(draw, points, "#087f79")
                x, y = _path_point(points, tick / 7)
                draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill="#db7a3c", outline="#f5f2ea", width=2)
            draw.rounded_rectangle((65, 635, 1195, 695), radius=15, fill="#e3ebe4")
            draw.text((630, 665), captions[phase], font=face, fill="#263c37", anchor="mm")
            from PIL import ImageOps
            fitted = ImageOps.contain(frame, size, Image.Resampling.LANCZOS)
            output = Image.new("RGBA", size, "#f5f2ea")
            output.alpha_composite(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
            frames.append(output)
    return frames


def _arrow(draw, points, color):
    draw.line(points, fill=color, width=5, joint="curve")
    previous, tip = points[-2:]
    angle = math.atan2(tip[1] - previous[1], tip[0] - previous[0])
    wings = [(tip[0] - 16 * math.cos(angle + offset), tip[1] - 16 * math.sin(angle + offset)) for offset in [-0.45, 0.45]]
    draw.polygon([tip, *wings], fill=color)


def _path_point(points, progress):
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:])]
    remaining = progress * sum(lengths)
    for start, end, length in zip(points, points[1:], lengths):
        if remaining <= length:
            weight = remaining / length
            return start[0] + (end[0] - start[0]) * weight, start[1] + (end[1] - start[1]) * weight
        remaining -= length
    return points[-1]
