#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["httpx>=0.27,<1", "pillow>=10,<13"]
# ///
"""One fixed avatar animation recipe. No imports from other skills."""

import argparse
import base64
import fcntl
import hashlib
import ipaddress
import io
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
from urllib.parse import urlsplit

import httpx
from PIL import Image


PROMPT = (
    "角色非常灵动的挥挥手，傻傻的转一圈，然后凑到镜头上，再回去。\n"
    "整个过程种，镜头不允许有任何的 zoom 或者 move 等动作，镜头固定。"
    "角色一直都保持“运动”而非“静止”状态。"
)
PRESET = {
    "model": "doubao-seedance-2-5-260628",
    "duration": 10,
    "resolution": "720p",
    "ratio": "adaptive",
    "generate_audio": False,
    "watermark": False,
}
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
TERMINAL_FAILURES = {"failed", "cancelled", "expired"}
LOOPBACK_NAMES = {"localhost"}


class RunError(Exception):
    pass


def load_environment():
    path = Path.cwd() / ".env"
    if path.is_file():
        for line in path.read_text().splitlines():
            line = line.strip().removeprefix("export ")
            name, sep, value = line.partition("=")
            name = name.strip()
            if (
                sep
                and name in {"ARK_API_KEY", "ARK_BASE_URL"}
                and name not in os.environ
            ):
                parts = shlex.split(value, comments=True)
                if len(parts) == 1:
                    os.environ[name] = parts[0]


def safe_error(error):
    message = str(error)
    key = os.environ.get("ARK_API_KEY", "")
    return message.replace(key, "[redacted]") if key else message


def save_manifest(out, manifest):
    manifest["updated_at"] = time.time()
    temp = out / "manifest.json.tmp"
    with temp.open("w") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(out / "manifest.json")


def image_input(path):
    if not path.is_file():
        raise RunError("Image not found: " + str(path))
    size = path.stat().st_size
    # The same base64 image occurs twice; keep the whole body below 60 MiB.
    if size > 30 * 1024 * 1024 or 2 * ((size + 2) // 3 * 4) + 8192 > 60 * 1024 * 1024:
        raise RunError("Image is too large for two inline endpoint references.")
    data = path.read_bytes()
    try:
        with Image.open(io.BytesIO(data)) as image:
            fmt, width, height = image.format, *image.size
            if fmt not in {"PNG", "JPEG", "WEBP"} or getattr(image, "n_frames", 1) != 1:
                raise RunError("Use one still PNG, JPEG, or WebP image.")
            if not (
                300 <= width <= 6000
                and 300 <= height <= 6000
                and 0.4 <= width / height <= 2.5
            ):
                raise RunError(
                    "Image sides must be 300–6000px with width/height between 0.4 and 2.5."
                )
            image.load()
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        raise RunError("Cannot decode the input image.") from exc
    meta = {
        "sha256": hashlib.sha256(data).hexdigest(),
        "width": width,
        "height": height,
        "format": fmt,
        "bytes": len(data),
    }
    return data, meta


def payload_for(data, meta):
    mime = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}[
        meta["format"]
    ]
    url = "data:" + mime + ";base64," + base64.b64encode(data).decode("ascii")
    return {
        **PRESET,
        "content": [
            {"type": "text", "text": PROMPT},
            *[
                {"type": "image_url", "image_url": {"url": url}, "role": role}
                for role in ("first_frame", "last_frame")
            ],
        ],
    }


def check_tools():
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            raise RunError(tool + " is required before submitting a paid task.")


def run_media(command):
    try:
        result = subprocess.run(
            command, check=True, capture_output=True, text=True, timeout=180
        )
        return result.stdout
    except subprocess.CalledProcessError as exc:
        raise RunError("Media command failed: " + exc.stderr[-1200:]) from exc
    except subprocess.TimeoutExpired as exc:
        raise RunError(
            "Media command timed out; resume the same run to retry local export."
        ) from exc


def probe_video(path):
    info = json.loads(
        run_media(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=codec_type,codec_name,width,height",
                "-of",
                "json",
                str(path),
            ]
        )
    )
    video = next(
        (s for s in info.get("streams", []) if s.get("codec_type") == "video"), None
    )
    duration = float(info.get("format", {}).get("duration", 0))
    if not video or duration <= 0 or not video.get("width") or not video.get("height"):
        raise RunError("Downloaded media has no usable video stream.")
    return {
        "width": video["width"],
        "height": video["height"],
        "codec": video["codec_name"],
        "duration": duration,
    }


def file_info(path):
    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def require_auth():
    key = os.environ.get("ARK_API_KEY", "").strip()
    if not key:
        raise RunError("Set ARK_API_KEY in the environment or working directory .env.")
    return {"Authorization": "Bearer " + key}


