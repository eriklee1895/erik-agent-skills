#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27,<1", "pillow>=13,<14", "numpy>=1.26,<3", "fonttools>=4,<5"]
# ///
"""Create animated WebP and GIF with Seedream Pro and portable local composition."""

import argparse
import asyncio
from io import BytesIO
import json
import math
from pathlib import Path
import re
import sys
import tempfile
import time

from PIL import Image, ImageOps

import animation_io as media
import composition
import seedream_client as ark

SKILL = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL / "assets/templates"


def dimensions(value):
    try:
        width, height = map(int, value.lower().split("x"))
    except (ValueError, AttributeError):
        raise argparse.ArgumentTypeError("Use WIDTHxHEIGHT.")
    if min(width, height) < 1 or max(width, height) > 16383:
        raise argparse.ArgumentTypeError("Dimensions must be1–16383 pixels.")
    return width, height


def region(value):
    try:
        result = tuple(float(part) for part in value.split(","))
        composition.rectangle(result, (1000, 1000))
        return result
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError("Use normalized x,y,width,height inside0–1.")


def grid_value(value):
    try:
        columns, rows = map(int, value.lower().split("x"))
    except ValueError:
        raise argparse.ArgumentTypeError("Use COLUMNSxROWS.")
    if min(columns, rows) < 1:
        raise argparse.ArgumentTypeError("Grid dimensions must be positive.")
    return columns, rows


def read_template(name):
    if not re.fullmatch(r"[a-z0-9-]+", name):
        raise ValueError("Use a template name from the templates command.")
    path = TEMPLATES / f"{name}.json"
    if not path.is_file():
        raise ValueError(f"Unknown template: {name}")
    return json.loads(path.read_text())


def resolve_format(args, output=None):
    explicit = args.format
    if explicit != "auto":
        return explicit
    if output and Path(output).suffix.lower() in {".gif", ".webp"}:
        return Path(output).suffix.lower()[1:]
    return "gif" if args.destination in {"chat", "notion"} else "webp"


def sheet_plan(count, size, selected_grid=None):
    if not 1 <= count <= 24:
        raise ValueError("Generation supports1–24 source poses. Use encode for longer existing timelines.")
    width, height = size
    candidates = []
    for columns in range(1, count + 1):
        rows = math.ceil(count / columns)
        aspect = columns * width / (rows * height)
        if 1 / 16 <= aspect <= 16:
            score = (columns * rows - count) * 10 + abs(math.log(aspect)) + (0.01 if aspect < 1 else 0)
            candidates.append((score, columns, rows))
    if selected_grid:
        columns, rows = selected_grid
        if columns * rows < count:
            raise ValueError("The grid must contain all requested source poses.")
    elif candidates:
        _, columns, rows = min(candidates)
    else:
        raise ValueError("Choose an aspect ratio and pose count compatible with a Seedream sheet.")
    aspect = columns * width / (rows * height)
    if not 1 / 16 <= aspect <= 16:
        raise ValueError("The sheet aspect ratio must be between1:16 and16:1.")
    scale = max(1, 512 / max(size))
    pixel_count = columns * rows * width * height * scale * scale
    scale *= math.sqrt(max(921600, min(4400000, pixel_count)) / pixel_count)
    cell_width = max(16, round(width * scale / 16) * 16)
    cell_height = max(16, round(height * scale / 16) * 16)
    while columns * rows * cell_width * cell_height < 921600:
        cell_width += 16
        cell_height += 16
    while columns * rows * cell_width * cell_height > 4624220:
        if cell_width / width >= cell_height / height:
            cell_width -= 16
        else:
            cell_height -= 16
        if min(cell_width, cell_height) < 16:
            raise ValueError("The requested aspect and grid cannot fit the model's pixel budget.")
    return (columns, rows), (columns * cell_width, rows * cell_height)


def default_webp_mode(args, template):
    if args.webp_mode != "auto":
        return args.webp_mode
    return "lossy" if template in {"product-steam", "photo-reaction"} else "lossless"


def resampling(args):
    return Image.Resampling.NEAREST if args.resample == "nearest" else Image.Resampling.LANCZOS


