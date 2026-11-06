"""Bundled Ark request boundary adapted from seedream-image-gen.

The owning request, retry and download behavior is reused here so the skill
can be installed without a neighboring skill directory.
"""
from __future__ import annotations
import asyncio
import base64
import getpass
import os
import sys
import time
from pathlib import Path
from typing import Any, NamedTuple, Optional
import httpx

MODEL_PRO = "doubao-seedream-5-0-pro-260628"
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
MAX_RETRIES = 8
RETRY_BACKOFF = (2.0, 4.0, 8.0, 16.0, 30.0, 30.0, 30.0, 30.0)
MAX_REFERENCE_BYTES = 30 * 1024 * 1024
CAPS = {"optimize_modes": {"standard", "fast"}, "max_refs": 10}


class ImageOutput(NamedTuple):
    content: bytes
    size: Optional[str] = None
    output_format: Optional[str] = None
    z_index: Optional[int] = None
    bounding_box: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    description: Optional[str] = None


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


def _is_url(path: str) -> bool:
    return path.startswith(("http://", "https://"))


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
            request = client.build_request("GET", url, timeout=float(timeout))
            origin = (request.url.scheme, request.url.host, request.url.port)
            api_origin = (client.base_url.scheme, client.base_url.host, client.base_url.port)
            if origin != api_origin:
                request.headers.pop("Authorization", None)
            response = await client.send(request)
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

    raise last_error
