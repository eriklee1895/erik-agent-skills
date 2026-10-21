# erik-agent-skills

[English](README.md) | [简体中文](README.zh-CN.md)

![Erik Lee Agent Skills](assets/erik-agent-skills-cover-wide.jpg)

<p align="center">
  <a href="skills/README.md"><img alt="21 skills" src="https://img.shields.io/badge/COLLECTION-21_SKILLS-0B1F3A?style=for-the-badge"></a>
  <a href="skills/README.md"><img alt="3 categories" src="https://img.shields.io/badge/CATEGORIES-3-6750A4?style=for-the-badge"></a>
  <a href="README.zh-CN.md"><img alt="English and Chinese documentation" src="https://img.shields.io/badge/DOCS-EN_%7C_%E4%B8%AD%E6%96%87-F2B134?style=for-the-badge&logo=markdown&logoColor=white"></a>
</p>

Practical Agent Skills for creating images, video and audio, working with
documents and diagrams, and finding and extracting information.

Each skill provides focused task instructions and supporting resources. Install
the skills you need and use them with your agent.

## Find a skill for your task

| I want to… | Start here |
| --- | --- |
| Generate or edit images | [GPT Image](skills/gpt-image-api/SKILL.md) · [OpenRouter](skills/openrouter-image/SKILL.md) · [Seedream](skills/seedream-image-gen/SKILL.md) |
| Create article covers and illustrations | [Article Illustration](skills/article-illustration/SKILL.md) |
| Generate video from text or references | [Seedance](skills/seedance-video-gen/SKILL.md) |
| Create speech, music, or a mixed audio scene | [TTS](skills/volcengine-tts/SKILL.md) · [BGM](skills/volcengine-bigmusic-bgm/SKILL.md) · [Seed Audio](skills/seed-audio-gen/SKILL.md) |
| Turn Markdown into a Feishu document or add diagrams | [Markdown to Feishu](skills/markdown-article-to-feishu-doc/SKILL.md) · [Native whiteboards](skills/feishu-whiteboard-diagram/SKILL.md) · [Interactive diagrams](skills/feishu-html-diagram/SKILL.md) |
| Search the web or collect article sources | [DeepSeek Search](skills/deepseek-web-search/SKILL.md) · [Doubao Search](skills/volcengine-web-search/SKILL.md) · [WeChat article extraction](skills/wechat-article-fetcher/SKILL.md) |

[Browse all 21 skills →](skills/README.md), including avatars, transcription,
Notion, documentation retrieval, and macOS disk audits.

## Quick start

Install one skill:

```bash
npx skills add eriklee1895/erik-agent-skills --skill gpt-image-api
```

Or install the complete collection:

```bash
npx skills add eriklee1895/erik-agent-skills --all
```

The [installation guide](docs/installation.en.md) covers project-level, global,
and agent-specific options. After installation, follow the selected skill's
setup instructions for runtime tools and service credentials.

## Explore the repository

- [Skills](skills/README.md) — the complete list and each skill's instructions.
- [Installation](docs/installation.en.md) — installation scope and options.
- `skills/<name>/` — each skill's source, bundled tools, references, and examples.
- `assets/` — repository visuals.
