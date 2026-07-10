# erik-agent-skills

[English](README.md) | [简体中文](README.zh-CN.md)

![Erik Lee Agent Skills README banner](assets/erik-agent-skills-cover-wide.png)

<p align="center">
  <a href="docs/skills-catalog.zh-CN.md"><img alt="23 个精选 Skills" src="https://img.shields.io/badge/COLLECTION-23_SKILLS-0B1F3A?style=for-the-badge"></a>
  <a href="docs/skills-catalog.zh-CN.md"><img alt="4 个 Skills 分类" src="https://img.shields.io/badge/CATEGORIES-4-6750A4?style=for-the-badge"></a>
  <a href="https://developers.openai.com/codex/skills"><img alt="Codex Ready" src="https://img.shields.io/badge/CODEX-READY-0F9D88?style=for-the-badge&logo=openai&logoColor=white"></a>
  <a href="README.md"><img alt="中英文文档" src="https://img.shields.io/badge/DOCS-EN_%7C_%E4%B8%AD%E6%96%87-F2B134?style=for-the-badge&logo=markdown&logoColor=white"></a>
  <a href="https://github.com/eriklee1895"><img alt="由 Erik Lee 维护" src="https://img.shields.io/badge/CURATED_BY-ERIK_LEE-E85D75?style=for-the-badge&logo=github&logoColor=white"></a>
</p>

Erik Lee 的个人 Agent Skills 仓库，收录可跨项目复用的写作、发布、媒体创作与工具型工作流。

## Skills

仓库目前收录 23 个 skills，分为四类：

| 分类 | 数量 | 能力范围 |
| --- | ---: | --- |
| 写作 | 4 | 选题构思、文章润色、发布前检查与任务收尾 |
| 发布与渠道 | 7 | 微信公众号、博客、Notion 与飞书工作流 |
| 媒体 | 9 | 图片、视频、语音、音乐与媒体素材处理 |
| 工具与集成 | 3 | 可复用 CLI、文档抓取与联网搜索 |

完整分类、skill 清单及用途说明见[中文 Skills 目录](docs/skills-catalog.zh-CN.md)。

## 仓库结构

- `skills/` 是唯一发布源，每个一级子目录对应一个 skill。
- `docs/` 存放双语 Skills 目录和仓库级文档。
- `assets/` 存放仓库级视觉资源。

每个 skill 都是一个自包含目录，必须提供 `SKILL.md`，并可按需包含
`scripts/`、`references/`、`assets/`、`evals/` 和 `agents/`。

## 相关项目

欢迎访问 [writing-agent-harness](https://github.com/eriklee1895/writing-agent-harness)：
Erik 的个人 AI 写作系统，覆盖选题、研究、起草、润色、视觉制作、发布与工作流持续改进。
