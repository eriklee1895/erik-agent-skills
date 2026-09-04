#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests>=2.32",
#   "mutagen>=1.47",
#   "python-dotenv>=1.0",
# ]
# ///
"""Volcengine Doubao ASR 2.0 standard file transcription and orchestration."""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

from subtitle import (
    DEFAULT_MAX_CUE_CHARS,
    DEFAULT_MAX_CUE_DURATION_S,
    default_output_stem,
    load_tts_meta,
    normalize_result,
    resolve_output_path,
    write_outputs,
)

try:
    import mutagen
except ImportError:
    mutagen = None  # type: ignore[assignment]

API_BASE = "https://openspeech.bytedance.com"
SUBMIT_ENDPOINT = f"{API_BASE}/api/v3/auc/bigmodel/submit"
QUERY_ENDPOINT = f"{API_BASE}/api/v3/auc/bigmodel/query"
RESOURCE_ID = "volc.seedasr.auc"
MODEL_VERSION = "Doubao ASR 2.0"

STANDARD_MAX_DURATION_S = 5 * 3600
STANDARD_MAX_BYTES = 512 * 1024 * 1024
TRANSCODE_OVER_BYTES = 80 * 1024 * 1024
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0
RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}
STATUS_SUCCESS = "20000000"
STATUS_EMPTY = {"20000003", "45000002"}
STATUS_PENDING = {"20000001", "20000002"}

VIDEO_EXTS = {
    ".mp4", ".mov", ".mkv", ".avi", ".flv", ".webm", ".ts", ".m4v", ".wmv", ".3gp"
}
NATIVE_AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".raw"}
AUDIO_EXTS = VIDEO_EXTS | NATIVE_AUDIO_EXTS | {
    ".m4a", ".aac", ".flac", ".opus", ".wma", ".spx", ".amr", ".pcm"
}


def die(message: str, code: int = 1) -> None:
    print(json.dumps({"error": message}, ensure_ascii=False), file=sys.stderr)
    raise SystemExit(code)


def load_api_key() -> str:
    key = os.environ.get("VOLC_SPEECH_API_KEY", "").strip()
    if key:
        return key
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env)
        key = os.environ.get("VOLC_SPEECH_API_KEY", "").strip()
        if key:
            return key
    user_env = Path.home() / ".volcengine.env"
    if user_env.exists():
        load_dotenv(user_env)
        key = os.environ.get("VOLC_SPEECH_API_KEY", "").strip()
        if key:
            return key
    die(
        "VOLC_SPEECH_API_KEY not found. Set it via environment, .env, "
        "or ~/.volcengine.env."
    )


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def probe_duration_s(path: Path) -> float:
    """Probe with ffprobe when available, then fall back to mutagen."""
    if shutil.which("ffprobe"):
        try:
            proc = subprocess.run(
                [
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", str(path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.returncode == 0:
                return float(proc.stdout.strip())
        except (subprocess.TimeoutExpired, ValueError):
            pass
    if mutagen is not None:
        try:
            audio = mutagen.File(str(path))
            if audio is not None and audio.info is not None and audio.info.length:
                return float(audio.info.length)
        except Exception:
            pass
    return 0.0


def build_ffmpeg_cmd(source: Path, destination: Path) -> list[str]:
    input_options: list[str] = []
    if source.suffix.lower() in {".raw", ".pcm"}:
        # The standard API's raw default is signed little-endian 16-bit,
        # 16 kHz, mono PCM; headerless input must be described before -i.
        input_options = ["-f", "s16le", "-ar", "16000", "-ac", "1"]
    return [
        "ffmpeg", "-y", *input_options, "-i", str(source), "-vn",
        "-af", "aresample=async=1:first_pts=0",
        "-ac", "1", "-ar", "16000", "-b:a", "64k", "-f", "mp3", str(destination),
    ]


def ensure_has_audio(path: Path) -> None:
    if not shutil.which("ffprobe"):
        return
    try:
        proc = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
                "-of", "json", str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return
    if proc.returncode != 0:
        return
    try:
        streams = json.loads(proc.stdout or "{}").get("streams", [])
    except json.JSONDecodeError:
        return
    if streams and not any(stream.get("codec_type") == "audio" for stream in streams):
        die(f"File has no audio track: {path.name}")


def ffmpeg_to_mp3(source: Path, destination: Path) -> None:
    try:
        proc = subprocess.run(
            build_ffmpeg_cmd(source, destination), capture_output=True, text=True, timeout=600
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ffmpeg timed out after 600s") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed (exit {proc.returncode}): {(proc.stderr or '')[-500:]}")


def standard_limit_reason(path: Path) -> Optional[str]:
    size = path.stat().st_size
    if size > STANDARD_MAX_BYTES:
        return f"audio is {size / 1024 / 1024:.0f}MB, above the 512MB standard limit"
    duration = probe_duration_s(path)
    if duration > STANDARD_MAX_DURATION_S:
        return f"audio is {duration / 3600:.2f}h, above the 5h standard limit"
    return None


def prepare_local_media(
    path: Path, *, keep_extracted: bool = False
) -> tuple[Path, Optional[Path]]:
    extension = path.suffix.lower()
    if extension not in AUDIO_EXTS:
        die(f"Unsupported file type '{extension}'. Supported: {sorted(AUDIO_EXTS)}")
    initial_limit = standard_limit_reason(path)
    if initial_limit and "5h" in initial_limit:
        die(initial_limit)

    is_video = extension in VIDEO_EXTS
    if is_video:
        ensure_has_audio(path)
    needs_transcode = (
        is_video or extension not in NATIVE_AUDIO_EXTS or path.stat().st_size > TRANSCODE_OVER_BYTES
    )
    if not needs_transcode:
        return path, None
    if not shutil.which("ffmpeg"):
        die("ffmpeg is required to extract or transcode this input")

    if keep_extracted:
        output = path.with_name(f"{path.stem}.asr-16k-mono.mp3")
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.stem}.asr-", suffix=".mp3", dir=path.parent
        )
        os.close(descriptor)
        temporary_output = Path(temporary_name)
        try:
            ffmpeg_to_mp3(path, temporary_output)
            os.replace(temporary_output, output)
        except Exception as exc:
            temporary_output.unlink(missing_ok=True)
            die(str(exc))
        return output, None
    descriptor, name = tempfile.mkstemp(prefix="asr-", suffix=".mp3")
    os.close(descriptor)
    output = Path(name)
    try:
        ffmpeg_to_mp3(path, output)
    except Exception as exc:
        output.unlink(missing_ok=True)
        die(str(exc))
    return output, output


