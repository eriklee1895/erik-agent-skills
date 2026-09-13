#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "openai>=3.10.0",
#   "pillow>=10.0.0",
# ]
# ///
"""Generate, edit, stream, and batch-create images with GPT Image 2.5."""

from __future__ import annotations

import argparse
import asyncio
import base64
import datetime as dt
import getpass
import json
import os
import random
import re
import sys
import time
import uuid
from contextlib import ExitStack
from io import BytesIO
from pathlib import Path
from threading import Event, Thread
from typing import Any, Iterable, Optional
from urllib.parse import urlparse

DEFAULT_MODEL = "gpt-image-2.5-flare"
ALLOWED_MODELS = {
    "gpt-image-2.5-flare",
    "gpt-image-2.5-flare-2026-09-08",
    "gpt-image-2.5-sunburst",
    "gpt-image-2.5-sunburst-2026-09-08",
}
MODEL_ALIASES = {
    "flare": "gpt-image-2.5-flare",
    "sunburst": "gpt-image-2.5-sunburst",
}
ALLOWED_QUALITIES = {"auto", "low", "medium", "high", "xhigh", "max"}
ALLOWED_BACKGROUNDS = {"auto", "opaque", "transparent"}
ALLOWED_OUTPUT_FORMATS = {"png", "jpeg", "webp"}
ALLOWED_MODERATION = {"auto", "low"}
ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}

SIZE_PRESETS = {
    "square": "1024x1024",
    "landscape": "1536x1024",
    "portrait": "1024x1536",
    "wide": "1792x1024",
    "2k-square": "2048x2048",
    "2k-landscape": "2048x1152",
    "4k-landscape": "3840x2160",
    "4k-portrait": "2160x3840",
    "auto": "auto",
}

MAX_PROMPT_CHARS = 32_000
MAX_INPUT_IMAGES = 16
MAX_IMAGE_BYTES = 50 * 1024 * 1024
MAX_MASK_BYTES = 4 * 1024 * 1024
MAX_N = 10
MAX_CONCURRENCY = 25
MAX_ATTEMPTS = 10
MAX_BATCH_JOBS = 500
HEARTBEAT_SECONDS = 15.0
MIN_PIXELS = 655_360
MAX_PIXELS = 8_294_400
MAX_EDGE = 3_840
EXPERIMENTAL_PIXELS = 2_560 * 1_440
DEFAULT_OUTPUT = Path("output/gpt-image-api/output.png")
DEFAULT_BATCH_DIR = Path("output/gpt-image-api/batch")
OFOX_API_HOSTS = {"api.ofox.ai", "api.ofox.io"}


class UsageError(ValueError):
    """Raised when a request violates the local CLI contract."""


def _warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _json_safe(model_dump(mode="json", exclude_none=True))
    return str(value)


def _load_dotenv() -> None:
    path = Path.cwd() / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key and value and key not in os.environ:
            os.environ[key] = value


def get_api_settings(*, require_key: bool) -> tuple[Optional[str], Optional[str]]:
    custom_key = os.getenv("CUSTOM_OPENAI_API_KEY")
    custom_base_url = os.getenv("CUSTOM_OPENAI_BASE_URL")
    if custom_key or custom_base_url:
        if not custom_key or not custom_base_url:
            raise UsageError(
                "CUSTOM_OPENAI_API_KEY and CUSTOM_OPENAI_BASE_URL must be set together"
            )
        return custom_key, custom_base_url

    key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    if key or not require_key:
        return key, base_url
    if sys.stdin.isatty() and sys.stderr.isatty():
        try:
            key = getpass.getpass("OpenAI API key (temporary, not saved): ").strip()
        except (EOFError, KeyboardInterrupt):
            key = None
        if key:
            return key, base_url
    raise UsageError(
        "Set CUSTOM_OPENAI_API_KEY or OPENAI_API_KEY for live requests. "
        "Do not paste credentials into chat."
    )


def resolve_model(value: Optional[str] = None) -> str:
    candidate = value or DEFAULT_MODEL
    candidate = MODEL_ALIASES.get(candidate, candidate)
    if candidate not in ALLOWED_MODELS:
        allowed = ", ".join(sorted(ALLOWED_MODELS | set(MODEL_ALIASES)))
        raise UsageError(f"Unsupported model {candidate!r}. Use one of: {allowed}")
    return candidate


def resolve_provider(base_url: Optional[str]) -> str:
    """Classify only providers that change the GPT Image wire model name."""
    if not base_url:
        return "openai"
    hostname = (urlparse(base_url).hostname or "").lower()
    return "ofox" if hostname in OFOX_API_HOSTS else "custom"


def resolve_wire_model(model: str, base_url: Optional[str]) -> str:
    """Return the provider-facing model ID without changing the Images API."""
    canonical = resolve_model(model)
    if resolve_provider(base_url) == "ofox":
        return f"openai/{canonical}"
    return canonical


def resolve_provider_spec(
    spec: dict[str, Any], base_url: Optional[str]
) -> dict[str, Any]:
    resolved = dict(spec)
    resolved["provider"] = resolve_provider(base_url)
    resolved["wire_model"] = resolve_wire_model(spec["model"], base_url)
    return resolved


