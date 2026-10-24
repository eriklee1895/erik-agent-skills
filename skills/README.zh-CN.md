# Skills 目录

[English](README.md) | [简体中文](README.zh-CN.md) · [仓库首页](../README.zh-CN.md)

这里列出全部 **21 个 skills**：[写作（4）](#写作)、[媒体（12）](#媒体)、[通用工具（5）](#通用工具)。
点击名称即可打开对应的 `SKILL.md`，查看使用方法、环境要求和参考资料。

## 写作

| Skill | 用途 |
| --- | --- |
| [markdown-article-to-feishu-doc](./markdown-article-to-feishu-doc/SKILL.md) | 将本地 Markdown 转为结构完整的飞书文档，并支持图片与 Mermaid。 |
| [feishu-html-diagram](./feishu-html-diagram/SKILL.md) | 在 Mermaid、画板、表格或图片表达受限时，用 HTML5 块在飞书 Docx 中创建高保真、动态或交互式图表。 |
| [feishu-whiteboard-diagram](./feishu-whiteboard-diagram/SKILL.md) | 在飞书 Docx 中新增、改版或审查可二次编辑的精美架构 / 流程图，使用原生画板（SVG / DSL / Mermaid）、事实保真构图与分层证据门禁。 |
| [wechat-article-fetcher](./wechat-article-fetcher/SKILL.md) | 将微信公众号文章提取为结构化 Markdown 和本地素材，用于研究或复用。 |

## 媒体

| Skill | 用途 |
| --- | --- |
| [article-illustration](./article-illustration/SKILL.md) | 为文章制作封面、正文插图、图解、信息图和视觉分隔图。 |
| [gpt-image-2](./gpt-image-2/SKILL.md) | 使用 OpenAI gpt-image-2 模型生成、编辑和批量制作位图。 |
| [gpt-image-api](./gpt-image-api/SKILL.md) | 使用 OpenAI GPT Image 2.5 Flare 与 Sunburst 生成、精细编辑、流式生成和批量制作位图。 |
| [openrouter-image](./openrouter-image/SKILL.md) | 通过 OpenRouter 统一图像 API 使用 GPT Image 2.5 Sunburst/Flare 与 Nano Banana 2.1 生成和编辑图片；CLI 会在调用前校验各模型的参数方言。 |
| [seedream-image-gen](./seedream-image-gen/SKILL.md) | 使用 Seedream 5.0 Pro/Flash 生图和编辑，支持文字设计、坐标编辑、透明图层编辑、原生图层拆分与批量工作流。 |
| [avatar-creator](./avatar-creator/SKILL.md) | 制作静态头像、不同角色家族、同角色套图及固定 Seedance GIF/MP4 动画。图片使用可用图像工具；动图需 Ark 凭据、uv 和 ffmpeg，不依赖其他 skill。不负责交互式 3D 程序。 |
| [live-avatar-3d](./live-avatar-3d/SKILL.md) | 将角色图制作成无需构建步骤的交互式 3D 网页头像，支持环视、动作和可选的本地麦克风嘴型。 |
| [seedance-video-gen](./seedance-video-gen/SKILL.md) | 使用 Seedance 根据文本、图片或多模态参考生成视频。 |
| [volcengine-bigmusic-bgm](./volcengine-bigmusic-bgm/SKILL.md) | 为视频和文章媒体工作流生成无人声背景音乐。 |
| [volcengine-tts](./volcengine-tts/SKILL.md) | 使用火山引擎语音合成模型生成语音音频。 |
| [volcengine-transcribe](./volcengine-transcribe/SKILL.md) | 用火山引擎语音识别将音视频转写为文本并生成 SRT/VTT 字幕；内置说话人分离与 ffmpeg 视频抽音轨。 |
| [seed-audio-gen](./seed-audio-gen/SKILL.md) | 用生成式 seed-audio-1.0 模型一次生成人声+音效+BGM 的完整音频场景；支持多参考音色克隆、音效和导演式对白。 |

头像相关能力按产物选择：`avatar-creator` 制作单图、套图和循环 GIF/MP4 素材；
`live-avatar-3d` 制作交互式 3D 角色。两者可以使用同一张角色参考图。

## 通用工具

| Skill | 用途 |
| --- | --- |
| [deepseek-web-search](./deepseek-web-search/SKILL.md) | 通过 DeepSeek Search/Fetch API 搜索网页、抓取正文，内置官方源排序/过滤、本地化版本过滤与实测抓取边界说明。 |
| [macos-disk-deep-scan](./macos-disk-deep-scan/SKILL.md) | 仅显式调用的 macOS 开发者磁盘只读审计：限时扫描、进程/Git 复核及精确路径清理建议，不执行删除。 |
| [notion-cli](./notion-cli/SKILL.md) | 通过对官方 `ntn` CLI 的安全封装操作 Notion。 |
| [volcengine-doc-fetcher](./volcengine-doc-fetcher/SKILL.md) | 将火山引擎官方文档抓取为干净的 Markdown。 |
| [volcengine-web-search](./volcengine-web-search/SKILL.md) | 通过火山引擎搜索 API 搜索网页和图片，重点覆盖中文内容。 |

## 安装单个 skill

使用上方列表中的任意 skill 名称：

```bash
npx skills add eriklee1895/erik-agent-skills --skill gpt-image-api
```

安装完整集合可使用 `npx skills add eriklee1895/erik-agent-skills --all`。
安装范围和指定 Agent 的选项见[安装指南](../docs/installation.zh-CN.md)；
运行工具和服务凭据按各 skill 的说明配置。
