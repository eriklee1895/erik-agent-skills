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
Volcengine ASR — Doubao audio-file speech recognition (豆包录音文件识别).

Transcribe a local audio/video file (or a URL) and emit SRT / VTT / TXT
subtitles, plus a machine-readable JSON transcript.

Two endpoints, same API key as volcengine-tts (VOLC_SPEECH_API_KEY):

  flash    POST /api/v3/auc/bigmodel/recognize/flash   (volc.bigasr.auc_turbo)
           base64 direct upload, synchronous, one request.
           Limits: <= 2h, <= 100MB, WAV/MP3/OGG. Default for local files.

  standard POST /api/v3/auc/bigmodel/submit + /query   (volc.seedasr.auc)
           async submit/poll; audio must be a public URL (no local upload).
           Limits: <= 5h, <= 512MB. Escape hatch for long recordings.

Examples:
    uv run volcengine-asr.py meeting.mp3 --srt
    uv run volcengine-asr.py interview.mp4 --diarize --srt --vtt
    uv run volcengine-asr.py https://example.com/long.mp3 --mode standard --srt
    uv run volcengine-asr.py --from-tts-meta tts-output/tts_001.meta.json --srt

API docs:
    flash:    https://www.volcengine.com/docs/6561/1631584
    submit:   https://www.volcengine.com/docs/6561/2606791
    query:    https://www.volcengine.com/docs/6561/2606792
"""

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
import unicodedata
import uuid
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv

try:
    import mutagen
except ImportError:  # mutagen only needed for duration probing
    mutagen = None  # type: ignore[assignment]

# ── API constants ──────────────────────────────────────────────────────────

API_BASE = "https://openspeech.bytedance.com"
FLASH_ENDPOINT = f"{API_BASE}/api/v3/auc/bigmodel/recognize/flash"
SUBMIT_ENDPOINT = f"{API_BASE}/api/v3/auc/bigmodel/submit"
QUERY_ENDPOINT = f"{API_BASE}/api/v3/auc/bigmodel/query"

FLASH_RESOURCE_ID = "volc.bigasr.auc_turbo"
STANDARD_RESOURCE_ID = "volc.seedasr.auc"

FLASH_MAX_DURATION_S = 2 * 3600
FLASH_MAX_BYTES = 100 * 1024 * 1024
# base64 inflates payload by ~33%; transcode proactively before this to stay
# well under the server-side 100MB limit and the doc's "prefer <=20MB upload"
# guidance.
TRANSCODE_OVER_BYTES = 80 * 1024 * 1024

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".flv", ".webm", ".ts", ".m4v", ".wmv", ".3gp"}
# Flash officially supports WAV / MP3 / OGG OPUS; anything else is transcoded
# to mp3 when ffmpeg is available.
FLASH_NATIVE_AUDIO_EXTS = {".mp3", ".wav", ".ogg"}
AUDIO_EXTS = VIDEO_EXTS | FLASH_NATIVE_AUDIO_EXTS | {
    ".m4a", ".aac", ".flac", ".opus", ".wma", ".spx", ".amr", ".pcm",
}

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0
RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}
STATUS_SUCCESS = "20000000"
STATUS_EMPTY = "20000003"          # silence / no speech — empty result, not an error
STATUS_EMPTY_AUDIO = "45000002"    # empty audio upload — treat as empty result
STATUS_PENDING = {"20000001", "20000002"}  # standard mode: task still running
EMPTY_STATUSES = {STATUS_EMPTY, STATUS_EMPTY_AUDIO}

# ── Subtitle grouping defaults ─────────────────────────────────────────────

DEFAULT_MAX_CUE_CHARS = 20        # weighted chars (CJK=1, latin≈0.55)
DEFAULT_MAX_CUE_DURATION_S = 7.0
MIN_CLAUSE_WEIGHT = 10            # clause punctuation only breaks past this
MIN_CLAUSE_DURATION_MS = 2500
HARD_CUE_FACTOR = 1.5             # force break even without punctuation
SPEAKER_GAP_MS = 1200             # silence gap that forces a cue boundary

SENTENCE_PUNCT = set("。！？!?；;…\n.")
CLAUSE_PUNCT = set("，,、：:")

SPEAKER_LABELS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


# ── Environment ────────────────────────────────────────────────────────────

def load_api_key() -> str:
    """Load VOLC_SPEECH_API_KEY with three-level fallback (same key as TTS)."""
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
        "VOLC_SPEECH_API_KEY not found. Set it via environment, .env file, "
        "or ~/.volcengine.env (same key as volcengine-tts)."
    )


# ── Helpers ────────────────────────────────────────────────────────────────

def die(msg: str, code: int = 1) -> None:
    print(json.dumps({"error": msg}, ensure_ascii=False), file=sys.stderr)
    sys.exit(code)


def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def probe_duration_s(path: Path) -> float:
    """Best-effort audio duration in seconds via mutagen; 0.0 if unknown."""
    if mutagen is None:
        return 0.0
    try:
        audio = mutagen.File(str(path))
        if audio is not None and audio.info is not None and audio.info.length:
            return float(audio.info.length)
    except Exception:
        pass
    return 0.0


def have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def build_ffmpeg_cmd(src: Path, dst: Path) -> list[str]:
    """Extract/transcode to 16kHz mono MP3 (ideal ASR input, small upload).

    `aresample=async=1:first_pts=0` is mandatory for subtitle-grade timing:
    when the source audio has PTS gaps (recording pauses, concatenated clips,
    re-muxed streams), plain extraction concatenates samples and silently
    shortens the timeline — subtitles then drift cumulatively (a real 31-min
    video drifted 8.5s). async=1 fills gaps with silence / drops overlaps per
    the source PTS; first_pts=0 anchors streams that don't start at 0.
    It is a no-op for clean sources.
    """
    return [
        "ffmpeg", "-y", "-i", str(src),
        "-vn",
        "-af", "aresample=async=1:first_pts=0",
        "-ac", "1", "-ar", "16000", "-b:a", "64k",
        "-f", "mp3", str(dst),
    ]


def ensure_has_audio(path: Path) -> None:
    """Fail fast with a clear message when a video file has no audio track."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_type", "-of", "json",
        str(path),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return  # probe is best-effort; ffmpeg will still produce a real error
    if proc.returncode != 0:
        return
    try:
        streams = json.loads(proc.stdout or "{}").get("streams", [])
    except json.JSONDecodeError:
        return
    if streams and not any(s.get("codec_type") == "audio" for s in streams):
        die(f"File has no audio track: {path.name} (video-only stream — nothing to transcribe).")


