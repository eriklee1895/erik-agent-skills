---
name: volcengine-asr
description: >
  Transcribe audio and video to text using Volcano Engine's (火山引擎) Doubao speech recognition (豆包录音文件识别大模型), with SRT/VTT subtitle generation.
  Use this skill whenever the user needs speech-to-text, ASR, transcription, captions/subtitles, 语音识别, 语音转文字, 录音转写, 转录, 听写, 会议纪要转文字, 生成字幕, SRT, VTT, or subtitle files from audio/video.
  Also use when the user mentions 火山引擎 ASR, 豆包语音识别, volcengine speech recognition, or needs subtitles for a video/podcast/meeting recording.
  Speaker diarization (说话人分离, 发言人 A/B labels) and video audio-track extraction (ffmpeg) are built in.
  This skill should ALWAYS be used for any ASR/字幕生成 task — never call the Volcano Engine recognition API directly without it.
---

# Volcengine ASR

Transcribe audio/video files to text and generate subtitles (SRT / VTT / TXT / JSON) using Volcano Engine's Doubao audio-file recognition (豆包录音文件识别).

The same `VOLC_SPEECH_API_KEY` as `volcengine-tts` is used — TTS and ASR share one speech-console API key.

## Quick Start

```bash
# Transcribe an audio/video file; default output is an SRT next to the input
uv run scripts/volcengine-asr.py meeting.mp3

# All subtitle formats + full JSON transcript
uv run scripts/volcengine-asr.py interview.mp4 --srt --vtt --txt --transcript-json

# Speaker diarization (labels 【发言人A】/【发言人B】 in the subtitles)
uv run scripts/volcengine-asr.py meeting.m4a --diarize --srt
# Long multi-speaker meetings: voiceprint matching mode
uv run scripts/volcengine-asr.py townhall.mp3 --meeting --srt

# Boost domain vocabulary recognition
uv run scripts/volcengine-asr.py talk.wav --hotwords "豆包,火山引擎,Seedance" --srt

# Subtitles for TTS-narrated audio WITHOUT re-recognizing — reuse the
# word timestamps volcengine-tts already produced (free, instant, exact)
uv run scripts/volcengine-asr.py --from-tts-meta tts-output/tts_20260904_001.meta.json --srt --vtt

# Public URL inputs or long recordings (--mode standard handles both;
# local files over 2 h auto-route to standard in --mode auto)
uv run scripts/volcengine-asr.py https://example.com/long.mp3 --mode standard --srt
```

## Script

The core implementation is `scripts/volcengine-asr.py` — a PEP 723 inline-dependency Python script.

**Always run with `uv run`** — it auto-creates an isolated environment from the inline metadata. Never use bare `python` or `pip`.

Video files (`.mp4/.mov/.mkv/...`) and oversized/non-native audio are converted with **ffmpeg** to 16 kHz mono MP3 before upload. Install ffmpeg if missing (`brew install ffmpeg`).

## Two Recognition Modes

| | flash (default) | standard (`--mode standard`) |
|---|---|---|
| Call | One synchronous request | Submit + poll until done |
| Local files (base64) | ✅ works (documented in the older doc page; the newer 2026-08 pages only show URL, but data upload verified working) | ✅ works (undocumented in current docs; verified live + used in production by other tooling) |
| Public URLs | ✅ documented | ✅ documented |
| Limits | ≤ 2 h, ≤ 100 MB | ≤ 5 h, ≤ 512 MB (URL audio) |
| Resource | `volc.bigasr.auc_turbo` | `volc.seedasr.auc` (2.0) |

Base64 upload needs no object storage and is the default for local files; if Volcano ever retires it, passing an `http(s)` input (or `--audio-url`) uses the documented URL path instead.

Almost every case uses flash: a 2 h video extracts to a ~60 MB or smaller mono MP3, well inside the limits. `--mode auto` (default) automatically falls back to standard when a prepared local file exceeds flash limits — no action needed for long recordings. **Each resource must be enabled separately in the speech console** — an auth error on one mode does not imply the key is wrong.

### Timing accuracy for video sources

Audio extraction uses `ffmpeg -af aresample=async=1:first_pts=0`: PTS gaps in the source (recording pauses, concatenated clips, re-muxed streams) are filled with silence so subtitle timestamps stay aligned to the video timeline. Without it, gaps get squashed out and subtitles drift cumulatively (a real 31-min clip drifted 8.5 s). It is a no-op for clean sources.

## Environment Setup

The script reads `VOLC_SPEECH_API_KEY` with three-level fallback:
1. `VOLC_SPEECH_API_KEY` environment variable
2. `.env` file in the current working directory
3. `~/.volcengine.env` (user-level config)

