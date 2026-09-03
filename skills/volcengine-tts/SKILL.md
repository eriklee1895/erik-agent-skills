---
name: volcengine-tts
description: >
  Generate speech audio from text using Volcano Engine's (火山引擎) Doubao Speech Synthesis Model 2.0 (豆包语音合成大模型2.0, seed-tts-2.0).
  Use this skill whenever the user needs text-to-speech, voiceover, narration, dubbing, 配音, 旁白, 朗读, TTS, speech synthesis, or audio generation from text.
  Also use when the user mentions 火山引擎 TTS, 豆包语音, volcengine speech, or needs AI-generated voice audio for videos, podcasts, or presentations.
  Supports single-sentence and batch synthesis with Chinese, English, Japanese, Spanish, Indonesian, Portuguese, Korean, and dialects.
  This skill should ALWAYS be used for any TTS/语音合成 task — never attempt to call the Volcano Engine TTS API directly without it.
---

# Volcengine TTS

Generate speech audio using Volcano Engine's Doubao Speech Synthesis Model 2.0 (`seed-tts-2.0`).

## Quick Start

```bash
# Single sentence — outputs MP3 + .meta.json to tts-output/
uv run scripts/volcengine-tts.py "你好，欢迎使用豆包语音合成"

# With speaker selection
uv run scripts/volcengine-tts.py "Hello world" --speaker en_female_dacey_uranus_bigtts

# Batch mode — concurrent synthesis
uv run scripts/volcengine-tts.py --batch '[{"text":"第一句","speaker":"zh_female_vv_uranus_bigtts"},{"text":"第二句"}]'

# Math/education narration — always use the LaTeX parser trio
uv run scripts/volcengine-tts.py "根据公式 $a^2 + b^2 = c^2$ 可知..." --latex --latex-parser v2 --strip-markdown

# List available speakers (local table, no API call)
uv run scripts/volcengine-tts.py --list-speakers
```

## Script

The core implementation is `scripts/volcengine-tts.py` — a PEP 723 inline-dependency Python script.

**Always run with `uv run`** — it auto-creates an isolated environment from the inline metadata. Never use bare `python` or `pip`.

## Environment Setup

The script reads `VOLC_SPEECH_API_KEY` with three-level fallback:
1. `VOLC_SPEECH_API_KEY` environment variable
2. `.env` file in the current working directory
3. `~/.volcengine.env` (user-level config)

To set up permanently:
```bash
echo 'VOLC_SPEECH_API_KEY=your-key-here' >> ~/.volcengine.env
```

## CLI Reference

### Single Sentence Mode (default)

```
uv run scripts/volcengine-tts.py <text> [options]
```

Output: JSON to stdout with `audio_file`, `duration_ms`, `text`, `speaker`, `format`, `sample_rate`, `text_words`, `log_id`, and `error` (on failure).

### Batch Mode

```
uv run scripts/volcengine-tts.py --batch '<json-array>' [options]
```

Each item: `{"text": "...", "speaker": "...", ...}`. Extra keys override per-item options (speaker, speech_rate, volume, etc.).

Output: JSON array of results, each with the same fields as single mode. Failed items have `error` set; successful items continue independently.

### Key Options

| Flag | Default | Description |
|------|---------|-------------|
| `--speaker`, `-s` | `zh_female_vv_uranus_bigtts` | Voice/speaker ID |
| `--output-dir`, `-o` | `./tts-output/` | Output directory |
| `--batch`, `-b` | — | Batch JSON input (disables positional text) |
| `--concurrency`, `-c` | `3` | Max parallel requests in batch mode |
| `--format` | `mp3` | Audio format: mp3, pcm, ogg_opus, wav |
| `--sample-rate` | `24000` | Sample rate: 8000, 16000, 22050, 24000, 32000, 44100, 48000 |
| `--speech-rate` | `0` | Speed [-50, 100], 100=2x, -50=0.5x |
| `--volume` | `0` | Volume [-50, 100], 100=2x |
| `--pitch` | `0` | Pitch [-12, 12] semitones |
| `--model` | _(unset)_ | Optional model variant; mostly relevant for cloned (ICL) voices (e.g. `seed-tts-2.0-standard`). Official seed-tts-2.0 voices work without it. |
| `--context` | — | Natural language voice instruction — tone, emotion, pacing, persona. E.g. "用痛心的语气说话", "像深夜电台主持人一样温柔地读", "用激动兴奋的语气". Works with all official seed-tts-2.0 voices out of the box (no `--model` flag required). |
| `--ssml` | — | Parse input text as SSML |
| `--language` | — | Explicit language: zh-cn, en, ja, es-mx, id, pt-br, ko |
| `--latex` | — | Enable LaTeX formula reading; auto-enables Markdown filtering because the API requires `disable_markdown_filter=true` |
| `--latex-parser v2` | — | Stronger LaTeX parsing for math/education narration; auto-enables `--latex` and `--strip-markdown`, with higher latency |
| `--silence-duration` | `0` | Trailing silence in ms [0, 30000] |
| `--watermark` | — | Add AIGC audio watermark |
| `--no-subtitle` | _(subtitle on by default)_ | Turn off word-level timestamps. Saves ~600ms of tail latency for real-time / conversational use cases. Offline narration pipelines should leave subtitles **on** (the default) — downstream subtitle generation, B-roll alignment, and forced cuts all need word timestamps. |
| `--strip-markdown` | — | Remove Markdown syntax (e.g. `**bold**` → "bold") |
| `--strip-emoji` | — | Remove emoji characters before TTS |
| `--list-speakers` | — | List speakers from local table (no API call) |
| `--filter <k=v>` | — | Filter speakers: `scene=教学场景`, `type=bigtts`, `lang=ja` (repeatable) |
| `--sort heat` | — | Sort speakers by heat (popularity) |