def api_base_url():
    base = os.environ.get("ARK_BASE_URL", BASE_URL).strip().rstrip("/")
    try:
        parsed = urlsplit(base)
        host = parsed.hostname
        # Accessing .port also validates malformed port numbers.
        _ = parsed.port
    except ValueError as exc:
        raise RunError("ARK_BASE_URL must be a valid HTTPS URL.") from exc
    loopback = host in LOOPBACK_NAMES
    if host and not loopback:
        try:
            loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            pass
    if not host or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise RunError("ARK_BASE_URL must be an HTTPS URL without credentials, query, or fragment.")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
        raise RunError("ARK_BASE_URL must use HTTPS; HTTP is allowed only for loopback tests.")
    return base


def http_error(response):
    # Report only a bounded provider error, never the request body or headers.
    try:
        error = response.json().get("error", {})
        detail = str(error.get("code", "")) + ": " + str(error.get("message", ""))
    except (ValueError, AttributeError):
        detail = "Non-JSON provider error"
    return RunError(
        safe_error("HTTP " + str(response.status_code) + " " + detail[:600])
    )


def submit(client, base, headers, payload, out, manifest):
    manifest["phase"] = "submitting"
    save_manifest(out, manifest)
    try:
        # A transport timeout/5xx may follow successful creation: NEVER retry POST.
        response = client.post(
            base + "/contents/generations/tasks", headers=headers, json=payload
        )
        if not response.is_success:
            raise http_error(response)
        task_id = response.json().get("id")
        if not isinstance(task_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", task_id):
            raise RunError("Submission response did not contain a usable task ID.")
        manifest.update(task_id=task_id, phase="submitted")
        save_manifest(out, manifest)
    except BaseException:
        # If the ID was already obtained, retain it even if recording was interrupted.
        if not manifest.get("task_id"):
            manifest["phase"] = "submission_unknown"
        save_manifest(out, manifest)
        raise
    print("Task ID: " + task_id, flush=True)


def poll(client, base, headers, out, manifest, interval, max_wait):
    deadline = time.monotonic() + max_wait
    last_status = None
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RunError(
                "Polling timed out. The task is retained; use --resume with the same --out."
            )
        try:
            response = client.get(
                base + "/contents/generations/tasks/" + manifest["task_id"],
                headers=headers,
                timeout=min(60, remaining),
            )
            if response.status_code in {408, 429} or response.status_code >= 500:
                time.sleep(min(interval, max(0, deadline - time.monotonic())))
                continue
            if not response.is_success:
                raise http_error(response)
            result = response.json()
        except (httpx.TransportError, ValueError):
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
            continue
        status = result.get("status")
        if status not in {"queued", "running", "succeeded", *TERMINAL_FAILURES}:
            raise RunError("Unexpected task status; resume later without resubmitting.")
        manifest.update(status=status, phase="polling", usage=result.get("usage"))
        if result.get("error"):
            manifest["error"] = safe_error(
                json.dumps(result["error"], ensure_ascii=False)
            )[:1200]
        save_manifest(out, manifest)
        if status != last_status:
            print("Status: " + status, flush=True)
            last_status = status
        if status in TERMINAL_FAILURES:
            raise RunError(
                "Task " + status + ": " + manifest.get("error", "no error detail")
            )
        if status == "succeeded":
            url = result.get("content", {}).get("video_url")
            if not isinstance(url, str) or not url.startswith(("https://", "http://")):
                raise RunError("Succeeded task has no usable video URL; resume later.")
            return url
        time.sleep(min(interval, max(0, deadline - time.monotonic())))


def download(client, url, out):
    temp = out / "source.mp4.part"
    for attempt in range(3):
        try:
            # This client has NO default Authorization; signed downloads never get the Ark key.
            with client.stream(
                "GET", url, follow_redirects=True, timeout=120
            ) as response:
                response.raise_for_status()
                with temp.open("wb") as handle:
                    for chunk in response.iter_bytes():
                        handle.write(chunk)
            probe_video(temp)
            temp.replace(out / "source.mp4")
            return
        except (httpx.HTTPError, RunError):
            temp.unlink(missing_ok=True)
            if attempt == 2:
                raise RunError(
                    "Video download failed; use --resume to refresh its URL and retry."
                )
            time.sleep(2**attempt)


def export_media(out, manifest):
    source = out / "source.mp4"
    source_info = probe_video(source)
    mp4, gif = out / "avatar.mp4", out / "avatar.gif"
    if not mp4.exists():
        temp = out / "avatar.tmp.mp4"
        run_media(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(source),
                "-an",
                "-c:v",
                "libx264",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(temp),
            ]
        )
        probe_video(temp)
        temp.replace(mp4)
    mp4_info = probe_video(mp4)
    if not gif.exists():
        temp = out / "avatar.tmp.gif"
        run_media(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(source),
                "-filter_complex",
                "[0:v]fps=15,scale=480:480:force_original_aspect_ratio=decrease:flags=lanczos,"
                "split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a",
                "-loop",
                "0",
                str(temp),
            ]
        )
        temp.replace(gif)
    with Image.open(gif) as image:
        if image.format != "GIF" or image.n_frames < 2 or image.info.get("loop") != 0:
            raise RunError("GIF export is not a repeating animation.")
        gif_info = {
            "width": image.width,
            "height": image.height,
            "frames": image.n_frames,
            "loop": image.info["loop"],
            "duration_ms": 0,
        }
        for frame in range(image.n_frames):
            image.seek(frame)
            gif_info["duration_ms"] += image.info.get("duration", 0)
    manifest.update(
        phase="complete",
        files=[
            {**file_info(source), **source_info},
            {**file_info(mp4), **mp4_info},
            {**file_info(gif), **gif_info},
        ],
        visual_qa="pending: inspect actions, identity, camera, cropping, and loop seam",
    )
    save_manifest(out, manifest)
    print("MP4: " + str(mp4) + "\nGIF: " + str(gif), flush=True)


