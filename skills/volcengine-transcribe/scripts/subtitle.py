#!/usr/bin/env -S uv run
"""Render normalized Volcengine transcripts as SRT, VTT, or TXT."""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any, Optional

SCHEMA_VERSION = 1
DEFAULT_MAX_CUE_CHARS = 20
DEFAULT_MAX_CUE_DURATION_S = 7.0
MIN_CLAUSE_WEIGHT = 10
MIN_CLAUSE_DURATION_MS = 2500
HARD_CUE_FACTOR = 1.5
SPEAKER_GAP_MS = 1200
SENTENCE_PUNCT = set("。！？!?；;…\n.")
CLAUSE_PUNCT = set("，,、：:")
SPEAKER_LABELS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _is_punct(ch: str) -> bool:
    return unicodedata.category(ch).startswith("P")


def reinsert_punctuation(text: str, words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Align punctuation from utterance text onto timestamped word tokens."""
    if not words:
        return words
    out = [dict(word) for word in words]
    pos = 0
    last_aligned_i = -1
    for i, word in enumerate(out):
        token = word.get("text") or ""
        if not token:
            continue
        idx = text.find(token, pos)
        if idx == -1:
            continue
        between = "".join(ch for ch in text[pos:idx] if _is_punct(ch))
        if between:
            target = out[i - 1] if i > 0 else out[i]
            target["text"] = (
                target["text"] + between if i > 0 else between + target["text"]
            )
        pos = idx + len(token)
        last_aligned_i = i
    if last_aligned_i == len(out) - 1:
        tail = "".join(ch for ch in text[pos:] if _is_punct(ch))
        if tail:
            out[-1]["text"] += tail
    return out


def normalize_result(body: dict[str, Any], *, log_id: str = "") -> dict[str, Any]:
    """Normalize the provider response into the versioned transcript contract."""
    result = body.get("result") or {}
    additions = result.get("additions") or {}
    audio_info = body.get("audio_info") or {}
    duration_ms = 0
    for source in (audio_info.get("duration"), additions.get("duration")):
        try:
            if source:
                duration_ms = int(float(source))
                break
        except (TypeError, ValueError):
            pass

    utterances: list[dict[str, Any]] = []
    speaker_order: list[str] = []
    for utterance in result.get("utterances") or []:
        utterance_additions = utterance.get("additions") or {}
        speaker = utterance_additions.get("speaker")
        if speaker is not None:
            speaker = str(speaker)
            if speaker not in speaker_order:
                speaker_order.append(speaker)
        words = []
        for word in utterance.get("words") or []:
            word_text = word.get("text", "")
            start_ms = int(word.get("start_time", 0))
            end_ms = int(word.get("end_time", 0))
            if not word_text.strip() or (start_ms < 0 and end_ms < 0):
                continue
            words.append(
                {
                    "text": word_text,
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "confidence": word.get("confidence", 0),
                    "blank_duration_ms": int(word.get("blank_duration", 0) or 0),
                }
            )
        words = reinsert_punctuation(utterance.get("text") or "", words)
        utterances.append(
            {
                "text": (utterance.get("text") or "").strip(),
                "start_ms": int(utterance.get("start_time", 0)),
                "end_ms": int(utterance.get("end_time", 0)),
                "speaker": speaker,
                "channel": utterance_additions.get("channel_id"),
                "words": words,
            }
        )

    text = result.get("text") or "".join(item["text"] for item in utterances)
    return {
        "schema_version": SCHEMA_VERSION,
        "text": text.strip(),
        "duration_ms": duration_ms,
        "utterances": utterances,
        "speakers": speaker_order,
        "log_id": log_id,
    }


def speaker_label_map(speaker_ids: list[str]) -> dict[str, str]:
    return {
        speaker_id: SPEAKER_LABELS[i % len(SPEAKER_LABELS)]
        for i, speaker_id in enumerate(speaker_ids)
    }


def _is_cjk(ch: str) -> bool:
    return bool(ch) and ord(ch) >= 0x2E80


def _char_weight(ch: str) -> float:
    return 1.0 if _is_cjk(ch) else 0.55


def text_weight(text: str) -> float:
    return sum(_char_weight(ch) for ch in text)


def _needs_space(previous: str, following: str) -> bool:
    if not previous or not following:
        return False
    left, right = previous[-1], following[0]
    if _is_cjk(left) or _is_cjk(right):
        return False
    if left in "([{（【「『 \t" or right in ".,!?;:%)]}）】」』、。，；：！？":
        return False
    return True


def flatten_words(utterances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for utterance in utterances:
        for word in utterance.get("words") or []:
            if not word.get("text", "").strip():
                continue
            if word.get("start_ms", 0) < 0 and word.get("end_ms", 0) < 0:
                continue
            out.append(
                {
                    "text": word["text"],
                    "start_ms": word["start_ms"],
                    "end_ms": word["end_ms"],
                    "speaker": utterance.get("speaker"),
                }
            )
    return out


def utterances_to_proportional_words(
    utterances: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for utterance in utterances:
        text = utterance.get("text") or ""
        if not text.strip():
            continue
        pieces: list[str] = []
        buffer = ""
        for char in text:
            buffer += char
            if char in SENTENCE_PUNCT | CLAUSE_PUNCT:
                pieces.append(buffer)
                buffer = ""
        if buffer:
            pieces.append(buffer)
        weights = [text_weight(piece) for piece in pieces]
        total = sum(weights) or 1.0
        cursor = float(utterance["start_ms"])
        span = max(0, utterance["end_ms"] - utterance["start_ms"])
        for piece, weight in zip(pieces, weights):
            duration = span * (weight / total)
            out.append(
                {
                    "text": piece.strip(),
                    "start_ms": int(cursor),
                    "end_ms": int(cursor + duration),
                    "speaker": utterance.get("speaker"),
                }
            )
            cursor += duration
    return out


def words_to_cues(
    words: list[dict[str, Any]],
    *,
    max_weight: float = DEFAULT_MAX_CUE_CHARS,
    max_duration_ms: int = int(DEFAULT_MAX_CUE_DURATION_S * 1000),
) -> list[dict[str, Any]]:
    cues: list[dict[str, Any]] = []
    buffer: list[str] = []
    buffer_start = 0
    buffer_end = 0
    buffer_speaker: Optional[str] = None
    buffer_weight = 0.0

    def flush() -> None:
        nonlocal buffer, buffer_start, buffer_end, buffer_speaker, buffer_weight
        text = "".join(buffer).strip()
        if text:
            cues.append(
                {
                    "start_ms": buffer_start,
                    "end_ms": max(buffer_end, buffer_start + 200),
                    "text": text,
                    "speaker": buffer_speaker,
                }
            )
        buffer = []
        buffer_weight = 0.0

    for index, word in enumerate(words):
        token = word["text"]
        speaker = word.get("speaker")
        if buffer:
            speaker_change = speaker != buffer_speaker
            gap = word["start_ms"] - buffer_end
            if speaker_change or gap > SPEAKER_GAP_MS:
                flush()

        if not buffer:
            buffer_start = word["start_ms"]
            buffer_speaker = speaker
            buffer.append(token)
        else:
            if _needs_space("".join(buffer), token):
                buffer.append(" ")
            buffer.append(token)
        buffer_end = word["end_ms"]
        buffer_weight += text_weight(token)

        duration = buffer_end - buffer_start
        last = token[-1]
        hard_cap = (
            buffer_weight >= max_weight * HARD_CUE_FACTOR
            or duration >= max_duration_ms * HARD_CUE_FACTOR
        )
        sentence_end = last in SENTENCE_PUNCT
        clause_end = last in CLAUSE_PUNCT and (
            buffer_weight >= MIN_CLAUSE_WEIGHT or duration >= MIN_CLAUSE_DURATION_MS
        )
        soft_cap = buffer_weight >= max_weight or duration >= max_duration_ms
        if sentence_end or clause_end or hard_cap:
            flush()
        elif soft_cap and index == len(words) - 1:
            flush()

    flush()
    return cues


def fmt_srt_timestamp(milliseconds: int) -> str:
    milliseconds = max(0, int(milliseconds))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def fmt_vtt_timestamp(milliseconds: int) -> str:
    return fmt_srt_timestamp(milliseconds).replace(",", ".")


def _cue_text(text: str, speaker: Optional[str], labels: dict[str, str]) -> str:
    if speaker is not None and speaker in labels:
        return f"【发言人{labels[speaker]}】{text}"
    return text


def render_srt(cues: list[dict[str, Any]], labels: dict[str, str]) -> str:
    blocks = []
    for index, cue in enumerate(cues, 1):
        blocks.append(
            f"{index}\n"
            f"{fmt_srt_timestamp(cue['start_ms'])} --> "
            f"{fmt_srt_timestamp(cue['end_ms'])}\n"
            f"{_cue_text(cue['text'], cue.get('speaker'), labels)}"
        )
    return "\n\n".join(blocks) + "\n"


def render_vtt(cues: list[dict[str, Any]], labels: dict[str, str]) -> str:
    blocks = ["WEBVTT"]
    for cue in cues:
        blocks.append(
            f"{fmt_vtt_timestamp(cue['start_ms'])} --> "
            f"{fmt_vtt_timestamp(cue['end_ms'])}\n"
            f"{_cue_text(cue['text'], cue.get('speaker'), labels)}"
        )
    return "\n\n".join(blocks) + "\n"


def render_txt(utterances: list[dict[str, Any]], labels: dict[str, str]) -> str:
    lines = []
    for utterance in utterances:
        text = (utterance.get("text") or "").strip()
        if not text:
            continue
        speaker = utterance.get("speaker")
        if speaker is not None and speaker in labels:
            lines.append(f"发言人{labels[speaker]}：{text}")
        else:
            lines.append(text)
    return "\n".join(lines) + "\n"


def load_tts_meta(path: Path) -> dict[str, Any]:
    meta = json.loads(path.read_text(encoding="utf-8"))
    words = []
    for word in meta.get("words") or []:
        try:
            start = int(round(float(word["startTime"]) * 1000))
            end = int(round(float(word["endTime"]) * 1000))
        except (KeyError, TypeError, ValueError):
            continue
        words.append(
            {
                "text": word.get("word", ""),
                "start_ms": start,
                "end_ms": end,
                "confidence": word.get("confidence", 0),
            }
        )
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
        "schema_version": SCHEMA_VERSION,
        "text": text.strip(),
        "duration_ms": duration_ms,
        "utterances": [utterance] if words else [],
        "speakers": [],
        "log_id": "",
        "source": "tts-meta",
    }


def default_output_stem(
    *, source: Optional[Path] = None, tts_meta: Optional[Path] = None
) -> tuple[Path, str]:
    base = tts_meta if tts_meta is not None else source
    assert base is not None
    name = base.name
    if name.endswith(".meta.json"):
        name = name[: -len(".meta.json")]
    elif name.endswith(".transcript.json"):
        name = name[: -len(".transcript.json")]
    else:
        name = base.stem
    return base.parent, name


def resolve_output_path(spec: Any, out_dir: Path, stem: str, extension: str) -> Optional[Path]:
    if spec is False:
        return None
    if spec is True:
        return out_dir / f"{stem}.{extension}"
    return Path(spec)


def build_cues(
    transcript: dict[str, Any], *, max_weight: float, max_duration_ms: int
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    words = flatten_words(transcript.get("utterances", []))
    if not words:
        words = utterances_to_proportional_words(transcript.get("utterances", []))
    cues = words_to_cues(words, max_weight=max_weight, max_duration_ms=max_duration_ms)
    labels = speaker_label_map(transcript.get("speakers", []))
    return cues, labels


def validate_transcript_shape(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("transcript JSON must contain an object")
    if not isinstance(value.get("utterances"), list):
        raise ValueError("transcript JSON must contain an 'utterances' array")
    for index, utterance in enumerate(value["utterances"]):
        if not isinstance(utterance, dict):
            raise ValueError(f"transcript utterances[{index}] must be an object")
        words = utterance.get("words", [])
        if not isinstance(words, list):
            raise ValueError(f"transcript utterances[{index}].words must be an array")
        for word_index, word in enumerate(words):
            if not isinstance(word, dict):
                raise ValueError(
                    f"transcript utterances[{index}].words[{word_index}] must be an object"
                )
    speakers = value.get("speakers", [])
    if not isinstance(speakers, list):
        raise ValueError("transcript JSON 'speakers' must be an array")
    return value


def write_outputs(
    transcript: dict[str, Any],
    *,
    out_dir: Path,
    stem: str,
    srt: Any = False,
    vtt: Any = False,
    txt: Any = False,
    max_weight: float = DEFAULT_MAX_CUE_CHARS,
    max_duration_ms: int = int(DEFAULT_MAX_CUE_DURATION_S * 1000),
) -> tuple[dict[str, str], list[dict[str, Any]], dict[str, str]]:
    cues, labels = build_cues(
        transcript, max_weight=max_weight, max_duration_ms=max_duration_ms
    )
    outputs: dict[str, str] = {}
    for flag, extension, renderer, payload in (
        (srt, "srt", render_srt, (cues, labels)),
        (vtt, "vtt", render_vtt, (cues, labels)),
        (txt, "txt", render_txt, (transcript.get("utterances", []), labels)),
    ):
        path = resolve_output_path(flag, out_dir, stem, extension)
        if path is None:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(renderer(*payload), encoding="utf-8")
        outputs[extension] = str(path)
    return outputs, cues, labels


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a saved Volcengine transcript as subtitles"
    )
    parser.add_argument("transcript", type=Path, help="Normalized .transcript.json file")
    parser.add_argument("--srt", nargs="?", const=True, default=False)
    parser.add_argument("--vtt", nargs="?", const=True, default=False)
    parser.add_argument("--txt", nargs="?", const=True, default=False)
    parser.add_argument("-o", "--output-dir", type=Path)
    parser.add_argument("--max-cue-chars", type=float, default=DEFAULT_MAX_CUE_CHARS)
    parser.add_argument("--max-cue-duration", type=float, default=DEFAULT_MAX_CUE_DURATION_S)
    args = parser.parse_args()

    try:
        transcript = json.loads(args.transcript.read_text(encoding="utf-8"))
        if isinstance(transcript, dict) and "transcript" in transcript:
            transcript = transcript["transcript"]
        transcript = validate_transcript_shape(transcript)
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1) from exc

    out_dir, stem = default_output_stem(source=args.transcript)
    out_dir = args.output_dir or out_dir
    if not any((args.srt, args.vtt, args.txt)):
        args.srt = True
    outputs, cues, _ = write_outputs(
        transcript,
        out_dir=out_dir,
        stem=stem,
        srt=args.srt,
        vtt=args.vtt,
        txt=args.txt,
        max_weight=args.max_cue_chars,
        max_duration_ms=int(args.max_cue_duration * 1000),
    )
    print(json.dumps({"cues": len(cues), "outputs": outputs}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