def ffmpeg_to_mp3(src: Path, dst: Path) -> None:
    cmd = build_ffmpeg_cmd(src, dst)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        raise RuntimeError("ffmpeg timed out after 600s — the input file may be corrupt or extremely large.")
    if proc.returncode != 0:
        tail = (proc.stderr or "")[-500:]
        raise RuntimeError(f"ffmpeg failed (exit {proc.returncode}): {tail}")


# ── Media preparation ──────────────────────────────────────────────────────

def prepare_local_media(path: Path, *, keep_extracted: bool = False) -> tuple[Path, Optional[Path]]:
    """Return (path_to_upload, temp_path_to_clean_up).

    Video          -> ffmpeg audio extraction to a temp 16k mono mp3.
    Audio >80MB    -> ffmpeg transcode to a temp 16k mono mp3.
    Other audio    -> sent as-is.
    """
    ext = path.suffix.lower()
    if ext not in AUDIO_EXTS:
        die(f"Unsupported file type '{ext}'. Supported: {sorted(AUDIO_EXTS)}")

    is_video = ext in VIDEO_EXTS
    needs_transcode = is_video or ext not in FLASH_NATIVE_AUDIO_EXTS
    if is_video:
        ensure_has_audio(path)
    if not needs_transcode and path.stat().st_size <= TRANSCODE_OVER_BYTES:
        return path, None

    if not have_ffmpeg():
        if is_video:
            die(
                "Input is a video file but ffmpeg is not installed. "
                "Install ffmpeg (e.g. `brew install ffmpeg`) or extract the "
                "audio track yourself and pass the .mp3/.wav."
            )
        # Non-native audio (m4a/aac/flac/...) without ffmpeg: try sending as-is;
        # the server may still accept it.
        return path, None

    if keep_extracted:
        out = path.with_name(f"{path.stem}.asr-16k-mono.mp3")
        ffmpeg_to_mp3(path, out)
        print(f"Extracted audio kept at: {out}", file=sys.stderr)
        return out, None

    fd, tmp_name = tempfile.mkstemp(prefix="asr-", suffix=".mp3")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        ffmpeg_to_mp3(path, tmp)
    except Exception as e:
        tmp.unlink(missing_ok=True)
        die(str(e))
    return tmp, tmp


def flash_limit_reason(path: Path) -> Optional[str]:
    """Return a human-readable reason if `path` exceeds flash limits, else None."""
    size = path.stat().st_size
    if size > FLASH_MAX_BYTES:
        return f"audio is {size / 1024 / 1024:.0f}MB after preparation, above the flash limit of 100MB"
    duration = probe_duration_s(path)
    if duration > FLASH_MAX_DURATION_S:
        return f"audio is {duration / 60:.0f} min long, above the flash limit of 120 min"
    return None


def check_flash_limits(path: Path) -> None:
    reason = flash_limit_reason(path)
    if reason:
        die(
            f"{reason}. Re-run with --mode standard (async, supports up to 5h; "
            f"local files are uploaded directly)."
        )


