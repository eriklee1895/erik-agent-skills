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
- 不是社区 35 套 `design.md` 文件仓库。色板只精选 7 套，见 [palettes.md](references/palettes.md)。
- 不是只会画浅色胶囊流程图。按关系选原型：分叉、对比列、枢纽、时间线、泳道、四象限、焦点+细节；概念图默认奶油底 + 墨边 + 单焦点，定量评测图可选白页橙灰报告风格，见 [composition.md](references/composition.md)。
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

官方 `routes/svg.md` 会劝 agent「打破矩形牢笼」。插画/海报可以那样做。文档精排图则以**直角墨边卡片、一个更大的饱和焦点、条件成立才放页脚结论条**为骨架；分层图才用浅色分组圆角。装饰 `path` 的可编辑性取决于 parser，结构件默认不用；带 marker 的曲线路径可成为原生 connector。目标是这种气质时，**以本 skill 的视觉和语法为准**，写入仍走 `lark-whiteboard`。历史 Human eval 与当前候选状态见 [evals/human-eval.md](evals/human-eval.md)。

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

每张图只回答一个问题。先按 [事实与交付复核](references/brief-review.md) 写一份不进入画布的简短契约：论点、读者、来源事实、允许的推断、关系、未知项、主语法、焦点、色板、密度删减。**箭头、数字、角色、状态和因果关系都是事实声明，不得为了填满布局而补造。**

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

按选定模式读取视觉参考，不必加载所有色板。概念图读取 [视觉系统](references/visual-system.md) 与 [构图](references/composition.md)，再选一套色板；定量报告读取 [白页橙灰报告风格](references/data-report-style.md) 与对应色板。概念图中循环 / 分叉 / 枢纽默认 **Riso Brut**，定性权衡用 **Riptide Cobalt**，时间线可用 **Coral**，四象限用 **Grove**，焦点+细节可用 **Avocado Press**。分层条带才用浅色分组。不要浅灰外框套均等胶囊。

### 3. 写 SVG（精排默认路径）

硬约束和实测映射见 [介质约束](references/constraints.md)。最小骨架：

下面的骨架只示范 **Riso Brut 概念图**。定量报告使用 [White Report](references/data-report-style.md) 的布局和色板，不要沿用这里的奶油底与粗墨边。

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 820">
  <defs>
    <marker id="arrow-ink" markerWidth="10" markerHeight="8" refX="9" refY="4"
            orient="auto" markerUnits="userSpaceOnUse">
      <path d="M0 0 L10 4 L0 8 z" fill="#0F0F0F"/>
    </marker>
  </defs>
  <rect x="0" y="0" width="1600" height="820" fill="#EFE9D9"/>
  <text x="80" y="80" font-size="40" font-weight="700" fill="#0F0F0F">图表标题：一句话论点</text>
  <text x="80" y="122" font-size="18" fill="#2A2A2A">副标题：读者带着什么问题看这张图</text>
  <!-- 只用 rect / circle / ellipse / line / polyline / text；默认 rx=0。菱形可用 polygon，但会变成嵌入 SVG 节点 -->
  <rect x="90" y="186" width="360" height="140" fill="#E85A1F"/>
  <rect x="80" y="176" width="360" height="140" fill="#E85A1F" stroke="#0F0F0F" stroke-width="4"/>
  <text x="260" y="240" font-size="24" font-weight="700" fill="#0F0F0F"
        text-anchor="middle" data-bg="#E85A1F">焦点（最大）</text>
  <rect x="500" y="200" width="280" height="100" fill="#FFFFFF" stroke="#0F0F0F" stroke-width="4"/>
  <text x="520" y="244" font-size="18" font-weight="700" fill="#0F0F0F">安静步骤</text>
  <line data-role="edge" x1="440" y1="246" x2="500" y2="246"
        stroke="#0F0F0F" stroke-width="3" marker-end="url(#arrow-ink)"/>
</svg>
```

文件必须 UTF-8。禁止 `font-family`。有向边标 `data-role="edge"` 并用 `marker-end`；无向辐射线、坐标轴和分隔线分别标 `spoke`、`axis`、`divider`。文字落在非白色块上时写 `data-bg="#背景色"`，让 lint 校验对比度。若中文已被写坏，停止并从未损坏源重新生成，不要对乱码做原地“转码修复”。

### 4. 本地审查，然后交给底座写入

```bash
python3 /resolved/skill-dir/scripts/lint_svg.py /absolute/path/to/diagram.svg
npx -y @larksuite/whiteboard-cli@^0.2.13 -i /absolute/path/to/diagram.svg -f svg --check
npx -y @larksuite/whiteboard-cli@^0.2.13 -i /absolute/path/to/diagram.svg -o /absolute/path/to/diagram.png -f svg
```

`lint_svg.py` 与 `--check` 的 error 必须修。编号签和硬阴影可以是有意重叠；为固定 fixture 记录预期 warning，新增 warning 仍要检查。目视 PNG：截断、贴边、无意重叠、缺箭头、中文豆腐。每轮先汇总问题再做一次局部修改，最多两轮；仍失败时按官方 fallback 丢弃坏 SVG，基于事实契约改走 DSL，不在两个路径间反复横跳。

交付前按 [事实与交付复核](references/brief-review.md) 检查事实、层级、平衡、密度、对比度和对齐。无 `fail`、最多一个 `weak` 才交付；这不会替代真实飞书体验验证。

通过后，用 `lark-whiteboard` 把 SVG/DSL/Mermaid 写入已有 `board_token`。文档正文里先写一句「这张图回答什么」，再放画板块。证据层见 [写入与验证](references/write-verify.md)。

## 评测与来源

- [`evals/scenarios.md`](evals/scenarios.md) 与 [`evals/evals.json`](evals/evals.json) — 行为评测场景；未运行时不得写成通过
- [`evals/human-eval.md`](evals/human-eval.md) 与 [`evals/fixtures/human-eval/`](evals/fixtures/human-eval/) — 飞书体验记分卡与候选图
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) — 社区来源、吸收范围与许可证声明