### Math and Education Narration

For education videos, math explainers, physics scripts, and any narration likely to contain LaTeX, **always pass `--latex --latex-parser v2 --strip-markdown`**. Do not use plain `--latex` manually for education content; the v2 parser is the intended default despite higher latency, because formula pronunciation quality matters more than speed in offline narration.

The script maps those flags to the API's required LaTeX parser trio internally. Agents should call the CLI flags above, not construct Volcano TTS API payloads directly.

### Voice Instructions (`--context`)

All official Doubao TTS 2.0 voices (speaker IDs ending in `_bigtts`) support natural-language voice instructions via `--context` / the API's `context_texts` field. You do **not** need to pass a special `--model` to use it. Examples:

- `"像深夜电台主持人一样温柔低沉地读"`
- `"用痛心疾首的语气说话，语速放慢"`
- `"像新闻联播主播一样正式、字正腔圆地播报"`
- `"Read like an excited startup founder giving a keynote"`

The `--model` flag is primarily for cloned (ICL) voices, where you can explicitly request `seed-tts-2.0-standard` (lower latency, no voice-instruction QA) — leave it unset for the default public catalog.

## Output Format

### Success (single)
```json
{
  "audio_file": "tts-output/tts_20260616_113000_001.mp3",
  "duration_ms": 1240,
  "text": "你好世界",
  "speaker": "zh_female_vv_uranus_bigtts",
  "format": "mp3",
  "sample_rate": 24000,
  "text_words": 4,
  "log_id": "202606161130000FACFE6D19421815D605",
  "words": [
    {"word": "你", "startTime": 0.22, "endTime": 0.33, "confidence": 0.85},
    {"word": "好", "startTime": 0.33, "endTime": 0.55, "confidence": 0.92},
    {"word": "世", "startTime": 0.55, "endTime": 0.80, "confidence": 0.78},
    {"word": "界", "startTime": 0.80, "endTime": 1.01, "confidence": 0.96}
  ],
  "sentence_text": "你好世界",
  "error": null
}
```

**Word-level timestamps are on by default.** Pass `--no-subtitle` if you don't need them and want ~600ms less tail latency (e.g. realtime playback).

### Error (single)
```json
{
  "audio_file": null,
  "duration_ms": null,
  "text": "你好世界",
  "error": "45002001: No readable text!",
  "log_id": "202606161130000FACFE6D19421815D605"
}
```

### Batch
```json
{
  "results": [
    {"audio_file": "tts-output/tts_20260616_113000_001.mp3", "duration_ms": 1240, ...},
    {"audio_file": null, "error": "429: quota exceeded for types: concurrency", ...}
  ],
  "total_duration_ms": 1240,
  "success_count": 1,
  "fail_count": 1
}
```

## Metadata Sidecar

Each audio file gets a `.meta.json` sibling with the same base name:
```
tts-output/
  tts_20260616_113000_001.mp3
  tts_20260616_113000_001.meta.json
```

The meta file includes all result fields, including `words` (word-level timestamps) **by default** (unless `--no-subtitle` was passed). Downstream tools (video compositors, subtitle generators, karaoke aligners, B-roll cut planners) should read the `.meta.json` files — they survive process restarts and don't require re-reading the audio.