def prepare_animation(animation, args, format):
    frames = animation.frames
    if args.size:
        frames = [frame.resize(args.size, resampling(args)) for frame in frames]
    if args.key_color:
        frames = [media.key_background(frame, args.key_color) for frame in frames]
    if args.align == "base":
        frames = media.align_base(frames)
    if args.motion_region:
        static = None
        if args.static_image:
            with Image.open(args.static_image) as image:
                static = ImageOps.exif_transpose(image).convert("RGBA")
        frames = composition.static_composite(frames, args.motion_region, static)
    if args.overlays:
        entries = json.loads(Path(args.overlays).read_text())
        frames = composition.overlays(frames, entries, args.font)
    delays = None
    if args.delays:
        delays = json.loads(Path(args.delays).read_text())
    if any(value is not None for value in [args.duration, args.fps, delays]):
        durations = media.timeline(len(frames), duration_ms=args.duration * 1000 if args.duration is not None else None,
                                   fps=args.fps, delays=delays, format=format)
    else:
        durations = media.timeline(len(frames), delays=animation.durations, format=format)
    return media.Animation(frames, durations, animation.plays if args.plays is None else args.plays)


def finish(animation, args, output, template=None, frames_dir=None):
    format = resolve_format(args, output)
    if Path(output).suffix.lower() != f".{format}":
        raise ValueError("Output extension must match the selected format.")
    animation = prepare_animation(animation, args, format)
    if frames_dir:
        media.save_frames(animation.frames, frames_dir, animation.durations, animation.plays)
    metadata = media.encode_animation(animation, output, webp_mode=default_webp_mode(args, template),
                                      quality=args.quality, colors=args.colors if args.colors is not None else 128,
                                      max_bytes=args.max_bytes, force=args.force)
    if frames_dir:
        metadata["frames_dir"] = str(Path(frames_dir).resolve())
        contact = Path(frames_dir) / "contact.jpg"
        media.contact_sheet(animation.frames, contact)
        metadata["contact_sheet"] = str(contact.resolve())
    metadata["alignment"] = args.align
    metadata["resample"] = "nearest" if resampling(args) == Image.Resampling.NEAREST else "lanczos"
    media.write_json(Path(output).with_suffix(Path(output).suffix + ".json"), metadata)
    return metadata


