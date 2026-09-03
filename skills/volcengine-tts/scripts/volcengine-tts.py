#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests>=2.32",
#   "mutagen>=1.47",
#   "python-dotenv>=1.0",
# ]
# ///

"""
Volcengine TTS — Doubao Speech Synthesis Model 2.0 (seed-tts-2.0).

Single sentence:
    uv run volcengine-tts.py "你好世界"

Batch mode:
    uv run volcengine-tts.py --batch '[{"text":"第一句"},{"text":"第二句"}]'

List speakers (local table, no API call):
    uv run volcengine-tts.py --list-speakers

API docs: https://www.volcengine.com/docs/6561/2528925?lang=zh
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv
from mutagen.mp3 import MP3

# ── API constants ──────────────────────────────────────────────────────────

API_BASE = "https://openspeech.bytedance.com"
TTS_ENDPOINT = f"{API_BASE}/api/v3/tts/unidirectional"

RESOURCE_ID = "seed-tts-2.0"
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SPEAKERS_JSON = SKILL_DIR / "references" / "speakers.json"
DEFAULT_SPEAKER = "zh_female_vv_uranus_bigtts"
DEFAULT_FORMAT = "mp3"
DEFAULT_SAMPLE_RATE = 24000
DEFAULT_CONCURRENCY = 3
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0  # seconds, exponential: base * 2^attempt

# Error codes that warrant a retry
RETRYABLE_VOLCANO_CODES = {"55000000"}  # service internal errors
RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}

# API success codes (volcano v3 uses 20000000 for success, 0 is also valid)
API_SUCCESS_CODES = {0, 20000000}


# ── Environment ────────────────────────────────────────────────────────────

def load_api_key() -> str:
    """Load VOLC_SPEECH_API_KEY with three-level fallback."""
    # Level 1: already in environment
    key = os.environ.get("VOLC_SPEECH_API_KEY", "").strip()
    if key:
        return key

    # Level 2: .env in current working directory
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env)
        key = os.environ.get("VOLC_SPEECH_API_KEY", "").strip()
        if key:
            return key

    # Level 3: user-level config
    user_env = Path.home() / ".volcengine.env"
    if user_env.exists():
        load_dotenv(user_env)
        key = os.environ.get("VOLC_SPEECH_API_KEY", "").strip()
        if key:
            return key

    die("VOLC_SPEECH_API_KEY not found. Set it via environment, .env file, or ~/.volcengine.env")


# ── Helpers ────────────────────────────────────────────────────────────────

def die(msg: str, code: int = 1) -> None:
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(code)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def get_mp3_duration_ms(path: Path) -> int:
    """Read MP3 duration in milliseconds from file header."""
    try:
        audio = MP3(str(path))
        if audio.info.length is not None:
            return int(audio.info.length * 1000)
    except Exception:
        pass
    return 0


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# ── Retry ──────────────────────────────────────────────────────────────────

def is_retryable(status_code: int, volcano_code: Optional[str]) -> bool:
    if status_code in RETRYABLE_HTTP_STATUS:
        return True
    if volcano_code and volcano_code in RETRYABLE_VOLCANO_CODES:
        return True
    return False


# ── TTS API call ───────────────────────────────────────────────────────────

def synthesize(
    text: str,
    *,
    api_key: str,
    speaker: str = DEFAULT_SPEAKER,
    fmt: str = DEFAULT_FORMAT,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    speech_rate: int = 0,
    loudness_rate: int = 0,
    pitch: int = 0,
    model: Optional[str] = None,
    ssml: bool = False,
    context_texts: Optional[list[str]] = None,
    language: Optional[str] = None,
    dialect: Optional[str] = None,
    enable_latex: bool = False,
    latex_parser: Optional[str] = None,
    silence_duration: int = 0,
    watermark: bool = False,
    disable_markdown_filter: bool = False,
    disable_emoji_filter: bool = False,
    enable_subtitle: bool = True,
) -> dict[str, Any]:
    """Call the Volcengine TTS HTTP unidirectional streaming API.

    Returns a dict with keys: audio_data (bytes), text_words, log_id,
    words (list of word-level timestamps, empty unless enable_subtitle=True),
    sentence_text (str), error.
    On success, error is None. On failure, audio_data is empty.
    """
    request_id = str(uuid.uuid4())
    headers = {
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": RESOURCE_ID,
        "X-Api-Request-Id": request_id,
        "X-Control-Require-Usage-Tokens-Return": "*",
        "Content-Type": "application/json",
        "Connection": "keep-alive",
    }

    audio_params: dict[str, Any] = {
        "format": fmt,
        "sample_rate": sample_rate,
    }
    if speech_rate != 0:
        audio_params["speech_rate"] = speech_rate
    if loudness_rate != 0:
        audio_params["loudness_rate"] = loudness_rate
    if enable_subtitle:
        audio_params["enable_subtitle"] = True

    body: dict[str, Any] = {
        "req_params": {
            "text": text,
            "speaker": speaker,
            "audio_params": audio_params,
        }
    }
    additions: dict[str, Any] = {}

    if model:
        body["req_params"]["model"] = model
    if ssml:
        body["req_params"]["ssml"] = "1"
    if context_texts:
        body["req_params"]["context_texts"] = context_texts
    if language:
        body["req_params"]["explicit_language"] = language
    if dialect:
        body["req_params"]["explicit_dialect"] = dialect
    if enable_latex or latex_parser:
        additions["enable_latex_tn"] = True
        additions["disable_markdown_filter"] = True
    if latex_parser:
        additions["latex_parser"] = latex_parser
    if silence_duration > 0:
        additions["silence_duration"] = silence_duration
    if watermark:
        additions["aigc_watermark"] = True
    if disable_markdown_filter:
        additions["disable_markdown_filter"] = True
    if disable_emoji_filter:
        additions["disable_emoji_filter"] = True
    if pitch != 0:
        additions["post_process"] = {"pitch": pitch}
    if additions:
        # API expects `additions` as a JSON-encoded string, not an object.
        # Passing a dict triggers: "json: cannot unmarshal object into Go
        # struct field TTSReqParams.req_params.additions of type string"
        body["req_params"]["additions"] = json.dumps(additions)

    last_error: Optional[str] = None
    log_id: str = ""

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.post(
                TTS_ENDPOINT,
                headers=headers,
                json=body,
                stream=True,
                timeout=60,
            )
            log_id = resp.headers.get("X-Tt-Logid", "")

            if not resp.ok:
                volcano_code = None
                try:
                    error_data = resp.json()
                    volcano_code = str(error_data.get("code", ""))
                    last_error = f"{volcano_code}: {error_data.get('message', resp.text)}"
                except Exception:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"

                if is_retryable(resp.status_code, volcano_code) and attempt < MAX_RETRIES:
                    delay = RETRY_BACKOFF_BASE * (2 ** attempt)
                    time.sleep(delay)
                    continue
                return {
                    "audio_data": b"",
                    "text_words": 0,
                    "log_id": log_id,
                    "error": last_error,
                }

            # Read chunked response
            audio_chunks: list[bytes] = []
            text_words = 0
            words: list[dict[str, Any]] = []
            sentence_text: str = ""
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue

                code = chunk.get("code", -1)
                if code not in API_SUCCESS_CODES:
                    volcano_code = str(code)
                    msg = chunk.get("message", "unknown error")
                    last_error = f"{volcano_code}: {msg}"

                    if is_retryable(resp.status_code, volcano_code) and attempt < MAX_RETRIES:
                        delay = RETRY_BACKOFF_BASE * (2 ** attempt)
                        time.sleep(delay)
                        break  # break inner loop, retry outer
                    return {
                        "audio_data": b"",
                        "text_words": 0,
                        "words": [],
                        "sentence_text": "",
                        "log_id": log_id,
                        "error": last_error,
                    }

                data_b64 = chunk.get("data", "")
                if data_b64:
                    try:
                        audio_chunks.append(base64.b64decode(data_b64))
                    except Exception:
                        pass

                sentence = chunk.get("sentence")
                if isinstance(sentence, dict):
                    sentence_text = sentence.get("text", sentence_text) or sentence_text
                    sw = sentence.get("words")
                    if isinstance(sw, list) and sw:
                        # Server may send words split across chunks; dedupe by (word, startTime, endTime)
                        seen: set[tuple[str, float, float]] = set()
                        merged: list[dict[str, Any]] = []
                        for w in words + sw:
                            key = (str(w.get("word", "")), float(w.get("startTime", 0.0)), float(w.get("endTime", 0.0)))
                            if key in seen:
                                continue
                            seen.add(key)
                            merged.append(w)
                        words = merged

                usage = chunk.get("usage", {})
                if isinstance(usage, dict):
                    text_words = usage.get("text_words", text_words)

            if last_error and attempt < MAX_RETRIES:
                continue

            return {
                "audio_data": b"".join(audio_chunks),
                "text_words": text_words,
                "words": words,
                "sentence_text": sentence_text,
                "log_id": log_id,
                "error": last_error if last_error else None,
            }

        except requests.RequestException as e:
            last_error = f"Request error: {e}"
            if attempt < MAX_RETRIES:
                delay = RETRY_BACKOFF_BASE * (2 ** attempt)
                time.sleep(delay)
                continue
            return {
                "audio_data": b"",
                "text_words": 0,
                "words": [],
                "sentence_text": "",
                "log_id": log_id,
                "error": last_error,
            }

    return {
        "audio_data": b"",
        "text_words": 0,
        "words": [],
        "sentence_text": "",
        "log_id": log_id,
        "error": last_error or "Max retries exceeded",
    }


# ── Single synthesis ───────────────────────────────────────────────────────

def synthesize_one(
    text: str,
    output_dir: Path,
    *,
    api_key: str,
    speaker: str = DEFAULT_SPEAKER,
    **kwargs: Any,
) -> dict[str, Any]:
    """Synthesize one sentence, save audio + metadata, return result dict."""
    result = synthesize(text, api_key=api_key, speaker=speaker, **kwargs)

    timestamp = now_iso()
    # Use a simple counter embedded in the function's closure-like state
    seq = synthesize_one._seq if hasattr(synthesize_one, "_seq") else 0
    synthesize_one._seq = seq + 1  # type: ignore[attr-defined]

    filename = f"tts_{timestamp}_{seq:03d}"
    audio_path = output_dir / f"{filename}.{kwargs.get('fmt', DEFAULT_FORMAT)}"
    meta_path = output_dir / f"{filename}.meta.json"

    error = result.get("error")
    duration_ms = 0

    if not error and result["audio_data"]:
        ensure_dir(output_dir)
        audio_path.write_bytes(result["audio_data"])
        duration_ms = get_mp3_duration_ms(audio_path)

    meta: dict[str, Any] = {
        "text": text,
        "speaker": speaker,
        "format": kwargs.get("fmt", DEFAULT_FORMAT),
        "sample_rate": kwargs.get("sample_rate", DEFAULT_SAMPLE_RATE),
        "text_words": result["text_words"],
        "log_id": result["log_id"],
        "duration_ms": duration_ms,
        "error": error,
    }
    if result.get("words"):
        meta["words"] = result["words"]
    if result.get("sentence_text"):
        meta["sentence_text"] = result["sentence_text"]

    if not error and result["audio_data"]:
        ensure_dir(output_dir)
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "audio_file": str(audio_path) if not error else None,
        "duration_ms": duration_ms,
        "text": text,
        "speaker": speaker,
        "format": kwargs.get("fmt", DEFAULT_FORMAT),
        "sample_rate": kwargs.get("sample_rate", DEFAULT_SAMPLE_RATE),
        "text_words": result["text_words"],
        "log_id": result["log_id"],
        "words": result.get("words", []),
        "sentence_text": result.get("sentence_text", ""),
        "error": error,
    }


# ── Batch synthesis ────────────────────────────────────────────────────────

def synthesize_batch(
    items: list[dict[str, Any]],
    output_dir: Path,
    *,
    api_key: str,
    concurrency: int = DEFAULT_CONCURRENCY,
    base_kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Synthesize multiple sentences concurrently."""
    results: list[Optional[dict[str, Any]]] = [None] * len(items)

    def task(idx: int, item: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        text = item.get("text", "")
        if not text:
            return idx, {"audio_file": None, "duration_ms": 0, "text": "", "error": "Empty text"}

        kwargs = {**base_kwargs}
        kwargs["speaker"] = item.get("speaker", base_kwargs.get("speaker", DEFAULT_SPEAKER))
        # Simple scalar overrides (key in item → kwarg name passed to synthesize())
        scalar_map = {
            "speech_rate": "speech_rate",
            "volume": "loudness_rate",
            "pitch": "pitch",
            "model": "model",
            "language": "language",
            "format": "fmt",
            "sample_rate": "sample_rate",
            "ssml": "ssml",
            "silence_duration": "silence_duration",
            "watermark": "watermark",
            "subtitle": "enable_subtitle",
            "strip_markdown": "disable_markdown_filter",
            "strip_emoji": "disable_emoji_filter",
            "latex": "enable_latex",
            "latex_parser": "latex_parser",
        }
        for item_key, kwarg_key in scalar_map.items():
            if item_key in item:
                kwargs[kwarg_key] = item[item_key]
        # context can come either as a string (single instruction) or list of strings
        if "context" in item:
            ctx = item["context"]
            kwargs["context_texts"] = [ctx] if isinstance(ctx, str) else list(ctx)
        elif "context_texts" in item:
            ctx = item["context_texts"]
            kwargs["context_texts"] = [ctx] if isinstance(ctx, str) else list(ctx)

        return idx, synthesize_one(text, output_dir, api_key=api_key, **kwargs)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(task, i, item): i for i, item in enumerate(items)}
        for future in as_completed(futures):
            idx, result = future.result()
            results[idx] = result

    valid = [r for r in results if r is not None]
    return {
        "results": valid,
        "total_duration_ms": sum(r.get("duration_ms", 0) for r in valid),
        "success_count": sum(1 for r in valid if not r.get("error")),
        "fail_count": sum(1 for r in valid if r.get("error")),
    }


