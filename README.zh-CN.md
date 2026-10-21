# erik-agent-skills

[English](README.md) | [简体中文](README.zh-CN.md)

![Erik Lee Agent Skills](assets/erik-agent-skills-cover-wide.jpg)

<p align="center">
  <a href="skills/README.zh-CN.md"><img alt="21 个 skills" src="https://img.shields.io/badge/COLLECTION-21_SKILLS-0B1F3A?style=for-the-badge"></a>
  <a href="skills/README.zh-CN.md"><img alt="3 个分类" src="https://img.shields.io/badge/CATEGORIES-3-6750A4?style=for-the-badge"></a>
  <a href="README.md"><img alt="中英文文档" src="https://img.shields.io/badge/DOCS-EN_%7C_%E4%B8%AD%E6%96%87-F2B134?style=for-the-badge&logo=markdown&logoColor=white"></a>
</p>

一组实用的 Agent Skills，用于图片、视频和音频创作，文档与图表制作，以及搜索和资料提取。

每个 skill 围绕一类任务组织说明和所需资源。按需安装，即可交给你的 Agent 使用。

## 按任务选择

| 我想要…… | 从这里开始 |
| --- | --- |
| 生成或编辑图片 | [GPT Image](skills/gpt-image-api/SKILL.md) · [OpenRouter](skills/openrouter-image/SKILL.md) · [Seedream](skills/seedream-image-gen/SKILL.md) |
| 制作文章封面和插图 | [Article Illustration](skills/article-illustration/SKILL.md) |
| 根据文字或参考素材生成视频 | [Seedance](skills/seedance-video-gen/SKILL.md) |
| 生成语音、音乐或完整音频场景 | [TTS 配音](skills/volcengine-tts/SKILL.md) · [BGM 配乐](skills/volcengine-bigmusic-bgm/SKILL.md) · [Seed Audio 场景音](skills/seed-audio-gen/SKILL.md) |
| 把 Markdown 转为飞书文档，或为文档配图 | [Markdown 转飞书](skills/markdown-article-to-feishu-doc/SKILL.md) · [原生画板](skills/feishu-whiteboard-diagram/SKILL.md) · [交互图表](skills/feishu-html-diagram/SKILL.md) |
| 联网搜索或收集文章素材 | [DeepSeek 搜索](skills/deepseek-web-search/SKILL.md) · [豆包搜索](skills/volcengine-web-search/SKILL.md) · [微信文章提取](skills/wechat-article-fetcher/SKILL.md) |

[浏览全部 21 个 skills →](skills/README.zh-CN.md)，还包括头像、语音转写、Notion、官方文档抓取和 macOS 磁盘审计。

## 快速开始

安装单个 skill：

```bash
npx skills add eriklee1895/erik-agent-skills --skill gpt-image-api
```

也可以安装完整集合：

```bash
npx skills add eriklee1895/erik-agent-skills --all
```

项目级、全局和指定 Agent 的安装选项见[安装指南](docs/installation.zh-CN.md)。
安装后，按所选 skill 的说明配置运行工具和服务凭据。

## 浏览仓库

- [Skills](skills/README.zh-CN.md)：完整清单和各 skill 的使用说明。
- [安装指南](docs/installation.zh-CN.md)：安装范围和常用选项。
- `skills/<name>/`：各 skill 的源文件、工具、参考资料和示例。
- `assets/`：仓库视觉资源。

## 相关项目

欢迎访问 [writing-agent-harness](https://github.com/eriklee1895/writing-agent-harness)：
Erik 的个人 AI 写作系统，覆盖选题、研究、起草、润色、视觉制作、发布与工作流持续改进。