def generation_plan(args):
    template = read_template(args.template) if args.template else None
    defaults = template["defaults"] if template else {}
    prompt = args.prompt or (Path(args.prompt_file).read_text() if args.prompt_file else "")
    if template and not prompt:
        prompt = template.get("prompt_template", "")
        values = {}
        for value in args.set:
            key, separator, text = value.partition("=")
            if not separator:
                raise ValueError("Template slots use --set name=value.")
            values[key] = text
        for name in re.findall(r"\{\{(\w+)\}\}", prompt):
            if name not in values:
                raise ValueError(f"Fill the template slot with --set {name}=...")
            prompt = prompt.replace("{{" + name + "}}", values[name])
    if not prompt.strip():
        raise ValueError("Supply --prompt, --prompt-file or a filled creative template.")
    master = args.master_only or args.template == "sleepy-idle"
    count = 1 if master else args.poses if args.poses is not None else defaults.get("poses", 9)
    if count == 1 and not master:
        raise ValueError("An animation needs at least two source poses. Use --master-only for a still master.")
    if args.cell_inset < 0:
        raise ValueError("Cell inset must be non-negative.")
    if template and args.poses and args.poses != defaults.get("poses", count) and not args.prompt and not args.prompt_file:
        raise ValueError("Adapt the template into --prompt-file before changing its pose structure.")
    size = args.size or tuple(defaults.get("canvas", [256, 256]))
    if args.template == "agent-tool-loop":
        raise ValueError("Use the flow command for the fixed process diagram, or encode your own frames.")
    selected_grid = args.grid or (tuple(defaults["grid"]) if "grid" in defaults and not master and count == defaults.get("poses") else None)
    grid, sheet_size = sheet_plan(count, size, selected_grid)
    if template and "sheet" in defaults and not master and not any([args.grid, args.size, args.poses]):
        sheet_size = tuple(defaults["sheet"])
    if min(sheet_size[0] / grid[0], sheet_size[1] / grid[1]) <= args.cell_inset * 2:
        raise ValueError("Cell inset leaves an empty frame.")
    native_alpha = False
    if args.transparent and len(args.reference) == 1 and not ark._is_url(args.reference[0]):
        with Image.open(args.reference[0]) as image:
            native_alpha = "A" in image.getbands() and image.getchannel("A").getextrema()[0] < 255
    columns, rows = grid
    layout = "Single character master image." if master else (
        f"Animation sprite sheet, exactly {columns} columns and {rows} rows, {count} sequential poses in row-major order. "
        "Equal cells, locked camera and character scale. Keep each subject inside its cell, with no grid lines or labels. "
        "Any trailing unused cells remain empty. "
    )
    if args.transparent and not native_alpha:
        color = {"green": "#00FF00", "magenta": "#FF00FF", "cyan": "#00FFFF"}[args.key_color or "green"]
        layout += f"Uniform flat {color} key background. Subject colors avoid this background color. "
    payload = ark._build_request_body(model=ark.MODEL_PRO, caps=ark.CAPS, prompt=layout + prompt.strip(),
                                      size=f"{sheet_size[0]}x{sheet_size[1]}", output_format="png", watermark=False,
                                      reference_images=None, optimize_prompt="standard", background="transparent" if native_alpha else "opaque")
    if len(args.reference) > 10:
        raise ValueError("Seedream Pro accepts at most10 references.")
    for reference in args.reference:
        if not ark._is_url(reference):
            path = Path(reference).expanduser()
            if not path.is_file() or path.stat().st_size > ark.MAX_REFERENCE_BYTES:
                raise ValueError("Reference images must be readable files no larger than30MB.")
            with Image.open(path) as image:
                if getattr(image, "n_frames", 1) > 1:
                    raise ValueError("Select a still reference frame, or use encode for an existing animation.")
    format = resolve_format(args)
    colors = args.colors if args.colors is not None else defaults.get("palette_colors", 128)
    resample = defaults.get("resize", "lanczos") if args.resample == "auto" else args.resample
    media.validate_export_options(format, default_webp_mode(args, args.template), args.quality, colors, args.max_bytes, args.plays or 0)
    delays = json.loads(Path(args.delays).read_text()) if args.delays else defaults.get("durations_ms")
    media.timeline(count, duration_ms=args.duration * 1000 if args.duration is not None else None,
                   fps=args.fps, delays=delays if args.duration is None and args.fps is None else None, format=format)
    if args.static_image and not args.motion_region:
        raise ValueError("A static image needs --motion-region.")
    if args.align == "base" and not args.transparent:
        raise ValueError("Generated base alignment needs --transparent so the subject can be isolated.")
    if args.static_image:
        with Image.open(args.static_image) as image:
            image = ImageOps.exif_transpose(image)
            image.load()
            if abs(image.width / image.height - size[0] / size[1]) > 0.02:
                raise ValueError("Crop or pad the static image to the animation aspect ratio first.")
    if args.overlays:
        composition.overlay_plan(json.loads(Path(args.overlays).read_text()), size, count, args.font)
    return {"operation": "master" if master else "animation", "model": ark.MODEL_PRO, "format": format,
            "size": list(size), "poses": count, "grid": list(grid), "sheet_size": list(sheet_size),
            "native_alpha": native_alpha, "references_count": len(args.reference), "payload": payload,
            "template": args.template, "colors": colors, "resample": resample,
            "source_upscale": sheet_size[0] / columns < size[0] or sheet_size[1] / rows < size[1]}