# ── Request building (pure; unit-tested) ───────────────────────────────────

def build_request_body(
    *,
    audio_data_b64: Optional[str] = None,
    audio_url: Optional[str] = None,
    language: Optional[str] = None,
    audio_format: Optional[str] = None,
    send_format: bool = False,
    diarize: bool = False,
    meeting: bool = False,
    hotwords: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Build the request payload shared by flash and standard endpoints."""
    audio: dict[str, Any] = {}
    if audio_url:
        audio["url"] = audio_url
    if audio_data_b64 is not None:
        audio["data"] = audio_data_b64
    # Flash data mode sniffs the format from the bytes (proven clients omit
    # it); standard submit requires/accepts explicit format, even for data.
    if (audio_url or send_format) and audio_format:
        audio["format"] = audio_format
    if language:
        audio["language"] = language

    request: dict[str, Any] = {
        "model_name": "bigmodel",
        "enable_itn": True,    # 口语数字/日期 → 书面格式 ("一百二十三" → "123")
        "enable_punc": True,
        "enable_ddc": False,   # keep fillers/语气词 for subtitle fidelity
        "show_utterances": True,  # required for timestamps + speaker info
    }
    if diarize or meeting:
        request["enable_speaker_info"] = True
        # 300 = voiceprint matching for long meetings; 200 = <=5 speakers.
        request["ssd_version"] = "300" if meeting else "200"
    if hotwords:
        request["corpus"] = {
            "context": json.dumps(
                {"hotwords": [{"word": w} for w in hotwords]}, ensure_ascii=False
            )
        }

    return {"user": {"uid": "erik-agent-skills-asr"}, "audio": audio, "request": request}


def build_headers(api_key: str, resource_id: str, request_id: str) -> dict[str, str]:
    return {
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Request-Id": request_id,
        "X-Api-Sequence": "-1",
        "Content-Type": "application/json",
    }


def is_retryable(http_status: int, api_code: Optional[str]) -> bool:
    if http_status in RETRYABLE_HTTP_STATUS:
        return True
    if api_code and (api_code == "55000031" or api_code.startswith("550")):
        return True
    return False


# ── API calls ──────────────────────────────────────────────────────────────

def _post(url: str, headers: dict[str, str], body: Any, *, timeout: int) -> requests.Response:
    return requests.post(url, headers=headers, json=body, timeout=timeout)


def recognize_flash(
    *,
    api_key: str,
    audio_path: Optional[Path] = None,
    audio_url: Optional[str] = None,
    language: Optional[str] = None,
    audio_format: Optional[str] = None,
    diarize: bool = False,
    meeting: bool = False,
    hotwords: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Synchronous flash recognition. Returns normalized transcript dict."""
    b64: Optional[str] = None
    if audio_path is not None:
        b64 = base64.b64encode(audio_path.read_bytes()).decode("ascii")

    body = build_request_body(
        audio_data_b64=b64,
        audio_url=audio_url,
        language=language,
        audio_format=audio_format,
        diarize=diarize,
        meeting=meeting,
        hotwords=hotwords,
    )

    last_error = "unknown error"
    log_id = ""
    for attempt in range(MAX_RETRIES + 1):
        request_id = str(uuid.uuid4())
        headers = build_headers(api_key, FLASH_RESOURCE_ID, request_id)
        try:
            resp = _post(FLASH_ENDPOINT, headers, body, timeout=600)
            log_id = resp.headers.get("X-Tt-Logid", "")
            code = resp.headers.get("X-Api-Status-Code", "")
            message = resp.headers.get("X-Api-Message", "")

            if code in EMPTY_STATUSES:
                return {"text": "", "duration_ms": 0, "utterances": [], "speakers": [], "log_id": log_id}
            if code != STATUS_SUCCESS:
                last_error = f"{code or 'HTTP ' + str(resp.status_code)}: {message or resp.text[:200]}"
                if is_retryable(resp.status_code, code) and attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_BASE * 2**attempt)
                    continue
                return {"error": last_error, "log_id": log_id}

            return normalize_result(resp.json(), log_id=log_id)

        except requests.RequestException as e:
            last_error = f"Request error: {e}"
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_BASE * 2**attempt)
                continue

    return {"error": last_error, "log_id": log_id}


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
    poll_interval: int = 5,
    timeout_s: int = 1800,
) -> dict[str, Any]:
    """Async submit + poll. Accepts a public URL or a local file (base64).

    The submit endpoint accepts audio.data despite the docs only showing
    audio.url (verified live 2026-09 with volc.seedasr.auc).
    """
    b64: Optional[str] = None
    if audio_path is not None:
        b64 = base64.b64encode(audio_path.read_bytes()).decode("ascii")
    elif not audio_url:
        return {"error": "standard mode requires audio_path or audio_url", "log_id": ""}

    request_id = str(uuid.uuid4())
    body = build_request_body(
        audio_data_b64=b64,
        audio_url=audio_url,
        language=language,
        audio_format=audio_format,
        send_format=True,
        diarize=diarize,
        meeting=meeting,
        hotwords=hotwords,
    )
    headers = build_headers(api_key, STANDARD_RESOURCE_ID, request_id)

    # ── submit ──
    submit_code = ""
    log_id = ""
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = _post(SUBMIT_ENDPOINT, headers, body, timeout=600)
            log_id = resp.headers.get("X-Tt-Logid", "")
            submit_code = resp.headers.get("X-Api-Status-Code", "")
            message = resp.headers.get("X-Api-Message", "")
            if submit_code == STATUS_SUCCESS:
                break
            last_error = f"{submit_code or 'HTTP ' + str(resp.status_code)}: {message or resp.text[:200]}"
            if is_retryable(resp.status_code, submit_code) and attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_BASE * 2**attempt)
                continue
            return {"error": f"submit failed: {last_error}", "log_id": log_id}
        except requests.RequestException as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_BASE * 2**attempt)
                continue
            return {"error": f"submit request error: {e}", "log_id": log_id}

    # ── poll ──
    deadline = time.monotonic() + timeout_s
    poll_headers = build_headers(api_key, STANDARD_RESOURCE_ID, request_id)
    while time.monotonic() < deadline:
        try:
            resp = _post(QUERY_ENDPOINT, poll_headers, {}, timeout=60)
            log_id = resp.headers.get("X-Tt-Logid", log_id)
            code = resp.headers.get("X-Api-Status-Code", "")
            message = resp.headers.get("X-Api-Message", "")
            if code in EMPTY_STATUSES:
                return {"text": "", "duration_ms": 0, "utterances": [], "speakers": [], "log_id": log_id}
            if code == STATUS_SUCCESS:
                body = resp.json() if resp.content else {}
                # Success with no result yet means the task is still running.
                if "result" not in body:
                    time.sleep(poll_interval)
                    continue
                return normalize_result(body, log_id=log_id)
            if code in STATUS_PENDING:
                time.sleep(poll_interval)
                continue
            # 45xxxxxx fatal; 55xxxxxx retriable within the poll window
            if code.startswith("45"):
                return {"error": f"{code}: {message}", "log_id": log_id}
            time.sleep(poll_interval)
        except requests.RequestException as e:
            # transient network blip during polling — keep polling until deadline
            print(f"poll error (will retry): {e}", file=sys.stderr)
            time.sleep(poll_interval)

    return {"error": f"timed out after {timeout_s}s waiting for transcription", "log_id": log_id}