def validate_quality(value: str) -> str:
    if value not in ALLOWED_QUALITIES:
        raise UsageError(
            "quality must be one of auto, low, medium, high, xhigh, or max"
        )
    return value


def validate_prompt(prompt: str) -> str:
    if not prompt or not prompt.strip():
        raise UsageError("prompt must not be empty")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise UsageError(
            f"prompt is {len(prompt)} characters; maximum is {MAX_PROMPT_CHARS}"
        )
    return prompt


def validate_size(value: str) -> str:
    resolved = SIZE_PRESETS.get(value, value)
    if resolved == "auto":
        return resolved
    match = re.fullmatch(r"([0-9]+)x([0-9]+)", resolved)
    if not match:
        raise UsageError("size must be auto, a documented preset, or WIDTHxHEIGHT")
    width, height = (int(match.group(1)), int(match.group(2)))
    if width <= 0 or height <= 0:
        raise UsageError("size edges must be positive")
    if width % 16 or height % 16:
        raise UsageError("size width and height must both be divisible by 16")
    if max(width, height) > MAX_EDGE:
        raise UsageError(f"size edges must be at most {MAX_EDGE}px")
    if max(width, height) / min(width, height) > 3:
        raise UsageError("size aspect ratio must be between 1:3 and 3:1")
    pixels = width * height
    if pixels < MIN_PIXELS or pixels > MAX_PIXELS:
        raise UsageError(
            f"size must contain between {MIN_PIXELS:,} and {MAX_PIXELS:,} pixels"
        )
    return resolved


def is_experimental_size(value: str) -> bool:
    resolved = validate_size(value)
    if resolved == "auto":
        return False
    width, height = (int(part) for part in resolved.split("x", 1))
    return width * height > EXPERIMENTAL_PIXELS


def normalize_output_format(value: str) -> str:
    normalized = "jpeg" if value.lower() == "jpg" else value.lower()
    if normalized not in ALLOWED_OUTPUT_FORMATS:
        raise UsageError("output-format must be png, jpeg, or webp")
    return normalized


def validate_output_options(
    background: str, output_format: str, output_compression: Optional[int]
) -> tuple[str, str, Optional[int]]:
    if background not in ALLOWED_BACKGROUNDS:
        raise UsageError("background must be auto, opaque, or transparent")
    output_format = normalize_output_format(output_format)
    if background == "transparent" and output_format not in {"png", "webp"}:
        raise UsageError("transparent background requires PNG or WebP output")
    if output_compression is not None:
        if not 0 <= output_compression <= 100:
            raise UsageError("output-compression must be between 0 and 100")
        if output_format not in {"jpeg", "webp"}:
            raise UsageError("output-compression is only valid for JPEG or WebP")
    return background, output_format, output_compression


def _validate_common(
    *,
    prompt: str,
    model: Optional[str],
    n: int,
    size: str,
    quality: str,
    background: str,
    output_format: str,
    output_compression: Optional[int],
    stream: bool,
    partial_images: int,
) -> dict[str, Any]:
    if not 1 <= n <= MAX_N:
        raise UsageError(f"n must be between 1 and {MAX_N}")
    if not 0 <= partial_images <= 3:
        raise UsageError("partial-images must be between 0 and 3")
    if partial_images and not stream:
        raise UsageError("partial-images requires --stream")
    if stream and n != 1:
        raise UsageError("streaming supports one final output per CLI invocation")
    background, output_format, output_compression = validate_output_options(
        background, output_format, output_compression
    )
    resolved_size = validate_size(size)
    if is_experimental_size(resolved_size):
        _warn("requested resolution exceeds 2560x1440 total pixels and is experimental")
    return {
        "model": resolve_model(model),
        "prompt": validate_prompt(prompt),
        "n": n,
        "size": resolved_size,
        "quality": validate_quality(quality),
        "background": background,
        "output_format": output_format,
        "output_compression": output_compression,
        "stream": stream,
        "partial_images": partial_images,
    }


def build_generate_spec(
    *,
    prompt: str,
    model: Optional[str] = None,
    n: int = 1,
    size: str = "auto",
    quality: str = "auto",
    background: str = "auto",
    output_format: str = "png",
    output_compression: Optional[int] = None,
    moderation: str = "auto",
    stream: bool = False,
    partial_images: int = 0,
) -> dict[str, Any]:
    if moderation not in ALLOWED_MODERATION:
        raise UsageError("moderation must be auto or low")
    spec = _validate_common(
        prompt=prompt,
        model=model,
        n=n,
        size=size,
        quality=quality,
        background=background,
        output_format=output_format,
        output_compression=output_compression,
        stream=stream,
        partial_images=partial_images,
    )
    return {
        "command": "generate",
        "endpoint": "/v1/images/generations",
        **spec,
        "moderation": moderation,
    }


def _validate_image_file(path: Path) -> Path:
    if not path.is_file():
        raise UsageError(f"input image does not exist: {path}")
    if path.suffix.lower() not in ALLOWED_IMAGE_SUFFIXES:
        raise UsageError(f"unsupported input image format: {path.suffix or '<none>'}")
    if path.stat().st_size >= MAX_IMAGE_BYTES:
        raise UsageError(f"input image must be smaller than 50MB: {path}")
    try:
        from PIL import Image

        with Image.open(path) as image:
            image.verify()
    except Exception as exc:
        raise UsageError(f"input image is not decodable: {path}: {exc}") from exc
    return path