# ── List speakers (local table) ────────────────────────────────────────────

def query_speakers(speakers: list[dict], *, filters: dict | None = None, sort_by: str | None = None) -> list[dict]:
    """Filter/sort the local speakers.json catalog. lang contains-matches languages[]."""
    result = list(speakers)
    if filters:
        for k, v in filters.items():
            if k == "lang":
                result = [s for s in result if v in s.get("languages", [])]
            else:
                result = [s for s in result if s.get(k) == v]
    if sort_by == "heat":
        result = sorted(result, key=lambda s: -s.get("heat", 0))
    return result


def _list_speakers(args) -> None:
    if not SPEAKERS_JSON.exists():
        die(f"speakers.json not found: {SPEAKERS_JSON}")
    speakers = json.loads(SPEAKERS_JSON.read_text(encoding="utf-8"))
    filters = {}
    if args.filter:
        for f in args.filter:
            k, _, v = f.partition("=")
            filters[k] = v
    result = query_speakers(speakers, filters=filters or None, sort_by=args.sort)
    out = [
        {
            "name": s["name"],
            "voice_type": s["voice_type"],
            "type": s["type"],
            "gender": s.get("gender", ""),
            "scene": s.get("scene", ""),
            "description": s.get("description", "")[:40],
            "heat": s.get("heat", 0),
        }
        for s in result
    ]
    print(json.dumps({"total": len(out), "speakers": out}, ensure_ascii=False, indent=2))