# ── Result normalization (pure; unit-tested) ───────────────────────────────

def _is_punct(ch: str) -> bool:
    return unicodedata.category(ch).startswith("P")


def reinsert_punctuation(text: str, words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Align utterance `text` (which carries enable_punc punctuation) onto
    word tokens (which omit punctuation — verified against the live API).

    Punctuation sitting between two words is appended to the preceding word;
    trailing punctuation to the last word. This lets the cue grouper break on
    。/， exactly where the ASR placed them.
    """
    if not words:
        return words
    out = [dict(w) for w in words]
    pos = 0
    last_aligned_i = -1
    for i, w in enumerate(out):
        token = w.get("text") or ""
        if not token:
            continue
        idx = text.find(token, pos)
        if idx == -1:
            continue  # ASR/ITN mismatch — leave this token untouched
        between = "".join(ch for ch in text[pos:idx] if _is_punct(ch))
        if between:
            target = out[i - 1] if i > 0 else out[i]
            target["text"] = (target["text"] + between) if i > 0 else (between + target["text"])
        pos = idx + len(token)
        last_aligned_i = i
    if last_aligned_i == len(out) - 1:
        tail = "".join(ch for ch in text[pos:] if _is_punct(ch))
        if tail:
            out[-1]["text"] = out[-1]["text"] + tail
    return out


def normalize_result(body: dict[str, Any], *, log_id: str = "") -> dict[str, Any]:
    """Normalize the raw API body into a flat transcript structure (ms units)."""
    result = body.get("result") or {}
    additions = result.get("additions") or {}
    audio_info = body.get("audio_info") or {}

    duration_ms = 0
    for src in (audio_info.get("duration"), additions.get("duration")):
        try:
            if src:
                duration_ms = int(float(src))
                break
        except (TypeError, ValueError):
            pass

    utterances: list[dict[str, Any]] = []
    speaker_order: list[str] = []
    for u in result.get("utterances") or []:
        u_adds = u.get("additions") or {}
        speaker = u_adds.get("speaker")
        if speaker is not None:
            speaker = str(speaker)
            if speaker not in speaker_order:
                speaker_order.append(speaker)
        words = []
        for w in u.get("words") or []:
            w_text = w.get("text", "")
            start_ms = int(w.get("start_time", 0))
            end_ms = int(w.get("end_time", 0))
            # English responses include explicit space tokens with no
            # timestamp (text=" ", start/end=-1). They would poison cue
            # start/end times and double spaces — drop them; cue rendering
            # re-derives word spacing from the token pair.
            if not w_text.strip() or (start_ms < 0 and end_ms < 0):
                continue
            words.append({
                "text": w_text,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "confidence": w.get("confidence", 0),
            })
        words = reinsert_punctuation((u.get("text") or ""), words)
        utterances.append({
            "text": (u.get("text") or "").strip(),
            "start_ms": int(u.get("start_time", 0)),
            "end_ms": int(u.get("end_time", 0)),
            "speaker": speaker,
            "channel": u_adds.get("channel_id"),
            "words": words,
        })

    text = result.get("text") or "".join(u["text"] for u in utterances)
    return {
        "text": text.strip(),
        "duration_ms": duration_ms,
        "utterances": utterances,
        "speakers": speaker_order,
        "log_id": log_id,
    }


def speaker_label_map(speaker_ids: list[str]) -> dict[str, str]:
    """Map raw speaker ids ('0','1',...) to labels ('A','B',...) by first appearance."""
    labels = {}
    for i, sid in enumerate(speaker_ids):
        labels[sid] = SPEAKER_LABELS[i % len(SPEAKER_LABELS)]
    return labels


# ── Subtitle engine (pure; unit-tested) ────────────────────────────────────

def _is_cjk(ch: str) -> bool:
    return bool(ch) and ord(ch) >= 0x2E80


def _char_weight(ch: str) -> float:
    return 1.0 if _is_cjk(ch) else 0.55


def text_weight(s: str) -> float:
    return sum(_char_weight(ch) for ch in s)


def _needs_space(prev: str, nxt: str) -> bool:
    """Whether a space should join two adjacent word tokens."""
    if not prev or not nxt:
        return False
    a, b = prev[-1], nxt[0]
    if _is_cjk(a) or _is_cjk(b):
        return False
    if a in "([{（【「『 \t" or b in ".,!?;:%)]}）】」』、。，；：！？":
        return False
    return True


def flatten_words(utterances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach each utterance's speaker to its words, in time order."""
    out: list[dict[str, Any]] = []
    for u in utterances:
        for w in u.get("words") or []:
            if not w.get("text", "").strip() or (w.get("start_ms", 0) < 0 and w.get("end_ms", 0) < 0):
                continue
            out.append({
                "text": w["text"],
                "start_ms": w["start_ms"],
                "end_ms": w["end_ms"],
                "speaker": u.get("speaker"),
            })
    return out


def utterances_to_proportional_words(utterances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fallback when the API returns no word timestamps: split utterance text
    on punctuation and distribute [start_ms, end_ms] by text weight."""
    out: list[dict[str, Any]] = []
    for u in utterances:
        text = u.get("text") or ""
        if not text.strip():
            continue
        pieces: list[str] = []
        buf = ""
        for ch in text:
            buf += ch
            if ch in SENTENCE_PUNCT | CLAUSE_PUNCT:
                pieces.append(buf)
                buf = ""
        if buf:
            pieces.append(buf)
        weights = [text_weight(p) for p in pieces]
        total = sum(weights) or 1.0
        cursor = float(u["start_ms"])
        span = max(0, u["end_ms"] - u["start_ms"])
        for piece, wgt in zip(pieces, weights):
            dur = span * (wgt / total)
            out.append({
                "text": piece.strip(),
                "start_ms": int(cursor),
                "end_ms": int(cursor + dur),
                "speaker": u.get("speaker"),
            })
            cursor += dur
    return out


def words_to_cues(
    words: list[dict[str, Any]],
    *,
    max_weight: float = DEFAULT_MAX_CUE_CHARS,
    max_duration_ms: int = int(DEFAULT_MAX_CUE_DURATION_S * 1000),
) -> list[dict[str, Any]]:
    """Group timestamped words into subtitle cues.

    Breaks, in priority order:
      1. speaker change / long silence gap
      2. sentence-ending punctuation (always)
      3. clause punctuation, once the cue is already reasonably long
      4. hard cap (max_weight * 1.5 / max_duration * 1.5) even mid-clause
    """
    cues: list[dict[str, Any]] = []
    buf: list[str] = []
    buf_start = 0
    buf_end = 0
    buf_speaker: Optional[str] = None
    buf_weight = 0.0

    def flush() -> None:
        nonlocal buf, buf_start, buf_end, buf_speaker, buf_weight
        text = "".join(buf).strip()
        if text:
            cues.append({
                "start_ms": buf_start,
                "end_ms": max(buf_end, buf_start + 200),
                "text": text,
                "speaker": buf_speaker,
            })
        buf = []
        buf_weight = 0.0

    for i, w in enumerate(words):
        token = w["text"]
        speaker = w.get("speaker")

        if buf:
            speaker_change = speaker != buf_speaker
            gap = w["start_ms"] - buf_end
            if speaker_change or gap > SPEAKER_GAP_MS:
                flush()

        if not buf:
            buf_start = w["start_ms"]
            buf_speaker = speaker
            buf.append(token)
        else:
            if _needs_space("".join(buf), token):
                buf.append(" ")
            buf.append(token)
        buf_end = w["end_ms"]
        buf_weight += text_weight(token)

        duration = buf_end - buf_start
        last = token[-1]
        hard_cap = (
            buf_weight >= max_weight * HARD_CUE_FACTOR
            or duration >= max_duration_ms * HARD_CUE_FACTOR
        )
        sentence_end = last in SENTENCE_PUNCT
        clause_end = (
            last in CLAUSE_PUNCT
            and (buf_weight >= MIN_CLAUSE_WEIGHT or duration >= MIN_CLAUSE_DURATION_MS)
        )
        soft_cap = buf_weight >= max_weight or duration >= max_duration_ms

        if sentence_end or clause_end or hard_cap or (soft_cap and last in CLAUSE_PUNCT | SENTENCE_PUNCT):
            flush()
        elif soft_cap and i == len(words) - 1:
            flush()

    flush()
    return cues


def fmt_srt_timestamp(ms: int) -> str:
    ms = max(0, int(ms))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, milli = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"


def fmt_vtt_timestamp(ms: int) -> str:
    return fmt_srt_timestamp(ms).replace(",", ".")


def _cue_text(text: str, speaker: Optional[str], labels: dict[str, str]) -> str:
    if speaker is not None and speaker in labels:
        return f"【发言人{labels[speaker]}】{text}"
    return text


def render_srt(cues: list[dict[str, Any]], labels: dict[str, str]) -> str:
    blocks = []
    for i, cue in enumerate(cues, 1):
        blocks.append(
            f"{i}\n"
            f"{fmt_srt_timestamp(cue['start_ms'])} --> {fmt_srt_timestamp(cue['end_ms'])}\n"
            f"{_cue_text(cue['text'], cue.get('speaker'), labels)}"
        )
    return "\n\n".join(blocks) + "\n"


def render_vtt(cues: list[dict[str, Any]], labels: dict[str, str]) -> str:
    blocks = ["WEBVTT"]
    for cue in cues:
        blocks.append(
            f"{fmt_vtt_timestamp(cue['start_ms'])} --> {fmt_vtt_timestamp(cue['end_ms'])}\n"
            f"{_cue_text(cue['text'], cue.get('speaker'), labels)}"
        )
    return "\n\n".join(blocks) + "\n"


def render_txt(utterances: list[dict[str, Any]], labels: dict[str, str]) -> str:
    lines = []
    for u in utterances:
        text = (u.get("text") or "").strip()
        if not text:
            continue
        speaker = u.get("speaker")
        if speaker is not None and speaker in labels:
            lines.append(f"发言人{labels[speaker]}：{text}")
        else:
            lines.append(text)
    return "\n".join(lines) + "\n"


# ── TTS meta reuse ─────────────────────────────────────────────────────────

def load_tts_meta(path: Path) -> dict[str, Any]:
    """Load a volcengine-tts .meta.json into the normalized transcript shape.

    TTS meta stores word timestamps in seconds (startTime/endTime); ASR uses
    milliseconds. No speaker info exists for synthesized narration.
    """
    meta = json.loads(path.read_text(encoding="utf-8"))
    words = []
    for w in meta.get("words") or []:
        try:
            start = int(round(float(w["startTime"]) * 1000))
            end = int(round(float(w["endTime"]) * 1000))
        except (KeyError, TypeError, ValueError):
            continue
        words.append({
            "text": w.get("word", ""),
            "start_ms": start,
            "end_ms": end,
            "confidence": w.get("confidence", 0),
        })
    text = meta.get("sentence_text") or meta.get("text") or ""
    duration_ms = int(meta.get("duration_ms") or 0)
    if not duration_ms and words:
        duration_ms = words[-1]["end_ms"]
    utterance = {
        "text": text.strip(),
        "start_ms": words[0]["start_ms"] if words else 0,
        "end_ms": words[-1]["end_ms"] if words else duration_ms,
        "speaker": None,
        "channel": None,
        "words": words,
    }
    return {
        "text": text.strip(),
        "duration_ms": duration_ms,
        "utterances": [utterance] if words else [],
        "speakers": [],
        "log_id": "",
        "source": "tts-meta",
    }


# ── Output writing ─────────────────────────────────────────────────────────

def default_output_stem(*, source: Optional[Path] = None, tts_meta: Optional[Path] = None) -> tuple[Path, str]:
    """(output_dir, stem) for subtitle files written alongside the source."""
    base = tts_meta if tts_meta is not None else source
    assert base is not None
    name = base.name
    if name.endswith(".meta.json"):
        name = name[: -len(".meta.json")]
    else:
        name = base.stem
    return base.parent, name


def resolve_output_path(spec: Any, out_dir: Path, stem: str, ext: str) -> Optional[Path]:
    """Flag spec: False (absent), True (present without value -> default), or path."""
    if spec is False:
        return None
    if spec is True:
        return out_dir / f"{stem}.{ext}"
    return Path(spec)


# ── CLI ────────────────────────────────────────────────────────────────────

def parse_hotwords(raw: Optional[str]) -> Optional[list[str]]:
    if not raw:
        return None
    seen: set[str] = set()
    out: list[str] = []
    for w in raw.replace("，", ",").split(","):
        w = w.strip()
        if w and w not in seen:
            seen.add(w)
            out.append(w)
    return out[:100] or None


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="volcengine-asr",
        description="Volcengine Doubao ASR — transcribe audio/video to text and SRT/VTT subtitles",
    )
    parser.add_argument("input", nargs="?", help="Local audio/video file or http(s) URL")
    parser.add_argument(
        "--mode", choices=["auto", "flash", "standard"], default="auto",
        help="flash (default, sync, <=2h/100MB, local files) or standard (async, URL only, <=5h/512MB)",
    )
    parser.add_argument("--audio-url", help="Public audio URL (alternative to positional input)")
    parser.add_argument(
        "--from-tts-meta", type=Path,
        help="Skip ASR: build subtitles from a volcengine-tts .meta.json word-timestamp file",
    )

    parser.add_argument("--srt", nargs="?", const=True, default=False, help="Write SRT (default path: <stem>.srt next to input)")
    parser.add_argument("--vtt", nargs="?", const=True, default=False, help="Write WebVTT (<stem>.vtt)")
    parser.add_argument("--txt", nargs="?", const=True, default=False, help="Write plain transcript (<stem>.txt)")
    parser.add_argument("--transcript-json", nargs="?", const=True, default=False, help="Write full JSON transcript (<stem>.transcript.json)")
    parser.add_argument("-o", "--output-dir", type=Path, help="Directory for output files (default: next to input)")

    parser.add_argument("--language", help="Language code, e.g. zh-CN / en-US / ja-JP. Omit for auto-detect (zh/en + Chinese dialects).")
    parser.add_argument("--diarize", action="store_true", help="Enable speaker diarization (labels 【发言人A/B】 in subtitles)")
    parser.add_argument("--meeting", action="store_true", help="Meeting mode: voiceprint diarization (ssd_version=300) for long multi-speaker recordings; implies --diarize")
    parser.add_argument("--hotwords", help="Comma-separated hotwords to boost recognition, e.g. '豆包,火山引擎,Seedance'")

    parser.add_argument("--max-cue-chars", type=float, default=DEFAULT_MAX_CUE_CHARS, help="Max weighted chars per subtitle cue (default 20)")
    parser.add_argument("--max-cue-duration", type=float, default=DEFAULT_MAX_CUE_DURATION_S, help="Max seconds per subtitle cue (default 7)")

    parser.add_argument("--poll-interval", type=int, default=5, help="Standard mode poll interval in seconds (default 5)")
    parser.add_argument("--timeout", type=int, default=1800, help="Standard mode max wait in seconds (default 1800)")
    parser.add_argument("--keep-extracted-audio", action="store_true", help="Keep the ffmpeg-extracted 16k mono mp3 instead of deleting it")

    args = parser.parse_args()

    hotwords = parse_hotwords(args.hotwords)
    max_duration_ms = int(args.max_cue_duration * 1000)
    used_mode = "flash"

    # ── TTS meta mode (no API call) ──
    if args.from_tts_meta:
        meta_path = args.from_tts_meta
        if not meta_path.exists():
            die(f"TTS meta file not found: {meta_path}")
        transcript = load_tts_meta(meta_path)
        if not transcript["utterances"] or not transcript["utterances"][0]["words"]:
            die(f"No word timestamps in {meta_path}. Regenerate the TTS audio without --no-subtitle.")
        source_path = meta_path
        source_url = None
        used_mode = "tts-meta"
    else:
        source = args.audio_url or args.input
        if not source:
            die("Provide an input file/URL, or use --from-tts-meta <file.meta.json>")

        api_key = load_api_key()

        if is_url(source):
            source_url = source
            source_path = None
            fmt = Path(source.split("?")[0]).suffix.lstrip(".").lower() or "mp3"
            mode = args.mode
            if mode == "auto":
                mode = "flash"  # flash accepts URLs too and is synchronous
            used_mode = mode
            if mode == "flash":
                transcript = recognize_flash(
                    api_key=api_key, audio_url=source_url, language=args.language,
                    audio_format=fmt, diarize=args.diarize or args.meeting,
                    meeting=args.meeting, hotwords=hotwords,
                )
            else:
                transcript = recognize_standard(
                    api_key=api_key, audio_url=source_url, audio_format=fmt,
                    language=args.language, diarize=args.diarize or args.meeting,
                    meeting=args.meeting, hotwords=hotwords,
                    poll_interval=args.poll_interval, timeout_s=args.timeout,
                )
        else:
            source_path = Path(source).expanduser().resolve()
            if not source_path.exists():
                die(f"Input file not found: {source_path}")

            upload_path, temp_path = prepare_local_media(
                source_path, keep_extracted=args.keep_extracted_audio
            )
            used_mode = "flash"
            try:
                use_standard = args.mode == "standard"
                if args.mode == "auto" and flash_limit_reason(upload_path):
                    print(
                        f"Over flash limits ({flash_limit_reason(upload_path)}); "
                        f"using standard async mode.",
                        file=sys.stderr,
                    )
                    use_standard = True

                if use_standard:
                    used_mode = "standard"
                    upload_fmt = upload_path.suffix.lstrip(".").lower() or "mp3"
                    transcript = recognize_standard(
                        api_key=api_key, audio_path=upload_path, audio_format=upload_fmt,
                        language=args.language, diarize=args.diarize or args.meeting,
                        meeting=args.meeting, hotwords=hotwords,
                        poll_interval=args.poll_interval, timeout_s=args.timeout,
                    )
                else:
                    check_flash_limits(upload_path)
                    transcript = recognize_flash(
                        api_key=api_key, audio_path=upload_path, language=args.language,
                        diarize=args.diarize or args.meeting,
                        meeting=args.meeting, hotwords=hotwords,
                    )
            finally:
                if temp_path is not None:
                    temp_path.unlink(missing_ok=True)
            source_url = None

    if transcript.get("error"):
        print(json.dumps(transcript, ensure_ascii=False, indent=2))
        sys.exit(1)

    # ── Build cues ──
    words = flatten_words(transcript["utterances"])
    if not words:
        words = utterances_to_proportional_words(transcript["utterances"])
    cues = words_to_cues(
        words, max_weight=args.max_cue_chars, max_duration_ms=max_duration_ms
    )
    labels = speaker_label_map(transcript.get("speakers", []))

    # ── Write outputs ──
    if args.from_tts_meta:
        out_dir_default, stem = default_output_stem(tts_meta=args.from_tts_meta)
    elif source_path is not None:
        out_dir_default, stem = default_output_stem(source=source_path)
    else:
        out_dir_default, stem = Path.cwd(), f"asr-{uuid.uuid4().hex[:8]}"
    out_dir = args.output_dir or out_dir_default
    if args.output_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    # Default: with no format flags, write SRT (the common case: "生成字幕").
    if not any([args.srt, args.vtt, args.txt, args.transcript_json]):
        args.srt = True

    outputs: dict[str, str] = {}
    for flag, ext, renderer, payload in [
        (args.srt, "srt", render_srt, (cues, labels)),
        (args.vtt, "vtt", render_vtt, (cues, labels)),
        (args.txt, "txt", render_txt, (transcript["utterances"], labels)),
    ]:
        path = resolve_output_path(flag, out_dir, stem, ext)
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(renderer(*payload), encoding="utf-8")
            outputs[ext] = str(path)

    json_path = resolve_output_path(args.transcript_json, out_dir, stem, "transcript.json")
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(
                {
                    "source": str(source_path) if source_path else source_url,
                    "mode": used_mode,
                    **{k: v for k, v in transcript.items() if k != "error"},
                    "cues": cues,
                    "speaker_labels": labels,
                },
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
        outputs["transcript_json"] = str(json_path)

    summary = {
        "source": str(source_path) if source_path else source_url,
        "mode": used_mode,
        "duration_ms": transcript.get("duration_ms", 0),
        "text": transcript.get("text", ""),
        "utterances": len(transcript.get("utterances", [])),
        "cues": len(cues),
        "speakers": [f"发言人{labels[sid]}" for sid in transcript.get("speakers", []) if sid in labels],
        "outputs": outputs,
        "log_id": transcript.get("log_id", ""),
        "error": None,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not transcript.get("text") and not args.from_tts_meta:
        print("Note: transcript is empty (silent audio or no speech detected).", file=sys.stderr)


if __name__ == "__main__":
    main()