Enabling subtitles adds ~600ms of **tail latency** (the server runs a forced-alignment pass after audio generation) but does not affect time-to-first-byte, does not increase audio size, and does not incur extra billing. For offline narration/video pipelines (this repo's main use case), leave it on; for real-time conversational use, pass `--no-subtitle`.

### Word-level timestamps (`--subtitle`)

When `--subtitle` is set, each returned word has:

| Field | Type | Meaning |
|-------|------|---------|
| `word` | string | The character / token (Chinese: 1 char per word; English: word or punctuation group) |
| `startTime` | float | Start offset in seconds |
| `endTime` | float | End offset in seconds |
| `confidence` | float | Alignment confidence 0–1 |

Notes from the official docs (2026-06-29):
- Only seed-tts-2.0 voices support `enable_subtitle`; only Chinese and English are supported.
- Timestamps are relative to the returned audio (i.e., start of the MP3).
- Use for: subtitles, karaoke-style highlight, forced alignment with video cuts, lip-sync hinting.

## Voice Selection

**Query the catalog with `--list-speakers`** (reads a local table, no API call). Do **not** read `references/speakers.json` into context — it is ~220KB / 444 seed-tts-2.0 voices. `references/volcengine-speakers.md` is a short curated shortlist (Top 5 per scene, narration/教学/客服 first, with trial links), not the full list.

### Common-scene quick picks

For the usual narration scenes, reach for these defaults first; otherwise browse `references/volcengine-speakers.md` or `--list-speakers`:

| Scenario | Voice | voice_type |
|---|---|---|
| General narration (default female) | Vivi 2.0 · warm, calm (heat 100) | `zh_female_vv_uranus_bigtts` |
| Customer service / IVR | 暖阳女声 2.0 | `zh_female_kefunvsheng_uranus_bigtts` |
| Teaching / education (use with `--latex` as needed) | Tina老师 2.0 | `zh_female_yingyujiaoxue_uranus_bigtts` |
| Tech explainer (male) | 云舟 2.0 · clear, professional | `zh_male_m191_uranus_bigtts` |
| Story narration (warm female) | 温柔妈妈 2.0 | `zh_female_wenroumama_uranus_bigtts` |
| Suspense / dramatic narration (male) | 悬疑解说 2.0 | `zh_male_xuanyijieshuo_uranus_bigtts` |
| English content | Dacey (f) / Tim (m) | `en_female_dacey_uranus_bigtts` / `en_male_tim_uranus_bigtts` |

Browse by scene/heat:

```bash
# Full catalog
uv run scripts/volcengine-tts.py --list-speakers

# Filter by scene (JSON scene names, e.g. 教学场景 not 教育场景)
uv run scripts/volcengine-tts.py --list-speakers --filter scene=教学场景

# Official catalog only, sorted by heat
uv run scripts/volcengine-tts.py --list-speakers --filter type=bigtts --sort heat

# Filter by language, sorted by heat
uv run scripts/volcengine-tts.py --list-speakers --filter lang=ja --sort heat
```

`--list-speakers` may include ICL voices (`type=icl`, IDs containing `ICL_` or `_tob`). Seeing them in the local table does **not** mean they synthesize with the default public-catalog call. Official `_bigtts` voices work with Resource-Id `seed-tts-2.0` and do **not** need `--model`. Registered ICL/`_tob` voices typically need `--model seed-tts-2.0-standard`. Creating a new cloned voice is a different skill, not this list.

To refresh the speaker table when new voices are released, run:

```bash
uv run scripts/refresh-speakers.py
```

This requires AK/SK (`VOLC_ACCESSKEY`/`VOLC_SECRETKEY`) and the internal Volcano SDK preinstalled; the ListSpeakers API uses a different auth system than everyday synthesis, and always sends `ResourceIDs=["seed-tts-2.0"]`. To filter the local json and rebuild only the curated markdown (no API):

```bash
uv run scripts/refresh-speakers.py --from-json
```

## Error Handling

- **Retryable errors**: HTTP 429, 5xx, and Volcano codes 55000000 — auto-retried with exponential backoff (1s → 2s → 4s, max 3 attempts)
- **Non-retryable errors**: HTTP 4xx (except 429), Volcano codes 45000000–45002001 — returned immediately with error message
- **Batch mode**: Failed items report error in their result object; other items continue independently
- Always include the `log_id` in error output for support escalation
- For full error code reference and official docs, read `references/volcengine-api-docs.md`

## When to Use This Skill

- User asks to generate voice audio, TTS, speech synthesis
- User needs voiceover/narration/dubbing for video, podcast, or presentation
- User mentions 火山引擎, 豆包语音, volcengine TTS, or seed-tts
- User wants to convert text to spoken audio in Chinese, English, Japanese, etc.
- User needs batch voice generation from a script or article

## When NOT to Use

- Voice cloning / 声音复刻 — needs a separate skill (uses `seed-icl-2.0`)
- Real-time speech recognition / ASR — different API
- Music/audio editing — not TTS
