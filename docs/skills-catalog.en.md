# Skills catalog

[English](skills-catalog.en.md) | [简体中文](skills-catalog.zh-CN.md) · [Back to README](../README.md)

This catalog groups skills by their primary outcome. The categories are for
navigation only: skill directories remain flat under `skills/` so they can be
discovered, linked, and installed consistently.

> The end-to-end **writing workflow** skills (ideation, polishing, readiness
> checks, WeChat rendering/publishing, blog publishing, and post-publication
> closeout) are specific to Erik's
> [writing-agent-harness](https://github.com/eriklee1895/writing-agent-harness)
> project and are intentionally not published here.

## Publishing & Channels

| Skill | Purpose | Install |
| --- | --- | --- |
| [article-to-notion](../skills/article-to-notion/) | Capture and clean web articles into Notion while preserving useful metadata and assets. | `npx skills add eriklee1895/erik-agent-skills --skill article-to-notion` |
| [markdown-article-to-feishu-doc](../skills/markdown-article-to-feishu-doc/) | Convert local Markdown into a structured Feishu document with media and Mermaid support. | `npx skills add eriklee1895/erik-agent-skills --skill markdown-article-to-feishu-doc` |
| [feishu-html-diagram](../skills/feishu-html-diagram/) | Create high-fidelity, animated, or interactive diagrams inside Feishu Docx using HTML5 blocks when Mermaid, whiteboards, tables, or images are too restrictive. | `npx skills add eriklee1895/erik-agent-skills --skill feishu-html-diagram` |
| [feishu-whiteboard-diagram](../skills/feishu-whiteboard-diagram/) | Insert editable, document-quality architecture and process diagrams into Feishu Docx as native whiteboards (SVG / DSL / Mermaid), using editorial composition rather than screenshots or HTML5. | `npx skills add eriklee1895/erik-agent-skills --skill feishu-whiteboard-diagram` |
| [wechat-article-fetcher](../skills/wechat-article-fetcher/) | Extract a WeChat article into structured Markdown and local assets for research or reuse. | `npx skills add eriklee1895/erik-agent-skills --skill wechat-article-fetcher` |

## Media

| Skill | Purpose | Install |
| --- | --- | --- |
| [article-illustration](../skills/article-illustration/) | Create article covers, inset illustrations, diagrams, infographics, and visual dividers. | `npx skills add eriklee1895/erik-agent-skills --skill article-illustration` |
| [gpt-image-2](../skills/gpt-image-2/) | Generate, edit, and batch-create raster images with OpenAI's image model. | `npx skills add eriklee1895/erik-agent-skills --skill gpt-image-2` |
| [seedream-image-gen](../skills/seedream-image-gen/) | Generate and edit images with Seedream, including typography, marker editing, outpainting, and batch workflows. | `npx skills add eriklee1895/erik-agent-skills --skill seedream-image-gen` |
| [seedance-video-gen](../skills/seedance-video-gen/) | Generate videos with Seedance from text, images, or multimodal references. | `npx skills add eriklee1895/erik-agent-skills --skill seedance-video-gen` |
| [video-material-ingest](../skills/video-material-ingest/) | Ingest known video URLs into traceable local material packages. | `npx skills add eriklee1895/erik-agent-skills --skill video-material-ingest` |
| [video-highlight-select](../skills/video-highlight-select/) | Review video material and select article-relevant highlight ranges before clipping. | `npx skills add eriklee1895/erik-agent-skills --skill video-highlight-select` |
| [volcengine-bigmusic-bgm](../skills/volcengine-bigmusic-bgm/) | Generate instrumental background music for video and article media workflows. | `npx skills add eriklee1895/erik-agent-skills --skill volcengine-bigmusic-bgm` |
| [volcengine-tts](../skills/volcengine-tts/) | Synthesize speech audio with Volcano Engine's text-to-speech models. | `npx skills add eriklee1895/erik-agent-skills --skill volcengine-tts` |
| [volcengine-asr](../skills/volcengine-asr/) | Transcribe audio/video to text with Volcano Engine's speech recognition and generate SRT/VTT subtitles; speaker diarization and ffmpeg video extraction built in. | `npx skills add eriklee1895/erik-agent-skills --skill volcengine-asr` |
| [seed-audio-gen](../skills/seed-audio-gen/) | Generate complete mixed audio scenes (voice + SFX + BGM) with the generative seed-audio-1.0 model; multi-reference voice cloning, sound effects, and directed dialogue in one call. | `npx skills add eriklee1895/erik-agent-skills --skill seed-audio-gen` |

## Tools & Integrations

| Skill | Purpose | Install |
| --- | --- | --- |
| [notion-cli](../skills/notion-cli/) | Operate Notion through a guarded helper around the official `ntn` CLI. | `npx skills add eriklee1895/erik-agent-skills --skill notion-cli` |
| [volcengine-doc-fetcher](../skills/volcengine-doc-fetcher/) | Fetch official Volcano Engine documentation as clean Markdown. | `npx skills add eriklee1895/erik-agent-skills --skill volcengine-doc-fetcher` |
| [volcengine-web-search](../skills/volcengine-web-search/) | Search the web and images through Volcano Engine's search API, with strong Chinese-language coverage. | `npx skills add eriklee1895/erik-agent-skills --skill volcengine-web-search` |

## Classification rules

- Classify each skill by its primary user outcome, not by its implementation technology.
- Keep each skill in one primary category; link related skills instead of duplicating them.
- Keep all skill directories as direct children of `skills/`.
- Update both language versions of this catalog whenever skills are added, removed, or renamed.
