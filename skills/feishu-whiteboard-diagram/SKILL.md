---
name: feishu-whiteboard-diagram
description: Use when 飞书/Lark 文档需要新增、改版或审查可二次编辑的原生画板，尤其是架构、流程、分层、枢纽、时间线、泳道、四象限、定性对比或静态质量 / 性能 / 成本基准图；需要动画、筛选、交互探索、真实 UI 或照片时不使用。
metadata:
  author: liyuheng.erik
  requires:
    bins: ["node", "npx", "python3"]
    skills: ["lark-doc", "lark-whiteboard", "lark-shared"]
---

# 飞书画板精美图表

把技术文档里的架构、流程、边界和恢复粒度，画成**飞书原生画板**：读者能在文档里看，同事能点进画板改节点和连线。最终产物是 whiteboard block，不是 PNG，也不是 HTML 小网页。

> **先读底座，再读本文件。** 认证、`--as user`、创建/追加画板、`+export` / `+update`、覆盖确认、Mermaid/PlantUML/SVG/raw 的命令形态，一律按已安装的 [`lark-whiteboard`](https://github.com/larksuite/cli/tree/main/skills/lark-whiteboard) 与 [`lark-shared`](https://github.com/larksuite/cli/tree/main/skills/lark-shared)、[`lark-doc`](https://github.com/larksuite/cli/tree/main/skills/lark-doc) 执行。本 skill **不重写**这些基础用法。

本文件只回答：写文档时要不要画板、画哪种语法、怎样新建/改版/审查文档精排图、本地怎么验得过。

## 权威边界

| 问题 | 以谁为准 |
|---|---|
| 登录、身份、权限、高风险确认、创建/更新/覆盖 | `lark-shared`、`lark-doc`、`lark-whiteboard` |
| 当前 parser 支持什么 | 已安装的 `lark-whiteboard` + 本 skill 的固定版本 parser-contract 测试 |
| 文档解释图的论点、构图、密度、色板和复核 | 本 skill |

本 skill 只能收窄视觉自由度，不能放宽底座的权限与覆盖门禁。发生冲突时，安全和写入规则永远由底座决定。

## 它不是什么

- 不是 `lark-whiteboard` 的替代品，不复制其 CLI、scene 骨架和身份分流表。
- 不是 `feishu-html-diagram`：不需要动画、Tab、D3 时，不要用 HTML5 冒充画板。
- 不是社区 35 套 `design.md` 文件仓库。只保留少量可解释的主题家族，见 [palettes.md](references/palettes.md) 和 [主题路由](references/theme-routing.md)。
- 不是只会画浅色胶囊流程图。按关系选原型：分叉、对比列、枢纽、时间线、泳道、四象限、焦点+细节；技术架构默认白页浅色系统，编辑型概念图才使用奶油底 + 墨边 + 单焦点，见 [composition.md](references/composition.md)。
- `<whiteboard type="mermaid">` 交给飞书服务端转成画板，本 skill 不渲染 Mermaid。

## 适用 / 不适用

| 适用 | 不适用 |
|---|---|
| 技术文档需要可编辑图来解释架构、流程、分层或关系 | 微信 / Notion / 博客配图 → 走对应发布 skill |
| 来源明确、指标精简且需要节点可编辑的静态模型 / 基准对比 | 需要动态筛选或交互探索 → `feishu-html-diagram` |
| 用户给了飞书文档 URL，要求「配图 / 画到画板」 | 真实 UI、照片 → `<img>`（按 `lark-doc`） |
| 已有画板需要保真改版或只读质量审查 | 现场工作坊拖拽、贴便签 → 空白画板，走 `lark-whiteboard` |
| 一张图回答一个论点（职责、流向、恢复什么） | 用户只要文字润色 → `lark-doc` |

同一文档可以有多张画板。一个论点一张图。

## 和官方 SVG 路线的关键分歧

官方 `routes/svg.md` 会劝 agent「打破矩形牢笼」。插画/海报可以那样做。文档精排图则以**可编辑原生形状、8px 节奏、一个由尺寸和留白建立的焦点、条件成立才放页脚结论条**为骨架；技术架构用浅色分组，编辑型概念图才使用饱和色块和硬阴影。装饰 `path` 的可编辑性取决于 parser，结构件默认不用；带 marker 的曲线路径可成为原生 connector。目标是这种气质时，**以本 skill 的视觉和语法为准**，写入仍走 `lark-whiteboard`。社区实践吸收范围见 [community-practice.md](references/community-practice.md)；历史 Human eval 与当前候选状态见 [evals/human-eval.md](evals/human-eval.md)。

## 介质选择（命中即停）

写入方式以 `lark-whiteboard` / `lark-doc` 为准。这里只决定**画什么**。

| 条件 | 画什么 |
|---|---|
| 用户已给出 Mermaid/PlantUML，或图是思维导图 / 时序 / 类图 / 饼图 / 甘特 | 把源码放进 `<whiteboard type="mermaid">`（或 PlantUML），飞书自动转画板；不要重画成 SVG 架构 |
| 判断多、回路多、需要原生菱形，卡片对齐要求一般 | DSL `dagre` + `diamond`，按官方 DSL 路径 |
| 分层条带、多列运行图、编号层级、页脚结论、层间 API 标注；以及分叉 / 定性对比 / 枢纽 / 时间线 / 泳道 / 四象限 / 焦点+细节 | **UTF-8 SVG，只用可识别原生形状** |
| 来源明确、指标精简且需节点可编辑的静态模型评测 / 基准对比 | **UTF-8 SVG + [白页橙灰报告风格](references/data-report-style.md)**；按指标选择配对条形图或主图 + 结论卡片 |
| 需要动画、Tab、动态筛选或交互式数据探索 | `feishu-html-diagram` |
| 真实界面或照片 | 图片 |

精美技术文档图**默认走 SVG**。理由见 [介质边界](references/medium.md)。

## 主题路由（先选气质，再画图）

不要因为“这是技术图”就自动使用 Riso Brut，也不要因为“这是架构图”就把每层都染成不同鲜艳颜色。
先写 [主题路由](references/theme-routing.md) 中的 `article_tone`、`diagram_purpose`、`formality`、`theme` 和 `accent_budget`，必要时用 `scripts/theme_router.py` 复核，
再选择构图。选择优先级是：品牌 / 用户明确指定 → 已有画板视觉身份 → 图的语义 → 文章主题 → `light-technical` 默认。

默认策略：

| 请求 | 默认主题 |
|---|---|
| 技术架构、服务边界、系统拓扑 | `light-technical` / architecture |
| Agent 流程、任务编排、工具回路 | `light-technical` / process |
| 恢复、故障、状态机 | `light-technical` / reliability |
| 性能、质量、成本、模型基准 | `white-report` |
| 创意、品牌、概念型解释 | `coral` / `riso-brut`，只有明确需要编辑感时才用 |

一张图只用一个主主题；`light-technical` 内的成功 / 中断 / 失败是语义状态色，不是额外的主色板。

## 创作 Workflow

先按请求选一条路：

| 请求 | 行动 |
|---|---|
| 新建解释图 | 建事实与设计契约，再走下面 0–4 |
| 改版已有画板 | 先按 `lark-whiteboard` 只读导出；保持未被点名的事实、关系、几何和视觉身份，只改用户指定轴 |
| 只做审查 | 读取现有 SVG/预览/真实画板证据，按 [事实与交付复核](references/brief-review.md) 给结论；用户没要求修就不写回 |

### 0. 底座

1. 读取 `lark-shared`（认证）和 `lark-whiteboard`（创作/编辑 workflow）。
2. 在文档里落画板块、拿 `board_token`：按 `lark-doc` 的画板工作流。
3. 再回到下面 1–4 做精排。缺登录时仍可完成本地 SVG/PNG，不要假装已写入飞书。

```bash
bash /resolved/skill-dir/scripts/preflight.sh
```

### 1. 先写论点，再选语法

每张图只回答一个问题。先按 [事实与交付复核](references/brief-review.md) 写一份不进入画布的简短契约：论点、读者、文章气质、图的用途、来源事实、允许的推断、关系、未知项、主语法、焦点、主题、颜色语义、密度删减。**箭头、数字、角色、状态和因果关系都是事实声明，不得为了填满布局而补造。**

再把实体、关系、顺序、状态对到 [布局语法](references/grammars.md) 和 [构图原型](references/composition.md) 的一种：

1. 分层条带（职责 / 边界）
2. 任务循环 / 流水线分叉（判断 + 放大的工具回路）
3. 学习闭环（上门禁 + 下三列对比）
4. 多列运行架构（请求向右 / 事件向左）
5. 编号层级（恢复粒度）
6. 对比列（谁在这一行更优）
7. 枢纽（一个核心带 N 个方面）
8. 时间线（高潮在哪一段）
9. 泳道（多角色握手）
10. 四象限（两个维度、四个去处）
11. 焦点+细节（一块大卡 + 右侧支持）
12. 定量评测（同尺度指标配对条形图、时间 / 成本双面板，或指标主图 + 结论卡片；细则见 [白页橙灰报告风格](references/data-report-style.md)）

没有合适的就用「标题 + 分区卡片 + 少量语义连线 + 必要时的页脚结论条」现编，不要硬套成均等胶囊流程图。

### 2. 按文档精排上色，并先定焦点

按 [主题路由](references/theme-routing.md) 选择主题，再读取 [视觉系统](references/visual-system.md) 与 [构图](references/composition.md)；不必加载所有色板。定量报告读取 [白页橙灰报告风格](references/data-report-style.md) 与对应色板。技术架构、流程和分层默认使用 **Light Technical**；`Riso Brut` 只在文章明确需要编辑型 / 概念型视觉时使用；定性权衡可用 **Riptide Cobalt**，时间线可用 **Coral**，四象限可用 **Grove**，焦点+细节可用 **Avocado Press**。不要浅灰外框套均等胶囊，也不要让颜色替代结构。

### 3. 写 SVG（精排默认路径）

硬约束和实测映射见 [介质约束](references/constraints.md)。最小骨架：

下面的骨架示范技术文档的 **Light Technical** 默认主题。需要编辑型概念图时，再把画布和焦点换成 [palettes.md](references/palettes.md) 中明确选择的主题；定量报告使用 [White Report](references/data-report-style.md) 的布局和色板。

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 520">
  <defs>
    <marker id="arrow-blue" markerWidth="10" markerHeight="8" refX="9" refY="4"
            orient="auto" markerUnits="userSpaceOnUse">
      <path d="M0 0 L10 4 L0 8 z" fill="#2563EB"/>
    </marker>
  </defs>
  <rect x="0" y="0" width="1600" height="520" fill="#F8FAFC"/>
  <text x="80" y="120" font-size="40" font-weight="700" fill="#1F2937">图表标题：一句话论点</text>
  <text x="80" y="160" font-size="18" fill="#475569">副标题：读者带着什么问题看这张图</text>
  <!-- 技术架构默认：白页、浅色分组、一个蓝色焦点；只用 rect / circle / ellipse / line / polyline / text -->
  <rect x="80" y="224" width="360" height="140" rx="12" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="2"/>
  <text x="104" y="272" font-size="22" font-weight="700" fill="#1F2937">安静步骤</text>
  <text x="104" y="308" font-size="16" fill="#475569">保留结构，降低视觉权重</text>
  <rect x="520" y="208" width="440" height="172" rx="16" fill="#EFF6FF" stroke="#2563EB" stroke-width="2"/>
  <text x="740" y="286" font-size="26" font-weight="700" fill="#1D4ED8" text-anchor="middle" data-bg="#EFF6FF">焦点（最大）</text>
  <text x="740" y="322" font-size="16" fill="#1F2937" text-anchor="middle" data-bg="#EFF6FF">尺寸、留白和边界共同建立层级</text>
  <rect x="1040" y="224" width="440" height="140" rx="12" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="2"/>
  <text x="1064" y="272" font-size="22" font-weight="700" fill="#1F2937">支撑步骤</text>
  <text x="1064" y="308" font-size="16" fill="#475569">颜色只标记有语义的关系</text>
  <line data-role="edge" x1="440" y1="294" x2="520" y2="294"
        stroke="#2563EB" stroke-width="2" marker-end="url(#arrow-blue)"/>
</svg>
```

文件必须 UTF-8。禁止 `font-family`。有向边标 `data-role="edge"` 并用 `marker-end`；无向辐射线、坐标轴和分隔线分别标 `spoke`、`axis`、`divider`。文字落在非白色块上时写 `data-bg="#背景色"`，让 lint 校验对比度。若中文已被写坏，停止并从未损坏源重新生成，不要对乱码做原地“转码修复”。

### 4. 本地审查，然后交给底座写入

```bash
python3 /resolved/skill-dir/scripts/fit_check.py /absolute/path/to/diagram.svg --json
python3 /resolved/skill-dir/scripts/lint_svg.py /absolute/path/to/diagram.svg
npx -y @larksuite/whiteboard-cli@^0.2.13 -i /absolute/path/to/diagram.svg -f svg --check
npx -y @larksuite/whiteboard-cli@^0.2.13 -i /absolute/path/to/diagram.svg -o /absolute/path/to/diagram.png -f svg
```

`fit_check.py`、`lint_svg.py` 与 `--check` 的 error 必须修；外边距和大块空白 warning 需要解释或修正。编号签和明确声明的硬阴影可以是有意重叠；为固定 fixture 记录预期 warning，新增 warning 仍要检查。目视 PNG：截断、贴边、无意重叠、缺箭头、中文豆腐、颜色语义冲突。每轮先汇总问题，批量做一次局部修改，再做一次确认渲染；仍失败时按官方 fallback 丢弃坏 SVG，基于事实契约改走 DSL，不在两个路径间反复横跳。

交付前按 [事实与交付复核](references/brief-review.md) 检查事实、层级、平衡、密度、对比度和对齐。无 `fail`、最多一个 `weak` 才交付；这不会替代真实飞书体验验证。

通过后，用 `lark-whiteboard` 把 SVG/DSL/Mermaid 写入已有 `board_token`。文档正文里先写一句「这张图回答什么」，再放画板块。证据层见 [写入与验证](references/write-verify.md)。

## 评测与来源

- [`evals/scenarios.md`](evals/scenarios.md) 与 [`evals/evals.json`](evals/evals.json) — 行为评测场景；未运行时不得写成通过
- [`evals/human-eval.md`](evals/human-eval.md) 与 [`evals/fixtures/human-eval/`](evals/fixtures/human-eval/) — 飞书体验记分卡与候选图
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) — 社区来源、吸收范围与许可证声明
