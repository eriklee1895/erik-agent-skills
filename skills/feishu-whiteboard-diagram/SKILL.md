---
name: feishu-whiteboard-diagram
description: Use when 为飞书/Lark 技术文档创作、改版或审查可编辑的原生画板，包括架构、流程、关系与静态指标对比，或从参考画板提炼作图经验；动画与交互探索使用 feishu-html-diagram。
metadata:
  author: liyuheng.erik
  requires:
    bins: ["node", "npx", "python3"]
    skills: ["lark-doc", "lark-whiteboard", "lark-shared"]
---

# 飞书画板精美图表

把文章中的职责、关系、流程和指标画清楚，并保留原生节点的可编辑性。本 skill 负责事实、构图、视觉选择与验证；配色和布局由 agent 结合文章设计。交付可以是本地候选，也可以是经授权写入文档的 whiteboard block。

## 按请求开始

| 请求 | 起点与完成边界 |
|---|---|
| 新建图 / 只做本地 | 提炼来源事实，选择介质，生成并检查候选；本地工作不需要登录或 board token |
| 写入飞书文档 | 本地候选通过后，按底座创建画板块并写入；回读目标位置 |
| 修改已有画板 | 先导出当前预览与结构，固定改动轴；保留未被要求修改的事实、关系和视觉身份，复用原 token |
| 只审查 | 按可取得的证据给结论与建议；到审查结果为止 |
| 学习参考图 | 只读检查正文、预览与 raw；区分视觉效果和原生能力，泛化方法，原始内部材料留在研究目录 |

**底座分工：** 文档读取与画板块由已安装的 [`lark-doc`](https://github.com/larksuite/cli/tree/main/skills/lark-doc) 负责；导出、格式写入与已有画板编辑由 [`lark-whiteboard`](https://github.com/larksuite/cli/tree/main/skills/lark-whiteboard) 负责；身份、认证、权限与高风险确认遵守 [`lark-shared`](https://github.com/larksuite/cli/tree/main/skills/lark-shared)。进入相应操作前读取对应底座及其必读参考，CLI 参数以它们为准。

底座中的视觉建议不能替代本文的事实与可编辑性要求。装饰、内容扩展和整板重建都应符合当前任务；用户要求局部修改时，先按官方编辑路径判断是否会有损。

## 1. 明确问题与关系

在工作笔记中写清：**图回答什么、读者如何查看、来源事实、实体与关系、未知项、准备省略什么**。简单图用几句话即可；复杂图、改版或审查使用 [事实契约与复核](references/brief-review.md)。

箭头、数字、因果、归属、状态和先后顺序都是事实声明。参考图的对齐、颜色和编号也可能暗示关系，须与正文核对。缺少关系时可用中性分组或注明未知，不能为填满模板补造连线。

## 2. 选择介质与构图

优先满足用户指定的格式和用途；未指定时按下表选择。组合需求分清各自产物，详见 [介质边界](references/medium.md)。

| 需求 | 路径 |
|---|---|
| 已提供或指定 Mermaid / PlantUML；时序、思维导图、类图、饼图、甘特 | 保留源码，按底座转换为画板；不改写成另一种关系图 |
| 多判断、多回路，需要原生菱形与自动布局 | DSL `dagre` / `diamond`，按官方路线 |
| 架构、分层、关系、精排说明、静态指标图 | UTF-8 SVG + 可识别原生形状 |
| 动画、Tab、动态筛选、交互探索 | `feishu-html-diagram` |
| 真实 UI、照片 | 文档图片 |
| 工作坊拖便签、聚类共创 | 官方空白画板流程 |

构图由关系决定。单卡、连续区域、主线和等权比较都可组织阅读；辅助区域只承载新增信息。配色优先满足品牌、用户与既有视觉身份，再结合文章气质选择预置、改编或自定义方案。无明确线索时才从 Light Technical 起步。

**按当前问题读取参考，不预读整套目录：**

| 当前需要 | 参考 |
|---|---|
| 选关系骨架 / 阅读层级 | [构图选型](references/composition.md)；需要具体骨架时读 [布局语法](references/grammars.md) 对应小节 |
| 决定气质与颜色角色 | [主题选择](references/theme-routing.md)；需要色值时查 [色板](references/palettes.md) |
| 确定字号、间距、对比度和显示宽度 | [视觉系统](references/visual-system.md) |
| 多图统一、共享输入、跨层协作、阶段到指标映射，或学习参考图 | [成套技术图](references/technical-article-figures.md) |
| 来源 → 分析 → 行动，包含反馈或直达 | [语义分区价值链](references/semantic-columns.md) |
| 静态指标 / 基准报告 | [定量报告规则](references/data-report-style.md) |

## 3. 制作本地候选

SVG 路线先读 [介质约束](references/constraints.md)。优先用 `rect / circle / ellipse / text` 与原生 connector；文字保持 UTF-8，不转路径。精排使用显式坐标；字体由画板控制，不声明 `font-family`。

- 有向边标 `data-role="edge"`，用 marker 表达方向；通常使用 `marker-end`。无向关系、轴、分隔线分别标 `spoke / axis / divider`。
- 非白背景的文字声明实际 `data-bg`；白底文字也建议声明，才能被对比度检查覆盖。
- 尺寸按内容和目标显示宽度计算。关系复杂或正文过多时拆图，避免靠缩字容纳。
- 完整 SVG 示例可按需参考 [简洁技术架构](evals/fixtures/human-eval/15-light-architecture.svg) 或 [共享输入与汇合](evals/fixtures/shared-input-decision.svg)；只复用表达方法，实际事实重新填写。

首次使用本地工具时可运行 `bash /resolved/skill-dir/scripts/preflight.sh`。它检查工具可用性，不登录、不创建文档。

## 4. 验证与交付

按 [写入与验证](references/write-verify.md) 执行与介质匹配的检查：SVG 做 `fit_check.py`、`lint_svg.py`、固定版本 parser check、PNG 目视；原生结构与有向边另核对转换结果。DSL / Mermaid / PlantUML 使用各自底座的验证路径。

汇总问题后批量局部修正，再验证受影响部分。错误须修复，warning 须检查并解释；只有当前介质无法保留核心关系或编辑要求时才切换路线。仅有截图时，不能证明原生节点或拖动绑定。

交付前按 [事实与交付复核](references/brief-review.md) 检查事实、层级、密度、色彩语义与可读性。写入请求在候选通过后交给底座；文档中用一句话引出图的论点，回读确认画板处于目标位置。

交付说明包含产物、关键设计取舍、完成的检查和未验证项。**本地渲染、飞书写入、客户端体验、拖动绑定分别记录**；历史认可不覆盖新的内容、样式或 parser。

## 评测与来源

- [行为场景](evals/scenarios.md) / [评测清单](evals/evals.json)：区分待运行场景与已完成样本。
- [Human eval](evals/human-eval.md) / [历史 fixtures](evals/fixtures/human-eval/)：保留逐次证据与未完成项。
- [社区实践](references/community-practice.md) / [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)：吸收范围、来源与许可证。