def _validate_mask(mask: Path, first_image: Path) -> Path:
    if not mask.is_file():
        raise UsageError(f"mask does not exist: {mask}")
    if mask.suffix.lower() != ".png":
        raise UsageError("mask must be a PNG file")
    if mask.stat().st_size >= MAX_MASK_BYTES:
        raise UsageError("mask must be smaller than 4MB")
    try:
        from PIL import Image

        with Image.open(mask) as mask_image, Image.open(first_image) as source_image:
            if mask_image.size != source_image.size:
                raise UsageError("mask dimensions must match the first input image")
            if (
                "A" not in mask_image.getbands()
                and "transparency" not in mask_image.info
            ):
                raise UsageError("mask must contain an alpha channel")
            minimum_alpha, _ = mask_image.convert("RGBA").getchannel("A").getextrema()
            if minimum_alpha != 0:
                raise UsageError(
                    "mask must contain at least one fully transparent pixel"
                )
    except UsageError:
        raise
    except Exception as exc:
        raise UsageError(f"could not inspect mask and first image: {exc}") from exc
    return mask


def build_edit_spec(
    *,
    prompt: str,
    images: Iterable[Path | str],
    roles: Optional[list[str]] = None,
    mask: Optional[Path | str] = None,
    model: Optional[str] = None,
    n: int = 1,
    size: str = "auto",
    quality: str = "auto",
    background: str = "auto",
    output_format: str = "png",
    output_compression: Optional[int] = None,
    stream: bool = False,
    partial_images: int = 0,
) -> dict[str, Any]:
    paths = [_validate_image_file(Path(path)) for path in images]
    if not paths:
        raise UsageError("edit requires at least one --image")
    if len(paths) > MAX_INPUT_IMAGES:
        raise UsageError(f"edit accepts at most {MAX_INPUT_IMAGES} input images")
    if roles is not None and len(roles) != len(paths):
        raise UsageError("provide exactly one --image-role for each --image")
    if roles is not None and any(not role.strip() for role in roles):
        raise UsageError("image roles must not be empty")
    role_values = roles or [f"image {index}" for index in range(1, len(paths) + 1)]
    mask_path = _validate_mask(Path(mask), paths[0]) if mask is not None else None
    spec = _validate_common(
        prompt=prompt,
        model=model,
        n=n,
        size=size,
        quality=quality,
        background=background,
        output_format=output_format,
        output_compression=output_compression,
        stream=stream,
        partial_images=partial_images,
    )
    return {
        "command": "edit",
        "endpoint": "/v1/images/edits",
        **spec,
        "images": [str(path) for path in paths],
        "image_roles": role_values,
        "mask": str(mask_path) if mask_path else None,
    }


def build_output_paths(out: Path, output_format: str, n: int) -> list[Path]:
    output_format = normalize_output_format(output_format)
    expected_suffix = "." + output_format
    if out.suffix.lower() == ".jpg" and output_format == "jpeg":
        out = out.with_suffix(".jpeg")
    elif not out.suffix:
        out = out.with_suffix(expected_suffix)
    elif out.suffix.lower() != expected_suffix:
        raise UsageError(
            f"output path suffix {out.suffix!r} does not match {output_format!r}"
        )
    if n == 1:
        return [out]
    return [
        out.with_name(f"{out.stem}-{index:02d}{out.suffix}")
        for index in range(1, n + 1)
    ]


def _metadata_path(path: Path) -> Path:
    return path.with_suffix(".json")


def _partial_path(path: Path, index: int) -> Path:
    return path.with_name(f"{path.stem}.partial-{index + 1:02d}{path.suffix}")


def _downscale_path(path: Path, suffix: str) -> Path:
    return path.with_name(f"{path.stem}{suffix}{path.suffix}")


def preflight_output_paths(
    paths: Iterable[Path],
    *,
    force: bool,
    partial_images: int = 0,
    downscale_max_dim: Optional[int] = None,
    downscale_suffix: str = "-web",
) -> None:
    paths = list(paths)
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    if force:
        return
    candidates: list[Path] = []
    for path in paths:
        candidates.extend((path, _metadata_path(path)))
        candidates.extend(_partial_path(path, index) for index in range(partial_images))
        if downscale_max_dim is not None:
            candidates.append(_downscale_path(path, downscale_suffix))
    existing = [str(path) for path in candidates if path.exists()]
    if existing:
        raise UsageError(
            "refusing to overwrite existing output: " + ", ".join(existing)
        )