def execute(args):
    out = args.out.expanduser().resolve()
    if args.dry_run:
        if args.resume or args.task_id or not args.image:
            raise RunError("--dry-run requires --image and cannot resume a task.")
        _, meta = image_input(args.image.expanduser().resolve())
        print(
            json.dumps(
                {
                    "preset": PRESET,
                    "prompt": PROMPT,
                    "image": meta,
                    "first_frame_equals_last_frame": True,
                    "out": str(out),
                    "network_calls": 0,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    base = api_base_url()
    check_tools()
    if args.resume and not out.is_dir():
        raise RunError("No saved run at --out; --resume never creates a task.")
    out.mkdir(parents=True, exist_ok=True)
    with (out / ".run.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RunError("This run is already active in another process.") from exc
        manifest_path = out / "manifest.json"
        if args.resume:
            if args.image:
                raise RunError(
                    "--resume uses the saved input; do not pass a new --image."
                )
            if not manifest_path.is_file():
                raise RunError(
                    "No manifest to resume. Do not create a replacement task blindly."
                )
            manifest = json.loads(manifest_path.read_text())
            if manifest.get("schema_version") != 1:
                raise RunError("Unsupported run manifest version.")
            if args.task_id:
                if manifest.get("task_id") not in (None, args.task_id):
                    raise RunError("Cannot replace this run's saved task ID.")
                manifest.update(task_id=args.task_id, phase="recovered")
                save_manifest(out, manifest)
            if not manifest.get("task_id"):
                raise RunError(
                    "Submission outcome is unknown. Reconcile the provider record, then use --resume --task-id."
                )
            if manifest.get("status") in TERMINAL_FAILURES:
                raise RunError(
                    "Saved task is terminal: "
                    + manifest["status"]
                    + "; no new task was created."
                )
            if (out / "source.mp4").exists():
                export_media(out, manifest)
                return
            if manifest.get("api_base") != base:
                raise RunError(
                    "ARK_BASE_URL differs from the saved run. Restore the original endpoint before resuming."
                )
        else:
            if args.task_id or not args.image:
                raise RunError(
                    "A new run requires --image; --task-id is only for --resume."
                )
            if any(p.name != ".run.lock" for p in out.iterdir()):
                raise RunError(
                    "Output directory is not empty. Use --resume for an existing run."
                )
            headers = require_auth()
            data, meta = image_input(args.image.expanduser().resolve())
            suffix = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}[meta["format"]]
            (out / ("input" + suffix)).write_bytes(data)
            (out / "prompt.txt").write_text(PROMPT, encoding="utf-8")
            manifest = {
                "schema_version": 1,
                "phase": "prepared",
                "task_id": None,
                "api_base": base,
                "preset": PRESET,
                "prompt": PROMPT,
                "image": meta,
                "created_at": time.time(),
            }
            save_manifest(out, manifest)
        headers = require_auth()
        with httpx.Client(timeout=60, follow_redirects=False) as client:
            if not args.resume:
                submit(client, base, headers, payload_for(data, meta), out, manifest)
            url = poll(
                client, base, headers, out, manifest, args.poll_interval, args.max_wait
            )
            download(client, url, out)
        manifest["phase"] = "downloaded"
        save_manifest(out, manifest)
        export_media(out, manifest)


def main():
    parser = argparse.ArgumentParser(
        description="Animate one avatar with a fixed 10-second Seedance recipe."
    )
    parser.add_argument("--image", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--task-id", help="Attach a reconciled existing task ID; never submit."
    )
    parser.add_argument("--poll-interval", type=float, default=20)
    parser.add_argument("--max-wait", type=float, default=1800)
    args = parser.parse_args()
    if not all(
        math.isfinite(value) and value > 0
        for value in (args.poll_interval, args.max_wait)
    ):
        parser.error("Polling interval and maximum wait must be finite and positive.")
    if args.task_id and not re.fullmatch(r"[A-Za-z0-9_-]+", args.task_id):
        parser.error("Invalid task ID.")
    try:
        load_environment()
        execute(args)
    except KeyboardInterrupt:
        print(
            "Interrupted. Keep the output directory and resume; do not resubmit.",
            file=sys.stderr,
        )
        return 130
    except (RunError, OSError, ValueError, httpx.HTTPError) as exc:
        print("Error: " + safe_error(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
