# Skills 目录

[English](skills-catalog.en.md) | [简体中文](skills-catalog.zh-CN.md) · [返回 README](../README.zh-CN.md)

本目录按照 skill 的主要用户目标进行分类。分类仅用于浏览和理解；所有 skill 目录继续平铺在
`skills/` 下，以保持发现、链接和安装方式的一致性。

## 写作

| Skill | 用途 | 安装 |
| --- | --- | --- |
| [article-ideation](../skills/article-ideation/) | 在研究或起草前，把模糊灵感整理成聚焦的 writing brief 和文章大纲。 | `npx skills add eriklee1895/erik-agent-skills --skill article-ideation` |
| [polish-article](../skills/polish-article/) | 在保留作者观点的前提下，改善文章逻辑、结构、声音、密度与文体匹配度。 | `npx skills add eriklee1895/erik-agent-skills --skill polish-article` |
| [article-readiness-check](../skills/article-readiness-check/) | 发布前检查编辑成熟度、事实、元数据、Markdown 规范、素材和渠道交付阻塞项。 | `npx skills add eriklee1895/erik-agent-skills --skill article-readiness-check` |
| [writing-task-closeout](../skills/writing-task-closeout/) | 归档最终状态、更新发布信息、沉淀可复用经验，并完成发布后的任务交接。 | `npx skills add eriklee1895/erik-agent-skills --skill writing-task-closeout` |

## 发布与渠道

| Skill | 用途 | 安装 |
| --- | --- | --- |
| [article-to-notion](../skills/article-to-notion/) | 抓取和清洗网页文章，连同有价值的元数据与素材整理进 Notion。 | `npx skills add eriklee1895/erik-agent-skills --skill article-to-notion` |
| [markdown-article-to-feishu-doc](../skills/markdown-article-to-feishu-doc/) | 将本地 Markdown 转为结构完整的飞书文档，并支持图片与 Mermaid。 | `npx skills add eriklee1895/erik-agent-skills --skill markdown-article-to-feishu-doc` |
| [feishu-html-diagram](../skills/feishu-html-diagram/) | 在 Mermaid、画板、表格或图片表达受限时，用 HTML5 块在飞书 Docx 中创建高保真、动态或交互式图表。 | `npx skills add eriklee1895/erik-agent-skills --skill feishu-html-diagram` |
| [feishu-whiteboard-diagram](../skills/feishu-whiteboard-diagram/) | 在飞书 Docx 中插入可二次编辑的精美架构 / 流程图，使用原生画板（SVG / DSL / Mermaid），而不是截图或 HTML5。 | `npx skills add eriklee1895/erik-agent-skills --skill feishu-whiteboard-diagram` |
| [erik-blog-publish-workflow](../skills/erik-blog-publish-workflow/) | 将正式文章同步到 Erik 的 Astro 博客，并校验素材、分类、构建与部署交接。 | `npx skills add eriklee1895/erik-agent-skills --skill erik-blog-publish-workflow` |
| [wechat-article-fetcher](../skills/wechat-article-fetcher/) | 将微信公众号文章提取为结构化 Markdown 和本地素材，用于研究或复用。 | `npx skills add eriklee1895/erik-agent-skills --skill wechat-article-fetcher` |
| [wechat-article-renderer](../skills/wechat-article-renderer/) | 将 Markdown 渲染为适合微信公众号的精美内联 HTML 预览。 | `npx skills add eriklee1895/erik-agent-skills --skill wechat-article-renderer` |
| [wechat-article-publisher](../skills/wechat-article-publisher/) | 通过 Playwright 创建微信公众号草稿，填写文章字段并上传图片，但不执行最终发布。 | `npx skills add eriklee1895/erik-agent-skills --skill wechat-article-publisher` |
| [wechat-publish-workflow](../skills/wechat-publish-workflow/) | 编排微信公众号排版、校验、草稿创建和最终人工审核交接。 | `npx skills add eriklee1895/erik-agent-skills --skill wechat-publish-workflow` |

## 媒体

| Skill | 用途 | 安装 |
| --- | --- | --- |
| [article-illustration](../skills/article-illustration/) | 为文章制作封面、正文插图、图解、信息图和视觉分隔图。 | `npx skills add eriklee1895/erik-agent-skills --skill article-illustration` |
| [gpt-image-2](../skills/gpt-image-2/) | 使用 OpenAI 图片模型生成、编辑和批量制作位图。 | `npx skills add eriklee1895/erik-agent-skills --skill gpt-image-2` |
| [seedream-image-gen](../skills/seedream-image-gen/) | 使用 Seedream 生成和编辑图片，支持文字设计、标记编辑、扩图与批量工作流。 | `npx skills add eriklee1895/erik-agent-skills --skill seedream-image-gen` |
| [seedance-video-gen](../skills/seedance-video-gen/) | 使用 Seedance 根据文本、图片或多模态参考生成视频。 | `npx skills add eriklee1895/erik-agent-skills --skill seedance-video-gen` |
| [video-material-ingest](../skills/video-material-ingest/) | 将已知视频 URL 整理为可追踪的本地素材包。 | `npx skills add eriklee1895/erik-agent-skills --skill video-material-ingest` |
| [video-highlight-select](../skills/video-highlight-select/) | 审阅视频素材并选择与文章相关的高光时间段，为后续剪辑做准备。 | `npx skills add eriklee1895/erik-agent-skills --skill video-highlight-select` |
| [article-video-clip](../skills/article-video-clip/) | 将选定的源视频片段加工为轻包装、可直接用于文章的视频。 | `npx skills add eriklee1895/erik-agent-skills --skill article-video-clip` |
| [volcengine-bigmusic-bgm](../skills/volcengine-bigmusic-bgm/) | 为视频和文章媒体工作流生成无人声背景音乐。 | `npx skills add eriklee1895/erik-agent-skills --skill volcengine-bigmusic-bgm` |
| [volcengine-tts](../skills/volcengine-tts/) | 使用火山引擎语音合成模型生成语音音频。 | `npx skills add eriklee1895/erik-agent-skills --skill volcengine-tts` |
| [seed-audio-gen](../skills/seed-audio-gen/) | 用生成式 seed-audio-1.0 模型一次生成人声+音效+BGM 的完整音频场景；支持多参考音色克隆、音效和导演式对白。 | `npx skills add eriklee1895/erik-agent-skills --skill seed-audio-gen` |

## 工具与集成

| Skill | 用途 | 安装 |
| --- | --- | --- |
| [notion-cli](../skills/notion-cli/) | 通过对官方 `ntn` CLI 的安全封装操作 Notion。 | `npx skills add eriklee1895/erik-agent-skills --skill notion-cli` |
| [volcengine-doc-fetcher](../skills/volcengine-doc-fetcher/) | 将火山引擎官方文档抓取为干净的 Markdown。 | `npx skills add eriklee1895/erik-agent-skills --skill volcengine-doc-fetcher` |
| [volcengine-web-search](../skills/volcengine-web-search/) | 通过火山引擎搜索 API 搜索网页和图片，重点覆盖中文内容。 | `npx skills add eriklee1895/erik-agent-skills --skill volcengine-web-search` |

## 分类规则

- 按主要用户目标分类，不按底层实现技术分类。
- 每个 skill 只归入一个主分类；相关能力通过链接关联，不重复收录。
- 所有 skill 目录都保持为 `skills/` 的一级子目录。
- 新增、删除或重命名 skill 时，同步更新两种语言的目录。