# ── CLI ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="volcengine-tts",
        description="Volcengine Doubao TTS (seed-tts-2.0) — text to speech",
    )

    # Mode: single text or batch
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to synthesize (single mode)",
    )
    parser.add_argument(
        "--batch", "-b",
        help="Batch mode: JSON array of {\"text\": \"...\", \"speaker\": \"...\", ...}",
    )

    # Output
    parser.add_argument(
        "--output-dir", "-o",
        default="./tts-output/",
        help="Output directory (default: ./tts-output/)",
    )
    parser.add_argument(
        "--speaker", "-s",
        default=DEFAULT_SPEAKER,
        help=f"Speaker/voice ID (default: {DEFAULT_SPEAKER})",
    )

    # Audio params
    parser.add_argument("--format", default=DEFAULT_FORMAT, choices=["mp3", "pcm", "ogg_opus", "wav"])
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE)
    parser.add_argument("--speech-rate", type=int, default=0, help="Speed [-50, 100], 100=2x")
    parser.add_argument("--volume", type=int, default=0, help="Volume [-50, 100], 100=2x")
    parser.add_argument("--pitch", type=int, default=0, help="Pitch [-12, 12] semitones")
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Model variant to pass to the API. Omit by default (server picks). "
            "Mainly useful for cloned (ICL) voices, e.g. 'seed-tts-2.0-standard'. "
            "Official seed-tts-2.0 voices support --context without setting this."
        ),
    )
    parser.add_argument("--ssml", action="store_true", help="Parse text as SSML")
    parser.add_argument("--context", help="Voice instruction, e.g. '用温柔的语气说话'")
    parser.add_argument("--language", help="Explicit language: zh-cn, en, ja, es-mx, id, pt-br, ko")
    parser.add_argument("--silence-duration", type=int, default=0, help="Trailing silence ms [0, 30000]")
    parser.add_argument("--watermark", action="store_true", help="Add AIGC audio watermark")
    parser.add_argument("--no-subtitle", dest="subtitle", action="store_false", help="Disable word-level timestamps (saves ~600ms tail latency for latency-sensitive / realtime use cases)")
    parser.add_argument("--strip-markdown", action="store_true", help="Remove markdown syntax before TTS")
    parser.add_argument("--strip-emoji", action="store_true", help="Remove emoji characters before TTS")
    parser.add_argument("--latex", action="store_true", help="Enable LaTeX formula reading; auto-enables markdown filtering")
    parser.add_argument("--latex-parser", choices=["v2"], help="Stronger LaTeX parser for math/education narration; auto-enables --latex and --strip-markdown")

    # Batch
    parser.add_argument("--concurrency", "-c", type=int, default=DEFAULT_CONCURRENCY, help=f"Max parallel requests (default: {DEFAULT_CONCURRENCY})")

    # Info
    parser.add_argument("--list-speakers", action="store_true", help="list speakers from local table (no API call)")
    parser.add_argument("--filter", action="append", help="filter: scene=教学场景 / type=bigtts / lang=ja")
    parser.add_argument("--sort", choices=["heat"], help="sort by field")

    args = parser.parse_args()

    # --list-speakers mode (local table; does not need VOLC_SPEECH_API_KEY)
    if args.list_speakers:
        _list_speakers(args)
        return

    # Validate mode
    if args.batch:
        try:
            items = json.loads(args.batch)
        except json.JSONDecodeError as e:
            die(f"Invalid --batch JSON: {e}")
        if not isinstance(items, list) or len(items) == 0:
            die("--batch must be a non-empty JSON array")
    elif args.text:
        items = [{"text": args.text}]
    else:
        die("Either provide text as positional argument, use --batch '[...]', or --list-speakers")

    api_key = load_api_key()
    output_dir = Path(args.output_dir)

    base_kwargs: dict[str, Any] = {
        "speaker": args.speaker,
        "fmt": args.format,
        "sample_rate": args.sample_rate,
        "speech_rate": args.speech_rate,
        "loudness_rate": args.volume,
        "pitch": args.pitch,
        "model": args.model,
        "ssml": args.ssml,
        "context_texts": [args.context] if args.context else None,
        "language": args.language,
        "silence_duration": args.silence_duration,
        "watermark": args.watermark,
        "enable_subtitle": args.subtitle,
        "disable_markdown_filter": args.strip_markdown,
        "disable_emoji_filter": args.strip_emoji,
        "enable_latex": args.latex,
        "latex_parser": args.latex_parser,
    }

    if args.batch:
        result = synthesize_batch(
            items,
            output_dir,
            api_key=api_key,
            concurrency=args.concurrency,
            base_kwargs=base_kwargs,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Single mode: items has exactly one entry
        item = items[0]
        kwargs = {**base_kwargs}
        kwargs["speaker"] = item.get("speaker", base_kwargs["speaker"])
        result = synthesize_one(item["text"], output_dir, api_key=api_key, **kwargs)
        print(json.dumps(result, ensure_ascii=False, indent=2))

        if result.get("error"):
            sys.exit(1)


if __name__ == "__main__":
    main()
