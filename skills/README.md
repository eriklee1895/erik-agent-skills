# Skills

[English](README.md) | [简体中文](README.zh-CN.md) · [Repository home](../README.md)

Browse all **21 skills**: [Writing (4)](#writing), [Media (12)](#media), and
[General Utilities (5)](#general-utilities). Each name opens its `SKILL.md`,
with usage instructions, requirements, and supporting references.

## Writing

| Skill | Purpose |
| --- | --- |
| [markdown-article-to-feishu-doc](./markdown-article-to-feishu-doc/SKILL.md) | Convert local Markdown into a structured Feishu document with media and Mermaid support. |
| [feishu-html-diagram](./feishu-html-diagram/SKILL.md) | Create high-fidelity, animated, or interactive diagrams inside Feishu Docx using HTML5 blocks when Mermaid, whiteboards, tables, or images are too restrictive. |
| [feishu-whiteboard-diagram](./feishu-whiteboard-diagram/SKILL.md) | Create, restyle, or review editable, document-quality architecture and process diagrams in Feishu Docx as native whiteboards (SVG / DSL / Mermaid), with fact-preserving editorial composition and evidence gates. |
| [wechat-article-fetcher](./wechat-article-fetcher/SKILL.md) | Extract a WeChat article into structured Markdown and local assets for research or reuse. |

## Media

| Skill | Purpose |
| --- | --- |
| [article-illustration](./article-illustration/SKILL.md) | Create article covers, inset illustrations, diagrams, infographics, and visual dividers. |
| [gpt-image-2](./gpt-image-2/SKILL.md) | Generate, edit, and batch-create raster images with OpenAI's gpt-image-2 model. |
| [gpt-image-api](./gpt-image-api/SKILL.md) | Generate, precisely edit, stream, and batch-create raster images with OpenAI GPT Image 2.5 Flare and Sunburst. |
| [openrouter-image](./openrouter-image/SKILL.md) | Generate and edit images through OpenRouter's unified image API with GPT Image 2.5 Sunburst/Flare and Nano Banana 2.1; the CLI validates each model's parameter dialect before the call. |
| [seedream-image-gen](./seedream-image-gen/SKILL.md) | Generate and edit images with Seedream, including typography, marker editing, outpainting, and batch workflows. |
| [avatar-creator](./avatar-creator/SKILL.md) | Create static avatar images, distinct-character families, same-character sets, and fixed Seedance GIF/MP4 animations. Uses available image tools; animation requires Ark credentials, uv, and ffmpeg with no other skill dependency. Does not build interactive 3D runtimes. |
| [live-avatar-3d](./live-avatar-3d/SKILL.md) | Turn a character image into a no-build interactive 3D browser avatar with orbit, gestures, and optional local microphone mouth motion. |
| [seedance-video-gen](./seedance-video-gen/SKILL.md) | Generate videos with Seedance from text, images, or multimodal references. |
| [volcengine-bigmusic-bgm](./volcengine-bigmusic-bgm/SKILL.md) | Generate instrumental background music for video and article media workflows. |
| [volcengine-tts](./volcengine-tts/SKILL.md) | Synthesize speech audio with Volcano Engine's text-to-speech models. |
| [volcengine-transcribe](./volcengine-transcribe/SKILL.md) | Transcribe audio/video to text with Volcano Engine's speech recognition and generate SRT/VTT subtitles; speaker diarization and ffmpeg video extraction built in. |
| [seed-audio-gen](./seed-audio-gen/SKILL.md) | Generate complete mixed audio scenes (voice + SFX + BGM) with the generative seed-audio-1.0 model; multi-reference voice cloning, sound effects, and directed dialogue in one call. |

For avatars, `avatar-creator` produces images, image sets, and looping GIF/MP4
assets. `live-avatar-3d` builds interactive 3D characters. Choose by the output
you need; the two skills can use the same character reference image.

## General Utilities

| Skill | Purpose |
| --- | --- |
| [deepseek-web-search](./deepseek-web-search/SKILL.md) | Search and fetch pages through DeepSeek's Search/Fetch APIs, with measured guidance for official-source ranking, localization traps, and fetch coverage gaps. |
| [macos-disk-deep-scan](./macos-disk-deep-scan/SKILL.md) | Explicit-only, read-only macOS developer disk audit: bounded scans, process/Git checks, and exact-path cleanup advice without deletion. |
| [notion-cli](./notion-cli/SKILL.md) | Operate Notion through a guarded helper around the official `ntn` CLI. |
| [volcengine-doc-fetcher](./volcengine-doc-fetcher/SKILL.md) | Fetch official Volcano Engine documentation as clean Markdown. |
| [volcengine-web-search](./volcengine-web-search/SKILL.md) | Search the web and images through Volcano Engine's search API, with strong Chinese-language coverage. |

## Install a skill

Use any skill name from the list above:

```bash
npx skills add eriklee1895/erik-agent-skills --skill gpt-image-api
```

To install the whole collection, use `npx skills add eriklee1895/erik-agent-skills --all`.
See the [installation guide](../docs/installation.en.md) for installation scope
and agent-specific options. Runtime tools and service credentials are configured
according to each skill's instructions.
