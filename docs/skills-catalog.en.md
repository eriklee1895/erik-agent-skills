# Skills catalog

[English](skills-catalog.en.md) | [简体中文](skills-catalog.zh-CN.md) · [Back to README](../README.md)

This catalog groups skills by their primary outcome. The categories are for
navigation only: skill directories remain flat under `skills/` so they can be
discovered, linked, and installed consistently.

## Writing

| Skill | Purpose |
| --- | --- |
| [article-ideation](../skills/article-ideation/) | Turn a rough idea into a focused writing brief and outline before research or drafting. |
| [polish-article](../skills/polish-article/) | Improve an article's reasoning, structure, voice, density, and genre fit while preserving the author's perspective. |
| [article-readiness-check](../skills/article-readiness-check/) | Check editorial readiness, facts, metadata, Markdown hygiene, assets, and channel handoff blockers before publishing. |
| [writing-task-closeout](../skills/writing-task-closeout/) | Archive the final state, update publishing status, capture reusable lessons, and prepare the post-publication handoff. |

## Publishing & Channels

| Skill | Purpose |
| --- | --- |
| [article-to-notion](../skills/article-to-notion/) | Capture and clean web articles into Notion while preserving useful metadata and assets. |
| [markdown-article-to-feishu-doc](../skills/markdown-article-to-feishu-doc/) | Convert local Markdown into a structured Feishu document with media and Mermaid support. |
| [feishu-html-diagram](../skills/feishu-html-diagram/) | Create high-fidelity, animated, or interactive diagrams inside Feishu Docx using HTML5 blocks when Mermaid, whiteboards, tables, or images are too restrictive. |
| [erik-blog-publish-workflow](../skills/erik-blog-publish-workflow/) | Sync finalized articles to Erik's Astro blog and validate assets, taxonomy, builds, and deployment handoff. |
| [wechat-article-fetcher](../skills/wechat-article-fetcher/) | Extract a WeChat article into structured Markdown and local assets for research or reuse. |
| [wechat-article-renderer](../skills/wechat-article-renderer/) | Render Markdown into polished, WeChat-ready inline HTML previews. |
| [wechat-article-publisher](../skills/wechat-article-publisher/) | Create a WeChat draft through Playwright, including article fields and image uploads, without final publication. |
| [wechat-publish-workflow](../skills/wechat-publish-workflow/) | Orchestrate rendering, verification, draft creation, and final human-review handoff for WeChat publishing. |

## Media

| Skill | Purpose |
| --- | --- |
| [article-illustration](../skills/article-illustration/) | Create article covers, inset illustrations, diagrams, infographics, and visual dividers. |
| [gpt-image-2](../skills/gpt-image-2/) | Generate, edit, and batch-create raster images with OpenAI's image model. |
| [seedream-image-gen](../skills/seedream-image-gen/) | Generate and edit images with Seedream, including typography, marker editing, outpainting, and batch workflows. |
| [seedance-video-gen](../skills/seedance-video-gen/) | Generate videos with Seedance from text, images, or multimodal references. |
| [video-material-ingest](../skills/video-material-ingest/) | Ingest known video URLs into traceable local material packages. |
| [video-highlight-select](../skills/video-highlight-select/) | Review video material and select article-relevant highlight ranges before clipping. |
| [article-video-clip](../skills/article-video-clip/) | Turn selected source footage into a lightly packaged, article-ready video clip. |
| [volcengine-bigmusic-bgm](../skills/volcengine-bigmusic-bgm/) | Generate instrumental background music for video and article media workflows. |
| [volcengine-tts](../skills/volcengine-tts/) | Synthesize speech audio with Volcano Engine's text-to-speech models. |
| [seed-audio-gen](../skills/seed-audio-gen/) | Generate complete mixed audio scenes (voice + SFX + BGM) with the generative seed-audio-1.0 model; multi-reference voice cloning, sound effects, and directed dialogue in one call. |

## Tools & Integrations

| Skill | Purpose |
| --- | --- |
| [notion-cli](../skills/notion-cli/) | Operate Notion through a guarded helper around the official `ntn` CLI. |
| [volcengine-doc-fetcher](../skills/volcengine-doc-fetcher/) | Fetch official Volcano Engine documentation as clean Markdown. |
| [volcengine-web-search](../skills/volcengine-web-search/) | Search the web and images through Volcano Engine's search API, with strong Chinese-language coverage. |

## Classification rules

- Classify each skill by its primary user outcome, not by its implementation technology.
- Keep each skill in one primary category; link related skills instead of duplicating them.
- Keep all skill directories as direct children of `skills/`.
- Update both language versions of this catalog whenever skills are added, removed, or renamed.