def write_bytes(path: Path, data: bytes, *, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if force:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_json(path: Path, data: dict[str, Any], *, force: bool) -> None:
    encoded = json.dumps(_json_safe(data), ensure_ascii=False, indent=2).encode("utf-8")
    write_bytes(path, encoded + b"\n", force=force)


def extract_response_metadata(response: Any) -> dict[str, Any]:
    def value(name: str) -> Any:
        if isinstance(response, dict):
            return response.get(name)
        return getattr(response, name, None)

    usage = value("usage")
    return {
        "size": value("size"),
        "quality": value("quality"),
        "background": value("background"),
        "output_format": value("output_format"),
        "usage": _json_safe(usage),
        "request_id": value("_request_id") or value("request_id"),
    }


def decode_base64_image(value: Optional[str]) -> bytes:
    if not value:
        raise UsageError("API response did not contain b64_json image data")
    try:
        decoded = base64.b64decode(value, validate=True)
    except Exception as exc:
        raise UsageError("API returned invalid base64 image data") from exc
    if not decoded:
        raise UsageError("API returned empty image data")
    return decoded


def validate_transparent_image(data: bytes) -> None:
    try:
        from PIL import Image

        with Image.open(BytesIO(data)) as image:
            if "A" not in image.getbands() and "transparency" not in image.info:
                raise UsageError("transparent output does not contain an alpha channel")
            rgba = image.convert("RGBA")
            minimum_alpha, _ = rgba.getchannel("A").getextrema()
            if minimum_alpha == 255:
                raise UsageError("transparent output contains no transparent pixels")
    except UsageError:
        raise
    except Exception as exc:
        raise UsageError(f"could not inspect transparent output: {exc}") from exc


def downscale_image(data: bytes, *, max_dim: int, output_format: str) -> bytes:
    if max_dim <= 0:
        raise UsageError("downscale-max-dim must be positive")
    try:
        from PIL import Image

        with Image.open(BytesIO(data)) as source:
            image = source.copy()
        image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        if output_format == "jpeg" and image.mode not in {"RGB", "L"}:
            background = Image.new("RGB", image.size, "white")
            if "A" in image.getbands():
                background.paste(
                    image.convert("RGBA"), mask=image.convert("RGBA").getchannel("A")
                )
            else:
                background.paste(image.convert("RGB"))
            image = background
        output = BytesIO()
        image.save(
            output, format="JPEG" if output_format == "jpeg" else output_format.upper()
        )
        return output.getvalue()
    except UsageError:
        raise
    except Exception as exc:
        raise UsageError(f"could not downscale image: {exc}") from exc


def _error_status(exc: Any) -> Optional[int]:
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    return status if isinstance(status, int) else None


def _error_code(exc: Any) -> Optional[str]:
    code = getattr(exc, "code", None)
    if isinstance(code, str):
        return code
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        error = body.get("error", body)
        if isinstance(error, dict) and isinstance(error.get("code"), str):
            return error["code"]
    return None


def _moderation_detail(exc: Any) -> str:
    body = getattr(exc, "body", None)
    if not isinstance(body, dict):
        return ""
    error = body.get("error", body)
    if not isinstance(error, dict):
        return ""
    details = error.get("moderation_details")
    if not isinstance(details, dict):
        return ""
    stage = details.get("moderation_stage")
    categories = details.get("categories")
    parts = []
    if stage:
        parts.append(f"moderation_stage={stage}")
    if categories:
        parts.append(f"categories={_json_safe(categories)}")
    return " ".join(parts)


def is_retryable_error(exc: Any) -> bool:
    code = (_error_code(exc) or "").lower()
    if code in {
        "insufficient_quota",
        "quota_exceeded",
        "billing_hard_limit_reached",
        "billing_not_active",
        "moderation_blocked",
        "image_generation_user_error",
        "invalid_request_error",
    }:
        return False
    status = _error_status(exc)
    if status in {408, 409, 429} or (status is not None and status >= 500):
        return True
    if code in {
        "rate_limit_exceeded",
        "internal_server_error",
        "service_unavailable",
        "timeout",
    }:
        return True
    name = exc.__class__.__name__.lower()
    return any(token in name for token in ("connection", "timeout", "ratelimit"))


def _retry_after(exc: Any, attempt: int) -> float:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if headers:
        value = headers.get("retry-after")
        try:
            return min(120.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            pass
    return min(60.0, (2 ** (attempt - 1)) + random.random())


def _call_with_heartbeat(operation: Any) -> Any:
    stopped = Event()
    started = time.monotonic()

    def report() -> None:
        while not stopped.wait(HEARTBEAT_SECONDS):
            elapsed = round(time.monotonic() - started)
            print(f"Waiting for image API response... {elapsed}s", file=sys.stderr)

    reporter = Thread(target=report, daemon=True)
    reporter.start()
    try:
        return operation()
    finally:
        stopped.set()
        reporter.join(timeout=1.0)


def call_with_retry(operation: Any, *, max_attempts: int) -> tuple[Any, int]:
    if not 1 <= max_attempts <= MAX_ATTEMPTS:
        raise UsageError(f"max-attempts must be between 1 and {MAX_ATTEMPTS}")
    for attempt in range(1, max_attempts + 1):
        try:
            return _call_with_heartbeat(operation), attempt
        except Exception as exc:
            if attempt == max_attempts or not is_retryable_error(exc):
                raise
            delay = _retry_after(exc, attempt)
            _warn(
                "transient API failure; retrying in "
                f"{delay:.1f}s ({attempt}/{max_attempts})"
            )
            time.sleep(delay)
    raise RuntimeError("unreachable")


async def async_call_with_retry(
    operation: Any, *, max_attempts: int
) -> tuple[Any, int]:
    if not 1 <= max_attempts <= MAX_ATTEMPTS:
        raise UsageError(f"max-attempts must be between 1 and {MAX_ATTEMPTS}")
    for attempt in range(1, max_attempts + 1):
        try:
            return await operation(), attempt
        except Exception as exc:
            if attempt == max_attempts or not is_retryable_error(exc):
                raise
            delay = _retry_after(exc, attempt)
            _warn(
                "transient API failure; retrying in "
                f"{delay:.1f}s ({attempt}/{max_attempts})"
            )
            await asyncio.sleep(delay)
    raise RuntimeError("unreachable")


def _create_client(api_key: str, base_url: Optional[str], timeout: float) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise UsageError(
            "OpenAI Python SDK is not installed; run this script with uv run"
        ) from exc
    kwargs: dict[str, Any] = {
        "api_key": api_key,
        "max_retries": 0,
        "timeout": timeout,
    }
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def _create_async_client(api_key: str, base_url: Optional[str], timeout: float) -> Any:
    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise UsageError(
            "OpenAI Python SDK is not installed; run this script with uv run"
        ) from exc
    kwargs: dict[str, Any] = {
        "api_key": api_key,
        "max_retries": 0,
        "timeout": timeout,
    }
    if base_url:
        kwargs["base_url"] = base_url
    return AsyncOpenAI(**kwargs)


def _sdk_common_payload(spec: dict[str, Any]) -> dict[str, Any]:
    payload = {
        key: spec[key]
        for key in (
            "prompt",
            "n",
            "size",
            "quality",
            "background",
            "output_format",
            "output_compression",
        )
        if spec.get(key) is not None
    }
    payload["model"] = spec.get("wire_model", spec["model"])
    if spec.get("command") == "generate":
        payload["moderation"] = spec["moderation"]
    if spec.get("stream"):
        payload["stream"] = True
        payload["partial_images"] = spec.get("partial_images", 0)
    return payload


def _make_metadata(
    *,
    spec: dict[str, Any],
    response: Any,
    output: Path,
    elapsed_seconds: float,
    attempts: int,
    partial_outputs: Optional[list[Path]] = None,
    derived_output: Optional[Path] = None,
) -> dict[str, Any]:
    request = {
        key: value
        for key, value in spec.items()
        if key not in {"endpoint", "command", "images", "image_roles", "mask"}
    }
    inputs = [
        {"index": index, "path": path, "role": role}
        for index, (path, role) in enumerate(
            zip(spec.get("images", []), spec.get("image_roles", []), strict=False),
            start=1,
        )
    ]
    return {
        "schema_version": 1,
        "command": spec["command"],
        "endpoint": spec["endpoint"],
        "request": request,
        "inputs": inputs,
        "mask": spec.get("mask"),
        "response": extract_response_metadata(response),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "attempts": attempts,
        "output": str(output),
        "partial_outputs": [str(path) for path in (partial_outputs or [])],
        "derived_output": str(derived_output) if derived_output else None,
        "created_at": _now_iso(),
    }


def _save_final_images(
    *,
    response: Any,
    spec: dict[str, Any],
    output_paths: list[Path],
    elapsed_seconds: float,
    attempts: int,
    force: bool,
    downscale_max_dim: Optional[int],
    downscale_suffix: str,
) -> list[Path]:
    items = list(getattr(response, "data", None) or [])
    if len(items) != len(output_paths):
        raise UsageError(
            f"API returned {len(items)} image(s); expected {len(output_paths)}"
        )
    written: list[Path] = []
    for item, path in zip(items, output_paths, strict=True):
        raw = decode_base64_image(getattr(item, "b64_json", None))
        if spec["background"] == "transparent":
            validate_transparent_image(raw)
        derived_path = None
        if downscale_max_dim is not None:
            derived_path = _downscale_path(path, downscale_suffix)
            derived = downscale_image(
                raw,
                max_dim=downscale_max_dim,
                output_format=spec["output_format"],
            )
            write_bytes(derived_path, derived, force=force)
        write_bytes(path, raw, force=force)
        metadata = _make_metadata(
            spec=spec,
            response=response,
            output=path,
            elapsed_seconds=elapsed_seconds,
            attempts=attempts,
            derived_output=derived_path,
        )
        write_json(_metadata_path(path), metadata, force=force)
        written.append(path)
    return written


def _stream_event_type(event: Any) -> str:
    if isinstance(event, dict):
        return str(event.get("type", ""))
    return str(getattr(event, "type", ""))


def _stream_event_value(event: Any, name: str, default: Any = None) -> Any:
    if isinstance(event, dict):
        return event.get(name, default)
    return getattr(event, name, default)


def _save_stream(
    *,
    stream: Any,
    spec: dict[str, Any],
    output: Path,
    started_at: float,
    attempts: int,
    force: bool,
    downscale_max_dim: Optional[int],
    downscale_suffix: str,
) -> list[Path]:
    partial_paths: list[Path] = []
    final_data: Optional[bytes] = None
    completed_event: Any = None
    for event in stream:
        event_type = _stream_event_type(event)
        if event_type in {"image_generation.partial_image", "image_edit.partial_image"}:
            index = int(
                _stream_event_value(event, "partial_image_index", len(partial_paths))
            )
            raw = decode_base64_image(_stream_event_value(event, "b64_json"))
            path = _partial_path(output, index)
            write_bytes(path, raw, force=force)
            partial_paths.append(path)
            print(f"Wrote partial image: {path}", file=sys.stderr)
        elif event_type in {"image_generation.completed", "image_edit.completed"}:
            final_data = decode_base64_image(_stream_event_value(event, "b64_json"))
            completed_event = event
    if final_data is None:
        raise UsageError("stream ended without a completed image event")
    if spec["background"] == "transparent":
        validate_transparent_image(final_data)
    derived_path = None
    if downscale_max_dim is not None:
        derived_path = _downscale_path(output, downscale_suffix)
        write_bytes(
            derived_path,
            downscale_image(
                final_data,
                max_dim=downscale_max_dim,
                output_format=spec["output_format"],
            ),
            force=force,
        )
    write_bytes(output, final_data, force=force)
    metadata = _make_metadata(
        spec=spec,
        response=completed_event,
        output=output,
        elapsed_seconds=time.monotonic() - started_at,
        attempts=attempts,
        partial_outputs=partial_paths,
        derived_output=derived_path,
    )
    write_json(_metadata_path(output), metadata, force=force)
    return [output]


def run_live_request(
    *,
    spec: dict[str, Any],
    out: Path,
    force: bool,
    max_attempts: int,
    timeout: float,
    downscale_max_dim: Optional[int] = None,
    downscale_suffix: str = "-web",
) -> list[Path]:
    api_key, base_url = get_api_settings(require_key=True)
    assert api_key is not None
    spec = resolve_provider_spec(spec, base_url)
    output_paths = build_output_paths(out, spec["output_format"], spec["n"])
    preflight_output_paths(
        output_paths,
        force=force,
        partial_images=spec["partial_images"] if spec["stream"] else 0,
        downscale_max_dim=downscale_max_dim,
        downscale_suffix=downscale_suffix,
    )
    client = _create_client(api_key, base_url, timeout)
    started = time.monotonic()
    payload = _sdk_common_payload(spec)
    if spec["command"] == "edit":

        def operation() -> Any:
            request = dict(payload)
            with ExitStack() as stack:
                request["image"] = [
                    stack.enter_context(Path(path).open("rb"))
                    for path in spec["images"]
                ]
                if spec.get("mask"):
                    request["mask"] = stack.enter_context(Path(spec["mask"]).open("rb"))
                return client.images.edit(**request)

    else:

        def operation() -> Any:
            return client.images.generate(**payload)

    response, attempts = call_with_retry(operation, max_attempts=max_attempts)
    if spec["stream"]:
        return _save_stream(
            stream=response,
            spec=spec,
            output=output_paths[0],
            started_at=started,
            attempts=attempts,
            force=force,
            downscale_max_dim=downscale_max_dim,
            downscale_suffix=downscale_suffix,
        )
    return _save_final_images(
        response=response,
        spec=spec,
        output_paths=output_paths,
        elapsed_seconds=time.monotonic() - started,
        attempts=attempts,
        force=force,
        downscale_max_dim=downscale_max_dim,
        downscale_suffix=downscale_suffix,
    )


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return (slug[:48] or "image").strip("-") or "image"


def _safe_batch_output(out_dir: Path, value: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise UsageError("batch out must be a relative path under --out-dir")
    return out_dir / relative


def _batch_string(
    data: dict[str, Any], key: str, default: Optional[str], line_number: int
) -> Optional[str]:
    value = data.get(key, default)
    if value is None:
        return None
    if not isinstance(value, str):
        raise UsageError(f"line {line_number} field {key!r} must be a string")
    return value


def _batch_integer(
    data: dict[str, Any], key: str, default: Optional[int], line_number: int
) -> Optional[int]:
    value = data.get(key, default)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise UsageError(f"line {line_number} field {key!r} must be an integer")
    return value


def load_batch_jobs(source: Path, out_dir: Path) -> list[dict[str, Any]]:
    if not source.is_file():
        raise UsageError(f"batch input does not exist: {source}")
    jobs: list[dict[str, Any]] = []
    artifacts: set[Path] = set()
    for line_number, raw in enumerate(
        source.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise UsageError(f"invalid JSON on line {line_number}: {exc.msg}") from exc
        if isinstance(value, str):
            data: dict[str, Any] = {"prompt": value}
        elif isinstance(value, dict):
            data = dict(value)
        else:
            raise UsageError(f"line {line_number} must be a JSON string or object")
        allowed_keys = {
            "prompt",
            "model",
            "n",
            "size",
            "quality",
            "background",
            "output_format",
            "output_compression",
            "moderation",
            "out",
        }
        unknown = sorted(set(data) - allowed_keys)
        if unknown:
            raise UsageError(
                f"line {line_number} contains unknown field(s): {', '.join(unknown)}"
            )
        prompt = data.get("prompt")
        if not isinstance(prompt, str):
            raise UsageError(f"line {line_number} requires a string prompt")
        model = _batch_string(data, "model", None, line_number)
        size = _batch_string(data, "size", "auto", line_number)
        quality = _batch_string(data, "quality", "auto", line_number)
        background = _batch_string(data, "background", "auto", line_number)
        output_format_value = _batch_string(data, "output_format", "png", line_number)
        moderation = _batch_string(data, "moderation", "auto", line_number)
        output_name = _batch_string(data, "out", None, line_number)
        n = _batch_integer(data, "n", 1, line_number)
        output_compression = _batch_integer(
            data, "output_compression", None, line_number
        )
        assert size is not None
        assert quality is not None
        assert background is not None
        assert output_format_value is not None
        assert moderation is not None
        assert n is not None
        output_format = normalize_output_format(output_format_value)
        default_name = f"{line_number:04d}-{_slugify(prompt)}.{output_format}"
        output = _safe_batch_output(out_dir, output_name or default_name)
        spec = build_generate_spec(
            prompt=prompt,
            model=model,
            n=n,
            size=size,
            quality=quality,
            background=background,
            output_format=output_format,
            output_compression=output_compression,
            moderation=moderation,
        )
        job_outputs = build_output_paths(output, output_format, spec["n"])
        job_artifacts = {
            artifact
            for image_path in job_outputs
            for artifact in (image_path, _metadata_path(image_path))
        }
        duplicates = artifacts.intersection(job_artifacts)
        if duplicates:
            raise UsageError(
                "duplicate batch artifact path: "
                + ", ".join(str(path) for path in duplicates)
            )
        artifacts.update(job_artifacts)
        jobs.append({**spec, "out": str(output), "line": line_number})
        if len(jobs) > MAX_BATCH_JOBS:
            raise UsageError(f"batch accepts at most {MAX_BATCH_JOBS} jobs")
    if not jobs:
        raise UsageError("batch input contains no jobs")
    return jobs


async def _run_batch_job(
    *,
    client: Any,
    semaphore: asyncio.Semaphore,
    job: dict[str, Any],
    force: bool,
    max_attempts: int,
) -> dict[str, Any]:
    output_paths = build_output_paths(Path(job["out"]), job["output_format"], job["n"])
    started = time.monotonic()
    payload = _sdk_common_payload(job)

    async def operation() -> Any:
        async with semaphore:
            return await client.images.generate(**payload)

    try:
        response, attempts = await async_call_with_retry(
            operation, max_attempts=max_attempts
        )
        written = _save_final_images(
            response=response,
            spec=job,
            output_paths=output_paths,
            elapsed_seconds=time.monotonic() - started,
            attempts=attempts,
            force=force,
            downscale_max_dim=None,
            downscale_suffix="-web",
        )
        return {
            "line": job["line"],
            "status": "ok",
            "outputs": [str(p) for p in written],
        }
    except Exception as exc:
        return {
            "line": job["line"],
            "status": "failed",
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }


async def run_batch(
    *,
    jobs: list[dict[str, Any]],
    force: bool,
    concurrency: int,
    max_attempts: int,
    timeout: float,
    fail_fast: bool,
) -> list[dict[str, Any]]:
    if not 1 <= concurrency <= MAX_CONCURRENCY:
        raise UsageError(f"concurrency must be between 1 and {MAX_CONCURRENCY}")
    api_key, base_url = get_api_settings(require_key=True)
    assert api_key is not None
    jobs = [resolve_provider_spec(job, base_url) for job in jobs]
    all_paths: list[Path] = []
    for job in jobs:
        all_paths.extend(
            build_output_paths(Path(job["out"]), job["output_format"], job["n"])
        )
    preflight_output_paths(all_paths, force=force)
    client = _create_async_client(api_key, base_url, timeout)
    semaphore = asyncio.Semaphore(concurrency)
    results: list[dict[str, Any]] = []
    try:
        if fail_fast:
            for job in jobs:
                result = await _run_batch_job(
                    client=client,
                    semaphore=semaphore,
                    job=job,
                    force=force,
                    max_attempts=max_attempts,
                )
                results.append(result)
                print(
                    f"Batch progress: {len(results)}/{len(jobs)} "
                    f"({result['status']})",
                    file=sys.stderr,
                )
                if result["status"] == "failed":
                    break
        else:
            tasks = [
                asyncio.create_task(
                    _run_batch_job(
                        client=client,
                        semaphore=semaphore,
                        job=job,
                        force=force,
                        max_attempts=max_attempts,
                    )
                )
                for job in jobs
            ]
            for completed in asyncio.as_completed(tasks):
                result = await completed
                results.append(result)
                print(
                    f"Batch progress: {len(results)}/{len(jobs)} "
                    f"({result['status']})",
                    file=sys.stderr,
                )
            results.sort(key=lambda item: item["line"])
    finally:
        await client.close()
    return results


def _read_prompt(prompt: Optional[str], prompt_file: Optional[str]) -> str:
    if bool(prompt) == bool(prompt_file):
        raise UsageError("provide exactly one of --prompt or --prompt-file")
    if prompt_file:
        path = Path(prompt_file)
        if not path.is_file():
            raise UsageError(f"prompt file does not exist: {path}")
        prompt = path.read_text(encoding="utf-8")
    assert prompt is not None
    return validate_prompt(prompt)


def validate_runtime_controls(
    *,
    max_attempts: int,
    timeout: float,
    concurrency: Optional[int] = None,
    downscale_max_dim: Optional[int] = None,
) -> None:
    if not 1 <= max_attempts <= MAX_ATTEMPTS:
        raise UsageError(f"max-attempts must be between 1 and {MAX_ATTEMPTS}")
    if timeout <= 0:
        raise UsageError("timeout must be positive")
    if concurrency is not None and not 1 <= concurrency <= MAX_CONCURRENCY:
        raise UsageError(f"concurrency must be between 1 and {MAX_CONCURRENCY}")
    if downscale_max_dim is not None and downscale_max_dim <= 0:
        raise UsageError("downscale-max-dim must be positive")


def _shared_request_args(
    parser: argparse.ArgumentParser, *, include_moderation: bool
) -> None:
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="flare, sunburst, or an exact GPT Image 2.5 alias/snapshot",
    )
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--size", default="auto")
    parser.add_argument("--quality", default="auto")
    parser.add_argument(
        "--background", choices=sorted(ALLOWED_BACKGROUNDS), default="auto"
    )
    parser.add_argument(
        "--output-format", choices=["png", "jpeg", "jpg", "webp"], default="png"
    )
    parser.add_argument("--output-compression", type=int)
    if include_moderation:
        parser.add_argument(
            "--moderation", choices=sorted(ALLOWED_MODERATION), default="auto"
        )
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--partial-images", type=int, default=0)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--downscale-max-dim", type=int)
    parser.add_argument("--downscale-suffix", default="-web")


def _spec_from_args(args: argparse.Namespace) -> dict[str, Any]:
    prompt = _read_prompt(args.prompt, args.prompt_file)
    common = {
        "prompt": prompt,
        "model": args.model,
        "n": args.n,
        "size": args.size,
        "quality": args.quality,
        "background": args.background,
        "output_format": args.output_format,
        "output_compression": args.output_compression,
        "stream": args.stream,
        "partial_images": args.partial_images,
    }
    if args.command == "edit":
        return build_edit_spec(
            **common,
            images=args.image,
            roles=args.image_role,
            mask=args.mask,
        )
    common["moderation"] = args.moderation
    return build_generate_spec(**common)


def _dry_run_document(
    spec: dict[str, Any], out: Path, base_url: Optional[str]
) -> dict[str, Any]:
    spec = resolve_provider_spec(spec, base_url)
    outputs = build_output_paths(out, spec["output_format"], spec["n"])
    return {
        **spec,
        "outputs": [str(path) for path in outputs],
        "metadata": [str(_metadata_path(path)) for path in outputs],
        "partial_outputs": [
            str(_partial_path(outputs[0], index))
            for index in range(spec["partial_images"] if spec["stream"] else 0)
        ],
        "network_call": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate and edit images with OpenAI GPT Image 2.5 via the Image API."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="generate a new image")
    _shared_request_args(generate, include_moderation=True)

    edit = subparsers.add_parser("edit", help="edit using one to sixteen input images")
    _shared_request_args(edit, include_moderation=False)
    edit.add_argument("--image", action="append", required=True, type=Path)
    edit.add_argument("--image-role", action="append")
    edit.add_argument("--mask", type=Path)

    batch = subparsers.add_parser(
        "generate-batch", help="generate distinct jobs from a JSONL file"
    )
    batch.add_argument("--input", required=True, type=Path)
    batch.add_argument("--out-dir", type=Path, default=DEFAULT_BATCH_DIR)
    batch.add_argument("--concurrency", type=int, default=5)
    batch.add_argument("--max-attempts", type=int, default=3)
    batch.add_argument("--timeout", type=float, default=300.0)
    batch.add_argument("--fail-fast", action="store_true")
    batch.add_argument("--force", action="store_true")
    batch.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    _load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "generate-batch":
            validate_runtime_controls(
                max_attempts=args.max_attempts,
                timeout=args.timeout,
                concurrency=args.concurrency,
            )
            jobs = load_batch_jobs(args.input, args.out_dir)
            if args.dry_run:
                _, base_url = get_api_settings(require_key=False)
                jobs = [resolve_provider_spec(job, base_url) for job in jobs]
                print(
                    json.dumps(
                        {
                            "command": "generate-batch",
                            "jobs": jobs,
                            "network_call": False,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            results = asyncio.run(
                run_batch(
                    jobs=jobs,
                    force=args.force,
                    concurrency=args.concurrency,
                    max_attempts=args.max_attempts,
                    timeout=args.timeout,
                    fail_fast=args.fail_fast,
                )
            )
            succeeded = sum(item["status"] == "ok" for item in results)
            print(
                json.dumps(
                    {
                        "summary": {
                            "total": len(results),
                            "succeeded": succeeded,
                            "failed": len(results) - succeeded,
                        },
                        "results": results,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1 if any(item["status"] == "failed" for item in results) else 0

        validate_runtime_controls(
            max_attempts=args.max_attempts,
            timeout=args.timeout,
            downscale_max_dim=args.downscale_max_dim,
        )
        spec = _spec_from_args(args)
        if args.dry_run:
            _, base_url = get_api_settings(require_key=False)
            print(
                json.dumps(
                    _dry_run_document(spec, args.out, base_url),
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        paths = run_live_request(
            spec=spec,
            out=args.out,
            force=args.force,
            max_attempts=args.max_attempts,
            timeout=args.timeout,
            downscale_max_dim=args.downscale_max_dim,
            downscale_suffix=args.downscale_suffix,
        )
        for path in paths:
            print(path)
        return 0
    except UsageError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        code = _error_code(exc)
        status = _error_status(exc)
        detail = f" status={status}" if status is not None else ""
        if code:
            detail += f" code={code}"
        moderation = _moderation_detail(exc)
        if moderation:
            detail += f" {moderation}"
        print(f"API error:{detail} {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