def generate(args):
    plan = generation_plan(args)
    if args.dry_run:
        return plan
    args.colors, args.resample = plan["colors"], plan["resample"]
    directory = Path(args.out_dir or f"output/animated-image-gen/{time.time_ns()}").expanduser().resolve()
    if directory.exists():
        raise FileExistsError(f"Job directory exists: {directory}. Keep it for inspection or choose a new job directory.")
    ark._load_dotenv()
    api_key, base_url = ark._get_api_settings()
    directory.mkdir(parents=True, exist_ok=False)
    job_path = directory / "job.json"
    job = {key: value for key, value in plan.items() if key != "payload"}
    job.update(status="submitting", prompt=plan["payload"]["prompt"], paid_operations=1)
    media.write_json(job_path, job)
    payload = dict(plan["payload"])
    references = args.reference
    try:
        if plan["native_alpha"]:
            with Image.open(references[0]) as image:
                character = ImageOps.exif_transpose(image).convert("RGBA")
            cell_size = (plan["sheet_size"][0] // plan["grid"][0], plan["sheet_size"][1] // plan["grid"][1])
            cell = ImageOps.contain(character, cell_size, resampling(args))
            board = Image.new("RGBA", tuple(plan["sheet_size"]))
            for index in range(plan["poses"]):
                board.alpha_composite(cell, (index % plan["grid"][0] * cell_size[0] + (cell_size[0] - cell.width) // 2,
                                            index // plan["grid"][0] * cell_size[1] + (cell_size[1] - cell.height) // 2))
            reference_path = directory / "alpha-reference.png"
            board.save(reference_path)
            references = [str(reference_path)]
        if references:
            payload["image"] = ark._resolve_reference_images(references)
            if len(payload["image"]) == 1:
                payload["image"] = payload["image"][0]
        images, revised, usage, reported, elapsed = asyncio.run(ark._generate_with_retry(api_key, base_url, payload, args.timeout))
        if len(images) != 1:
            raise ValueError("The sprite operation expected exactly one output image.")
        with Image.open(BytesIO(images[0].content)) as image:
            sheet = image.convert("RGBA")
        sheet.save(directory / "source.png")
        job.update(status="source_ready", actual_sheet_size=list(sheet.size), api_reported_size=reported,
                   api_elapsed_ms=elapsed, usage=usage, revised_prompt=revised)
        media.write_json(job_path, job)
        if plan["operation"] == "master":
            job.update(status="master_ready", master=str(directory / "source.png"))
        else:
            frames = media.split_sheet(sheet, tuple(plan["grid"]), plan["poses"], tuple(plan["size"]), args.cell_inset, resampling(args))
            if args.transparent and not plan["native_alpha"]:
                frames = [media.key_background(frame, args.key_color or "green") for frame in frames]
            default_delays = read_template(args.template)["defaults"].get("durations_ms") if args.template else None
            default_delay = read_template(args.template)["defaults"].get("delay_ms", 120) if args.template else 120
            durations = default_delays or [default_delay] * len(frames)
            args.size = tuple(plan["size"])
            saved_key = args.key_color
            args.key_color = None
            result = finish(media.Animation(frames, durations), args, directory / f"animation.{plan['format']}",
                            args.template, directory / "frames")
            args.key_color = saved_key
            job.update(status="complete", output=result)
        media.write_json(job_path, job)
        return job
    except BaseException as error:
        job.update(status="outcome_unknown" if isinstance(error, ark._APIError) and error.code == "OutcomeUnknown" else "needs_review",
                   error_code=getattr(error, "code", type(error).__name__), error=str(error))
        media.write_json(job_path, job)
        raise


def encode(args):
    output = Path(args.out).expanduser().resolve()
    if output.exists() and not args.force:
        raise FileExistsError(f"Output exists: {output}")
    if args.grid:
        if not args.poses:
            raise ValueError("A sheet input needs --poses and --grid.")
        with Image.open(args.input) as image:
            size = args.size or (round(image.width / args.grid[0]), round(image.height / args.grid[1]))
            frames = media.split_sheet(image.convert("RGBA"), args.grid, args.poses, size, args.cell_inset, resampling(args))
        animation = media.Animation(frames, [120] * len(frames))
    else:
        animation = media.load_frames(args.input)
    transformed = any([args.size, args.key_color, args.motion_region, args.overlays, args.align == "base", args.grid])
    frames_dir = None
    if transformed:
        output.parent.mkdir(parents=True, exist_ok=True)
        frames_dir = Path(tempfile.mkdtemp(prefix=output.stem + "-frames-", dir=output.parent))
    return finish(animation, args, output, frames_dir=frames_dir)


def local_motion(args):
    output = Path(args.out).expanduser().resolve()
    if output.exists() and not args.force:
        raise FileExistsError(f"Output exists: {output}")
    if args.command == "flow":
        mascot = Image.open(args.mascot).convert("RGBA") if args.mascot else None
        frames = composition.flow_frames(args.size or (1280, 720), mascot, args.font, args.language)
        animation = media.Animation(frames, [100] * len(frames))
        template = "agent-tool-loop"
    else:
        with Image.open(args.input) as image:
            source = image.convert("RGBA")
        if args.size:
            source = source.resize(args.size, resampling(args))
        if args.key_color:
            source = media.key_background(source, args.key_color)
        frames = composition.breathing_frames(source, args.region, args.frames, args.amplitude)
        animation = media.Animation(frames, [160] * len(frames))
        args.key_color = None
        template = "sleepy-idle"
    output.parent.mkdir(parents=True, exist_ok=True)
    frames_dir = Path(tempfile.mkdtemp(prefix=output.stem + "-frames-", dir=output.parent))
    return finish(animation, args, output, template, frames_dir)


def export_options(parser):
    parser.add_argument("--format", choices=["auto", "webp", "gif"], default="auto")
    parser.add_argument("--destination", choices=["web", "chat", "notion"], default="web")
    parser.add_argument("--size", type=dimensions)
    timing = parser.add_mutually_exclusive_group()
    timing.add_argument("--duration", type=float, help="Total cycle duration in seconds.")
    timing.add_argument("--fps", type=float)
    timing.add_argument("--delays", help="JSON file of source-frame delays in milliseconds.")
    parser.add_argument("--plays", type=int, help="Total plays,0 for infinite. Existing animation inputs retain their setting.")
    parser.add_argument("--webp-mode", choices=["auto", "lossy", "lossless"], default="auto")
    parser.add_argument("--quality", type=int, default=80)
    parser.add_argument("--colors", type=int, help="Initial GIF palette size, defaults to the template or128.")
    parser.add_argument("--resample", choices=["auto", "lanczos", "nearest"], default="auto")
    parser.add_argument("--max-bytes", type=int)
    parser.add_argument("--key-color", choices=["green", "magenta", "cyan"])
    parser.add_argument("--align", choices=["none", "base"], default="none", help="Optionally register an isolated transparent subject to its first-frame base.")
    parser.add_argument("--motion-region", type=region)
    parser.add_argument("--static-image")
    parser.add_argument("--overlays", help="JSON list of local text/rectangle overlays.")
    parser.add_argument("--font", help="Font file path. ANIMATED_IMAGE_FONT is also supported.")
    parser.add_argument("--force", action="store_true", help="Replace an encoded local output.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("generate", help="Generate a PNG sprite sheet using Seedream Pro and finish the animation.")
    create.add_argument("--prompt")
    create.add_argument("--prompt-file")
    create.add_argument("--template")
    create.add_argument("--set", action="append", default=[])
    create.add_argument("--poses", type=int)
    create.add_argument("--grid", type=grid_value)
    create.add_argument("--reference", action="append", default=[])
    create.add_argument("--transparent", action="store_true")
    create.add_argument("--master-only", action="store_true")
    create.add_argument("--cell-inset", type=int, default=0)
    create.add_argument("--out-dir")
    create.add_argument("--timeout", type=int, default=300)
    create.add_argument("--dry-run", action="store_true")
    export_options(create)
    convert = commands.add_parser("encode", help="Encode PNG frames, a sheet, or an existing animation.")
    convert.add_argument("--input", required=True)
    convert.add_argument("--out", required=True)
    convert.add_argument("--grid", type=grid_value)
    convert.add_argument("--poses", type=int)
    convert.add_argument("--cell-inset", type=int, default=0)
    export_options(convert)
    inspect = commands.add_parser("inspect", help="Decode and report actual animation properties.")
    inspect.add_argument("input")
    templates = commands.add_parser("templates", help="List or read a creative template.")
    templates.add_argument("name", nargs="?")
    breathing = commands.add_parser("breathe", help="Animate a still pose with bounded local breathing.")
    breathing.add_argument("--input", required=True)
    breathing.add_argument("--region", type=region, required=True)
    breathing.add_argument("--frames", type=int, default=12)
    breathing.add_argument("--amplitude", type=float, default=1.0)
    breathing.add_argument("--out", required=True)
    export_options(breathing)
    flow = commands.add_parser("flow", help="Render the measured fixed four-node process diagram.")
    flow.add_argument("--out", required=True)
    flow.add_argument("--mascot")
    flow.add_argument("--language", choices=["en", "zh"], default="en")
    export_options(flow)
    args = parser.parse_args()
    try:
        if args.command == "generate":
            result = generate(args)
        elif args.command == "encode":
            result = encode(args)
        elif args.command == "inspect":
            result = media.inspect_animation(args.input)
        elif args.command == "templates":
            result = read_template(args.name) if args.name else [{"id": path.stem, "title": json.loads(path.read_text())["title"]} for path in sorted(TEMPLATES.glob("*.json"))]
        else:
            result = local_motion(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, ark._APIError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