Get the key at the speech console: https://console.volcengine.com/speech/new/setting/apikeys
Note: the speech API key is **not** the same as the Volcano Ark (方舟) key used by image/video skills.

## CLI Reference

```
uv run scripts/volcengine-asr.py <audio-or-video-file | URL> [options]
```

### Output flags

| Flag | Default | Description |
|------|---------|-------------|
| `--srt [PATH]` | on by default | Write SubRip subtitles. Flag alone → `<stem>.srt` next to input |
| `--vtt [PATH]` | off | Write WebVTT subtitles (`<stem>.vtt`) |
| `--txt [PATH]` | off | Write plain transcript, speaker-prefixed when diarized |
| `--transcript-json [PATH]` | off | Full machine-readable transcript (utterances, word timestamps, speakers) |
| `-o, --output-dir DIR` | alongside input | Directory for output files |

With no output flags, SRT is written (the common "生成字幕" case). The full result JSON is always printed to stdout.

### Recognition options

| Flag | Default | Description |
|------|---------|-------------|
| `--mode auto\|flash\|standard` | `auto` | `auto` → flash, falling back to standard automatically when the prepared file exceeds flash limits; `standard` forces async submit/poll |
| `--audio-url URL` | — | Public audio URL (alternative to positional input) |
| `--from-tts-meta FILE` | — | Skip ASR: build subtitles from a `volcengine-tts` `.meta.json` (word timestamps in seconds) |
| `--language CODE` | auto-detect | `zh-CN`, `en-US`, `ja-JP`, `ko-KR`, `yue-CN`(粤语), … Omit for auto (zh/en + Chinese dialects) |
| `--diarize` | off | Speaker diarization; subtitles prefixed 【发言人A/B】(only effective for Chinese/auto language) |
| `--meeting` | off | Long-meeting voiceprint diarization (`ssd_version=300`); implies `--diarize` |
| `--hotwords "词1,词2"` | — | Comma-separated hotwords to boost recognition (domain terms, names) |
| `--max-cue-chars N` | 20 | Max weighted chars per subtitle cue (CJK = 1, latin ≈ 0.55) |
| `--max-cue-duration S` | 7 | Max seconds per subtitle cue |
| `--poll-interval S` | 5 | Standard mode poll interval |
| `--timeout S` | 1800 | Standard mode max wait |
| `--keep-extracted-audio` | off | Keep the ffmpeg-extracted 16 kHz mono MP3 instead of deleting it |

### Cue splitting behavior

Word-level timestamps drive subtitle grouping. Cues break on:
1. Speaker change or a silence gap > 1.2 s
2. Sentence-ending punctuation (。！？!?；;…)
3. Clause punctuation (，、,) once the cue is already ~10+ chars / 2.5 s long
4. Hard length cap (~30 weighted chars / 10.5 s) even mid-clause

Punctuation note: the API returns punctuation only in utterance text, not on word tokens — the script re-aligns punctuation onto word boundaries before grouping.

## Output Format

### stdout (success)

```json
{
  "source": "/path/to/meeting.mp4",
  "mode": "flash",
  "duration_ms": 6312,
  "text": "整段转写文本……",
  "utterances": 12,
  "cues": 18,
  "speakers": ["发言人A", "发言人B"],
  "outputs": {
    "srt": "/path/to/meeting.srt",
    "vtt": "/path/to/meeting.vtt"
  },
  "log_id": "202609041651416AAD46CC9EAD8F25D925",
  "error": null
}
```

### SRT (with diarization)

```
1
00:00:00,280 --> 00:00:02,600
【发言人A】你好，这是一段语音识别测试。
```

### Silent / no-speech audio

Status `20000003` is treated as success with an empty transcript (exit 0, stderr note) — not an error.

### Errors

Errors are JSON (`{"error": "..."}`) on stderr with non-zero exit. Always include `log_id` when escalating. HTTP 401/403 and `45xxxxxx` parameter errors are non-retryable; `429/5xx`, `55000031` (overloaded) and `550xxxxx` auto-retry with exponential backoff. Full code table and parameters: `references/volcengine-asr-api-docs.md`.

## When to Use This Skill

- User asks to transcribe/转写/转录 audio or video, generate 字幕/SRT/VTT
- User has meeting recordings, interviews, podcasts, voice memos to turn into text
- User mentions 火山引擎 ASR, 豆包语音识别, volcengine speech-to-text
- User needs speaker-labeled transcripts (`--diarize` / `--meeting`)
- A TTS-narrated video needs subtitles — prefer `--from-tts-meta` over ASR (instant, exact alignment, no extra recognition cost)

## When NOT to Use

- Real-time / streaming recognition or one-shot dictation (<60 s live audio) — different WebSocket API
- Text-to-speech / 配音 / TTS — use `volcengine-tts`
- Music generation or audio editing — not ASR