def build_request_body(
    *,
    audio_data_b64: Optional[str] = None,
    audio_url: Optional[str] = None,
    language: Optional[str] = None,
    audio_format: Optional[str] = None,
    send_format: bool = True,
    diarize: bool = False,
    meeting: bool = False,
    hotwords: Optional[list[str]] = None,
    context: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    del send_format  # Kept for import compatibility; standard mode always sends format.
    audio: dict[str, Any] = {}
    if audio_url:
        audio["url"] = audio_url
    if audio_data_b64 is not None:
        audio["data"] = audio_data_b64
    if audio_format:
        audio["format"] = audio_format
    if language:
        audio["language"] = language

    request: dict[str, Any] = {
        "model_name": "bigmodel",
        "enable_itn": True,
        "enable_punc": True,
        "enable_ddc": False,
        "show_utterances": True,
    }
    if diarize or meeting:
        request["enable_speaker_info"] = True
        request["ssd_version"] = "300" if meeting else "200"
    context_payload = merge_context(context, hotwords)
    if context_payload is not None:
        request["corpus"] = {
            "context": json.dumps(context_payload, ensure_ascii=False, separators=(",", ":"))
        }
    return {"audio": audio, "request": request}


def merge_context(
    context: Optional[dict[str, Any]], hotwords: Optional[list[str]]
) -> Optional[dict[str, Any]]:
    """Merge a full context object with the CLI hotword shortcut."""
    if context is None and not hotwords:
        return None
    if context is not None and not isinstance(context, dict):
        raise ValueError("context must be a JSON object")
    payload = dict(context or {})
    existing = payload.get("hotwords", [])
    if not isinstance(existing, list):
        raise ValueError("context.hotwords must be a JSON array")

    merged: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in existing:
        if not isinstance(item, dict) or not isinstance(item.get("word"), str):
            raise ValueError("each context.hotwords item must contain a string 'word'")
        word = item["word"].strip()
        if word and word not in seen:
            merged.append({"word": word})
            seen.add(word)
    for word in hotwords or []:
        word = word.strip()
        if word and word not in seen:
            merged.append({"word": word})
            seen.add(word)
    if merged:
        payload["hotwords"] = merged
    elif "hotwords" in payload:
        payload["hotwords"] = []
    return payload


def load_context_json(path: Path) -> dict[str, Any]:
    """Read an official corpus.context object from a JSON file."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid context JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"context JSON must contain an object: {path}")
    # Validate the shape now, before uploading any media.
    merge_context(value, None)
    return value


def build_headers(
    api_key: str, task_or_request_id: str, *, include_sequence: bool = False
) -> dict[str, str]:
    headers = {
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": RESOURCE_ID,
        "X-Api-Request-Id": task_or_request_id,
        "Content-Type": "application/json",
    }
    if include_sequence:
        headers["X-Api-Sequence"] = "-1"
    return headers


def is_retryable(http_status: int, api_code: Optional[str]) -> bool:
    return http_status in RETRYABLE_HTTP_STATUS or bool(
        api_code and api_code.startswith("550")
    )


def _post(url: str, headers: dict[str, str], body: Any, *, timeout: int) -> requests.Response:
    return requests.post(url, headers=headers, json=body, timeout=timeout)


def _response_error(response: requests.Response, stage: str) -> Optional[str]:
    if response.status_code in (401, 403):
        return f"{stage} authentication failed: HTTP {response.status_code}"
    if 400 <= response.status_code < 500:
        return f"{stage} rejected: HTTP {response.status_code}: {response.text[:200]}"
    if response.status_code >= 500:
        return f"{stage} server error: HTTP {response.status_code}: {response.text[:200]}"
    return None


def _response_json(response: requests.Response, stage: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    try:
        value = response.json() if response.content else {}
    except (ValueError, json.JSONDecodeError) as exc:
        return None, f"{stage} returned invalid JSON: {exc}"
    if not isinstance(value, dict):
        return None, f"{stage} returned a non-object JSON response"
    if isinstance(value.get("body"), dict):
        return value["body"], None
    return value, None


def recognize_standard(
    *,
    api_key: str,
    audio_url: Optional[str] = None,
    audio_path: Optional[Path] = None,
    audio_format: Optional[str] = None,
    language: Optional[str] = None,
    diarize: bool = False,
    meeting: bool = False,
    hotwords: Optional[list[str]] = None,
    context: Optional[dict[str, Any]] = None,
    poll_interval: int = 5,
    timeout_s: int = 1800,
) -> dict[str, Any]:
    """Submit to Doubao ASR 2.0 standard and poll using returned task_id."""
    if audio_path is None and not audio_url:
        return {"error": "audio_path or audio_url is required", "log_id": ""}
    encoded = None
    if audio_path is not None:
        reason = standard_limit_reason(audio_path)
        if reason:
            return {"error": reason, "log_id": ""}
        # Legacy file-upload API documented audio.data; ASR 2.0 still accepts it.
        encoded = base64.b64encode(audio_path.read_bytes()).decode("ascii")
    body = build_request_body(
        audio_data_b64=encoded,
        audio_url=audio_url,
        language=language,
        audio_format=audio_format,
        diarize=diarize,
        meeting=meeting,
        hotwords=hotwords,
        context=context,
    )
    request_id = str(uuid.uuid4())
    submit_headers = build_headers(api_key, request_id, include_sequence=True)
    log_id = ""
    submit_payload: Optional[dict[str, Any]] = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = _post(SUBMIT_ENDPOINT, submit_headers, body, timeout=600)
        except requests.RequestException as exc:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_BASE * 2**attempt)
                continue
            return {"error": f"submit request error: {exc}", "log_id": log_id}
        log_id = response.headers.get("X-Tt-Logid", log_id)
        code = response.headers.get("X-Api-Status-Code", "")
        message = response.headers.get("X-Api-Message", "")
        http_error = _response_error(response, "submit")
        if code == STATUS_SUCCESS and not http_error:
            submit_payload, json_error = _response_json(response, "submit")
            if json_error:
                return {"error": json_error, "log_id": log_id}
            break
        error = http_error or f"submit failed: {code or 'missing status'}: {message}"
        if is_retryable(response.status_code, code) and attempt < MAX_RETRIES:
            time.sleep(RETRY_BACKOFF_BASE * 2**attempt)
            continue
        return {"error": error, "log_id": log_id}

    task_id = (submit_payload or {}).get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        if audio_path is None:
            return {"error": "submit succeeded without task_id", "log_id": log_id}
        # The legacy audio.data path can return {} while echoing the request id
        # in X-Api-Request-Id. The current service still accepts that id for
        # query, so retain compatibility when no server task_id is returned.
        task_id = submit_headers["X-Api-Request-Id"]
        print(
            "submit response omitted task_id; using request id for compatibility",
            file=sys.stderr,
        )

    deadline = time.monotonic() + timeout_s
    poll_headers = build_headers(api_key, task_id)
    while time.monotonic() < deadline:
        try:
            response = _post(QUERY_ENDPOINT, poll_headers, {}, timeout=60)
        except requests.RequestException as exc:
            print(f"poll request error (retrying): {exc}", file=sys.stderr)
            time.sleep(poll_interval)
            continue
        log_id = response.headers.get("X-Tt-Logid", log_id)
        code = response.headers.get("X-Api-Status-Code", "")
        message = response.headers.get("X-Api-Message", "")
        http_error = _response_error(response, "query")
        if http_error and not is_retryable(response.status_code, code):
            return {"error": http_error, "log_id": log_id}
        if code in STATUS_EMPTY:
            return {
                "schema_version": 1, "text": "", "duration_ms": 0,
                "utterances": [], "speakers": [], "log_id": log_id,
            }
        if code == STATUS_SUCCESS:
            payload, json_error = _response_json(response, "query")
            if json_error:
                return {"error": json_error, "log_id": log_id}
            if "result" in (payload or {}):
                return normalize_result(payload or {}, log_id=log_id)
        elif code.startswith("45"):
            return {"error": f"query failed: {code}: {message}", "log_id": log_id}
        elif code not in STATUS_PENDING and not is_retryable(response.status_code, code):
            return {
                "error": f"query failed: {code or 'missing status'}: {message}",
                "log_id": log_id,
            }
        time.sleep(poll_interval)
    return {"error": f"timed out after {timeout_s}s waiting for transcription", "log_id": log_id}


def parse_hotwords(raw: Optional[str]) -> Optional[list[str]]:
    if not raw:
        return None
    seen: set[str] = set()
    output: list[str] = []
    for word in raw.replace("，", ",").split(","):
        word = word.strip()
        if word and word not in seen:
            seen.add(word)
            output.append(word)
    return output or None


def _url_stem(url: str) -> str:
    name = Path(urlparse(url).path).stem
    return name or f"asr-{uuid.uuid4().hex[:8]}"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="volcengine-asr",
        description=(
            "Transcribe with volc.seedasr.auc (Doubao ASR 2.0 standard) "
            "and generate SRT/VTT/TXT"
        ),
    )
    parser.add_argument("input", nargs="?", help="Local audio/video file or HTTP(S) URL")
    parser.add_argument("--audio-url", help="Public audio URL")
    parser.add_argument("--from-tts-meta", type=Path)
    parser.add_argument("--srt", nargs="?", const=True, default=False)
    parser.add_argument("--vtt", nargs="?", const=True, default=False)
    parser.add_argument("--txt", nargs="?", const=True, default=False)
    parser.add_argument("--transcript-json", nargs="?", const=True, default=True)
    parser.add_argument("--no-transcript-json", action="store_true")
    parser.add_argument(
        "--transcript-only",
        action="store_true",
        help="Write only the word-timestamp transcript JSON; no SRT/VTT/TXT",
    )
    parser.add_argument("-o", "--output-dir", type=Path)
    parser.add_argument("--language")
    parser.add_argument("--diarize", action="store_true")
    parser.add_argument("--meeting", action="store_true")
    parser.add_argument("--hotwords")
    parser.add_argument(
        "--context-json",
        type=Path,
        help="JSON file containing the full provider corpus.context object",
    )
    parser.add_argument("--max-cue-chars", type=float, default=DEFAULT_MAX_CUE_CHARS)
    parser.add_argument("--max-cue-duration", type=float, default=DEFAULT_MAX_CUE_DURATION_S)
    parser.add_argument("--poll-interval", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--keep-extracted-audio", action="store_true")
    args = parser.parse_args()

    if args.poll_interval < 0 or args.timeout <= 0:
        die("--poll-interval must be >= 0 and --timeout must be > 0")
    if args.max_cue_chars <= 0 or args.max_cue_duration <= 0:
        die("subtitle limits must be positive")
    if args.transcript_only and any((args.srt, args.vtt, args.txt)):
        die("--transcript-only cannot be combined with --srt, --vtt, or --txt")
    if args.transcript_only and args.no_transcript_json:
        die("--transcript-only cannot be combined with --no-transcript-json")
    context: Optional[dict[str, Any]] = None
    if args.context_json:
        try:
            context = load_context_json(args.context_json)
        except ValueError as exc:
            die(str(exc))

    source_path: Optional[Path] = None
    source_url: Optional[str] = None
    mode = "standard"
    if args.from_tts_meta:
        if context is not None:
            die("--context-json only applies to an ASR input, not --from-tts-meta")
        if not args.from_tts_meta.exists():
            die(f"TTS meta file not found: {args.from_tts_meta}")
        transcript = load_tts_meta(args.from_tts_meta)
        if not transcript["utterances"]:
            die(f"No word timestamps in {args.from_tts_meta}")
        default_dir, stem = default_output_stem(tts_meta=args.from_tts_meta)
        source_path = args.from_tts_meta
        model = "tts-meta"
        mode = "tts-meta"
    else:
        source = args.audio_url or args.input
        if not source:
            die("Provide an input file/URL, or use --from-tts-meta")
        api_key = load_api_key()
        hotwords = parse_hotwords(args.hotwords)
        model = RESOURCE_ID
        if is_url(source):
            source_url = source
            extension = Path(urlparse(source).path).suffix.lstrip(".").lower() or "mp3"
            default_dir, stem = Path.cwd(), _url_stem(source)
            transcript = recognize_standard(
                api_key=api_key,
                audio_url=source,
                audio_format=extension,
                language=args.language,
                diarize=args.diarize or args.meeting,
                meeting=args.meeting,
                hotwords=hotwords,
                context=context,
                poll_interval=args.poll_interval,
                timeout_s=args.timeout,
            )
        else:
            source_path = Path(source).expanduser().resolve()
            if not source_path.exists():
                die(f"Input file not found: {source_path}")
            default_dir, stem = default_output_stem(source=source_path)
            upload_path, temporary_path = prepare_local_media(
                source_path, keep_extracted=args.keep_extracted_audio
            )
            try:
                transcript = recognize_standard(
                    api_key=api_key,
                    audio_path=upload_path,
                    audio_format=upload_path.suffix.lstrip(".").lower() or "mp3",
                    language=args.language,
                    diarize=args.diarize or args.meeting,
                    meeting=args.meeting,
                    hotwords=hotwords,
                    context=context,
                    poll_interval=args.poll_interval,
                    timeout_s=args.timeout,
                )
            finally:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)

    if transcript.get("error"):
        print(json.dumps(transcript, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)

    out_dir = args.output_dir or default_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    if not args.transcript_only and not any((args.srt, args.vtt, args.txt)):
        args.srt = True
    outputs, cues, labels = write_outputs(
        transcript,
        out_dir=out_dir,
        stem=stem,
        srt=args.srt,
        vtt=args.vtt,
        txt=args.txt,
        max_weight=args.max_cue_chars,
        max_duration_ms=int(args.max_cue_duration * 1000),
    )

    if not args.no_transcript_json:
        transcript_spec = args.transcript_json
        transcript_path = resolve_output_path(
            transcript_spec, out_dir, stem, "transcript.json"
        )
        if transcript_path is not None:
            transcript_path.parent.mkdir(parents=True, exist_ok=True)
            source_ref = str(source_path) if source_path else source_url
            artifact = {
                **transcript,
                "source": source_ref,
                "mode": mode,
                "model": model,
                "cues": cues,
                "speaker_labels": labels,
            }
            transcript_path.write_text(
                json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            outputs["transcript_json"] = str(transcript_path)

    summary = {
        "source": str(source_path) if source_path else source_url,
        "mode": mode,
        "model": model,
        "duration_ms": transcript.get("duration_ms", 0),
        "text": transcript.get("text", ""),
        "utterances": len(transcript.get("utterances", [])),
        "cues": len(cues),
        "speakers": [
            f"发言人{labels[speaker]}"
            for speaker in transcript.get("speakers", [])
            if speaker in labels
        ],
        "outputs": outputs,
        "log_id": transcript.get("log_id", ""),
        "error": None,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
