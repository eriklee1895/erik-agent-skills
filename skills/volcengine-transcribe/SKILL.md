---
name: volcengine-transcribe
description: Use whenever the user asks to transcribe audio or video, convert speech to text (ASR/STT), generate word-level timestamps or SRT/VTT subtitles, or diarize speakers with Volcano Engine Doubao ASR.
---

# Volcengine Transcribe

Use Volcano Engine's latest Doubao audio-file recognition 2.0 standard model
(`volc.seedasr.auc`) for high-quality transcription and subtitle generation.

## Quick start

```bash
# Local audio/video: writes meeting.srt and meeting.transcript.json
uv run scripts/volcengine-transcribe.py meeting.mp4

# Public audio URL
uv run scripts/volcengine-transcribe.py \
  'https://example.com/interview.mp3' --srt --vtt --txt

# Speaker diarization
uv run scripts/volcengine-transcribe.py meeting.m4a --meeting --srt

# Domain vocabulary
uv run scripts/volcengine-transcribe.py talk.wav \
  --hotwords '豆包,火山引擎,Seedance' --srt

# Full corpus context (dialog history, scene context, and hotwords)
uv run scripts/volcengine-transcribe.py talk.wav \
  --context-json context.json --srt

# Word/character timestamps only, for HyperFrames or custom renderers
uv run scripts/volcengine-transcribe.py video.mp4 --transcript-only

# Re-render a saved transcript without another ASR request
uv run scripts/subtitle.py meeting.transcript.json \
  --srt meeting-short.srt --max-cue-chars 16

# Reuse exact word timestamps produced by volcengine-tts
uv run scripts/volcengine-transcribe.py \
  --from-tts-meta tts-output/tts_001.meta.json --srt --vtt
```

Always run the scripts with `uv run`. Video extraction and non-native audio
conversion require `ffmpeg` and `ffprobe`.

## Implementation boundary

- `scripts/volcengine-transcribe.py`: stable one-command entrypoint.
- `scripts/transcribe.py`: media preparation, ASR 2.0 submit/query, response
  normalization, and workflow orchestration.
- `scripts/subtitle.py`: pure transcript-to-cue conversion and SRT/VTT/TXT
  rendering. It can run independently on a saved transcript.

The normalized `.transcript.json` is the reusable boundary. Prefer re-rendering
that file when adjusting subtitle length or format; do not pay for ASR again.

## API and model

The skill intentionally exposes only the standard 2.0 model:

| Item | Value |
|---|---|
| Resource | `volc.seedasr.auc` |
| Submit | `POST /api/v3/auc/bigmodel/submit` |
| Query | `POST /api/v3/auc/bigmodel/query` |
| Limits | 5 hours / 512 MB |
| Model | Doubao audio-file recognition 2.0 |

Submission is asynchronous. When the response contains `task_id`, the script
passes that value as `X-Api-Request-Id` when querying. The retained legacy
`audio.data` path may return `{}` instead; in that case the script falls back to
the submission request UUID, which the current service accepts for querying.

### Local file compatibility

The legacy recording-file API formally documented local binary/base64 upload
through `audio.data`. The current 2.0 documentation shows only `audio.url`, but
the current service retains `audio.data` compatibility and it has been verified
with `volc.seedasr.auc`.

Therefore:

- HTTP(S) inputs use the currently documented `audio.url` path.
- Local inputs use the retained `audio.data` base64 path.
- Video, non-native audio, and large local audio are converted to 16 kHz mono
  MP3 before encoding to keep requests smaller.
- `.raw` inputs are accepted when they are the documented 16 kHz, 16-bit, mono
  raw PCM form; otherwise provide an explicit conversion.

Do not describe local base64 as part of the new written API contract. Describe
it as a legacy-documented compatibility capability retained by the 2.0 service.

### Full context

Pass a JSON file containing the object serialized into `corpus.context`:

```json
{
  "hotwords": [{"word": "荷马"}, {"word": "奥德赛"}],
  "context_type": "dialog_ctx",
  "context_data": [
    {"speaker": "user", "text": "上一轮对话或领域背景"}
  ]
}
```

Use `--hotwords` for a quick list, or combine it with `--context-json`; duplicate
hotwords are removed while preserving file order. The provider limits context to
500 tokens and does not allow it together with automatic language detection.

## Subtitle behavior

Word timestamps drive cue creation. Cues break at speaker changes, long silence,
sentence punctuation, suitable clause punctuation, or a hard display cap.
Punctuation exists in utterance text but may be absent from word tokens, so the
renderer aligns it back to word boundaries before grouping.

Video extraction must retain:

```text
-af aresample=async=1:first_pts=0
```

It preserves source PTS gaps so subtitles do not drift against the video.

## Important options

| Option | Purpose |
|---|---|
| `--srt [PATH]` | Write SRT; enabled by default |
| `--vtt [PATH]` | Write WebVTT |
| `--txt [PATH]` | Write plain transcript |
| `--transcript-json [PATH]` | Save reusable normalized transcript; default on |
| `--no-transcript-json` | Suppress transcript JSON |
| `--transcript-only` | Write only word/character timestamps; no subtitle files |
| `--language CODE` | Explicit language such as `zh-CN`, `en-US`, `ja-JP` |
| `--diarize` | Speaker separation for short/non-meeting material |
| `--meeting` | Long-meeting voiceprint mode (`ssd_version=300`) |
| `--hotwords TEXT` | Comma-separated context words |
| `--context-json FILE` | Full serialized `corpus.context` object |
| `--max-cue-chars N` | Target weighted cue length |
| `--max-cue-duration S` | Target cue duration |
| `--timeout S` | Overall query deadline |

For `--diarize` and `--meeting`, speaker separation is effective only when
language is unspecified or `zh-CN`.

## Environment

The script reads `VOLC_SPEECH_API_KEY` in this order:

1. Process environment.
2. `.env` in the current directory.
3. `~/.volcengine.env`.

The speech-console key is shared with `volcengine-tts`; it is not an Ark API key.

## Failure handling

- `20000001` / `20000002`: keep polling.
- `20000003` / `45000002`: successful empty transcript.
- HTTP 401/403 and `45xxxxxx`: stop without retrying.
- HTTP 429/5xx and `55xxxxxx`: bounded retry/backoff.
- Include `X-Tt-Logid` when reporting provider failures.

Errors are JSON on stderr and use a non-zero exit status. Successful summaries
are JSON on stdout.

For protocol parameters and source links, read
`references/volcengine-transcribe-api-docs.md` only when extending or troubleshooting
the provider integration.

## Boundaries

Do not use this skill for real-time WebSocket recognition, live dictation,
text-to-speech, music generation, or subtitle styling/burn-in.
