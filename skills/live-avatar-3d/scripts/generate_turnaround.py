#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["openai>=3.10.0"]
# ///
"""Create one four-view GPT Image 2.5 reference sheet for a 3D avatar."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping


MODEL = "gpt-image-2.5-sunburst"
DEFAULT_SIZE = "1536x1024"
DEFAULT_QUALITY = "high"
MAX_INPUT_BYTES = 50 * 1024 * 1024
DEFAULT_PROMPT = """Edit Image 1 into a clean 2-by-2 character turnaround sheet of the exact same character.
Show four full-body views at the same scale and on the same simple neutral background:
top-left front, top-right three-quarter, bottom-left profile, bottom-right back.
Preserve the character's visible identity, silhouette, proportions, palette, face,
clothing construction, and accessories. Keep the same rendering style, lighting,
pose, and camera height across the four cells. Keep clear separation and margins.
Do not add text, labels, numbers, extra characters, props, costume changes, or a
watermark. Details hidden in Image 1 may be inferred simply; do not present those
inferences as facts. This sheet is a visual guide for building a 3D model, not a
replacement for the original reference."""


def build_prompt(character_notes: str = "") -> str:
    notes = character_notes.strip()
    if not notes:
        return DEFAULT_PROMPT
    return (
        f"{DEFAULT_PROMPT}\n\n"
        "Character details to preserve exactly where visible:\n"
        f"{notes}"
    )


def resolve_credentials(env: Mapping[str, str]) -> tuple[str, str | None]:
    custom_key = env.get("CUSTOM_OPENAI_API_KEY")
    custom_base_url = env.get("CUSTOM_OPENAI_BASE_URL")
    if custom_key or custom_base_url:
        if not custom_key or not custom_base_url:
            raise ValueError(
                "CUSTOM_OPENAI_API_KEY and CUSTOM_OPENAI_BASE_URL must be set together"
            )
        return custom_key, custom_base_url

    api_key = env.get("OPENAI_API_KEY")
    base_url = env.get("OPENAI_BASE_URL")
    if not api_key:
        raise ValueError(
            "Set OPENAI_API_KEY, or set CUSTOM_OPENAI_API_KEY and "
            "CUSTOM_OPENAI_BASE_URL together. Do not paste credentials into chat."
        )
    return api_key, base_url


def load_dotenv(path: Path, env: dict[str, str] | None = None) -> dict[str, str]:
    """Load simple KEY=VALUE entries without printing or overwriting the environment."""
    target = os.environ if env is None else env
    if not path.is_file():
        return dict(target)
    loaded = dict(target)
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key and key not in loaded:
            loaded[key] = value
    return loaded


def check_paths(source: Path, output: Path, *, force: bool) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Input image does not exist: {source}")
    if source.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("Input image must be smaller than 50 MB")
    if source.resolve() == output.resolve():
        raise ValueError("Input and output paths must differ")
    if output.suffix.lower() != ".png":
        raise ValueError("Turnaround output path must end in .png")
    metadata = output.with_suffix(".json")
    if not force and (output.exists() or metadata.exists()):
        existing = output if output.exists() else metadata
        raise FileExistsError(f"Output already exists: {existing}; choose a new path")


def save_atomically(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
            temp_path = Path(temporary.name)
            temporary.write(data)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def request_turnaround(
    *,
    source: Path,
    output: Path,
    prompt: str,
    size: str,
    quality: str,
    force: bool,
    env: Mapping[str, str] | None = None,
) -> dict[str, object]:
    check_paths(source, output, force=force)
    api_key, base_url = resolve_credentials(env or load_dotenv(Path.cwd() / ".env"))
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install the OpenAI SDK by running this file with uv") from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        max_retries=0,
        timeout=180.0,
    )
    started = time.monotonic()
    with source.open("rb") as image_file:
        response = client.images.edit(
            model=MODEL,
            image=image_file,
            prompt=prompt,
            size=size,
            quality=quality,
            output_format="png",
        )
    elapsed = round(time.monotonic() - started, 3)
    image_data = getattr(response.data[0], "b64_json", None)
    if not image_data:
        raise RuntimeError("Image API returned no PNG data")
    png_bytes = base64.b64decode(image_data, validate=True)
    save_atomically(output, png_bytes)

    usage = getattr(response, "usage", None)
    if usage is not None and hasattr(usage, "model_dump"):
        usage = usage.model_dump(mode="json")
    elif usage is not None:
        usage = str(usage)
    metadata: dict[str, object] = {
        "schema_version": 1,
        "model": MODEL,
        "size": size,
        "quality": quality,
        "output_format": "png",
        "input_name": source.name,
        "output": str(output),
        "elapsed_seconds": elapsed,
        "request_id": getattr(response, "_request_id", None),
        "usage": usage,
        "prompt": prompt,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    save_atomically(
        output.with_suffix(".json"),
        (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    return metadata


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create one GPT Image 2.5 Sunburst four-view reference sheet."
    )
    parser.add_argument("--image", required=True, type=Path, help="Source character image")
    parser.add_argument("--out", required=True, type=Path, help="New .png output path")
    prompt_group = parser.add_mutually_exclusive_group()
    prompt_group.add_argument("--prompt", help="Optional character-specific preservation notes")
    prompt_group.add_argument("--prompt-file", type=Path, help="File with character-specific notes")
    parser.add_argument("--size", default=DEFAULT_SIZE, help=f"Image size (default: {DEFAULT_SIZE})")
    parser.add_argument(
        "--quality",
        choices=("medium", "high", "xhigh", "max"),
        default=DEFAULT_QUALITY,
    )
    parser.add_argument("--force", action="store_true", help="Replace an existing output")
    parser.add_argument("--dry-run", action="store_true", help="Show the plan without calling the API")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        check_paths(args.image, args.out, force=args.force)
        notes = args.prompt or ""
        if args.prompt_file:
            notes = args.prompt_file.read_text(encoding="utf-8")
        prompt = build_prompt(notes)
        if args.dry_run:
            print(f"Model: {MODEL}")
            print(f"Input: {args.image}")
            print(f"Output: {args.out}")
            print(f"Size: {args.size}; quality: {args.quality}; requests: 1")
            return 0

        print(f"Sending one {MODEL} reference-edit request...")
        metadata = request_turnaround(
            source=args.image,
            output=args.out,
            prompt=prompt,
            size=args.size,
            quality=args.quality,
            force=args.force,
        )
        print(f"Saved: {args.out}")
        print(f"Metadata: {args.out.with_suffix('.json')}")
        print(f"Elapsed: {metadata['elapsed_seconds']}s")
        return 0
    except Exception as exc:
        print(f"Turnaround generation failed ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
