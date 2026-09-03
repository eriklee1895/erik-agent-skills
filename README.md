# erik-agent-skills

[English](README.md) | [简体中文](README.zh-CN.md)

![Erik Lee Agent Skills README banner](assets/erik-agent-skills-cover-wide.jpg)

<p align="center">
  <a href="docs/skills-catalog.en.md"><img alt="25 curated skills" src="https://img.shields.io/badge/COLLECTION-25_SKILLS-0B1F3A?style=for-the-badge"></a>
  <a href="docs/skills-catalog.en.md"><img alt="4 skill categories" src="https://img.shields.io/badge/CATEGORIES-4-6750A4?style=for-the-badge"></a>
  <a href="https://developers.openai.com/codex/skills"><img alt="Codex ready" src="https://img.shields.io/badge/CODEX-READY-0F9D88?style=for-the-badge&logo=openai&logoColor=white"></a>
  <a href="README.zh-CN.md"><img alt="English and Chinese documentation" src="https://img.shields.io/badge/DOCS-EN_%7C_%E4%B8%AD%E6%96%87-F2B134?style=for-the-badge&logo=markdown&logoColor=white"></a>
  <a href="https://github.com/eriklee1895"><img alt="Curated by Erik Lee" src="https://img.shields.io/badge/CURATED_BY-ERIK_LEE-E85D75?style=for-the-badge&logo=github&logoColor=white"></a>
</p>

Erik Lee's curated library of reusable Agent Skills for writing, publishing,
media creation, and tool-driven workflows.

## Install

Install the complete collection or choose individual skills with the Skills
CLI. See the [full installation guide](docs/installation.en.md) for project-
level, global, and agent-specific options.

```bash
# Install all skills
npx skills add eriklee1895/erik-agent-skills --all

# Install one skill
npx skills add eriklee1895/erik-agent-skills --skill seed-audio-gen
```

## Skills

The repository currently includes 25 skills across four areas:

| Area | Skills | Focus |
| --- | ---: | --- |
| Writing | 4 | Ideation, polishing, readiness checks, and closeout |
| Publishing & Channels | 8 | WeChat, blog, Notion, and Feishu workflows |
| Media | 10 | Image, video, speech, music, and media preparation |
| Tools & Integrations | 3 | Reusable CLIs, documentation retrieval, and web search |

Browse the [English skills catalog](docs/skills-catalog.en.md) for the complete
categorized list, descriptions, and per-skill install commands.

## Repository layout

- `skills/` is the canonical publishing source. Each direct child is one skill.
- `docs/` contains the bilingual catalog and repository-level documentation.
- `assets/` contains repository-level visual assets.

Each skill is a self-contained directory with a required `SKILL.md` and optional
`scripts/`, `references/`, `guides/`, `assets/`, `evals/`, and `agents/` directories.

## Related project

Explore [writing-agent-harness](https://github.com/eriklee1895/writing-agent-harness),
Erik's personal AI writing system for ideation, research, drafting, polishing,
visuals, publishing, and continuous workflow improvement.
