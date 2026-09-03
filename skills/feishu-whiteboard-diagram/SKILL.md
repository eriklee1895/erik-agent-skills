---
name: feishu-whiteboard-diagram
description: Use when 需要在飞书文档中插入可二次编辑的精美画板图表（分层架构、任务循环、多列运行图、编号层级、学习闭环等）。本 skill 是叠在 lark-whiteboard 上的文档精排方法论，不教画板 CLI。不适用于动画/交互 HTML Diagram，也不替代 lark-whiteboard / lark-doc / lark-shared。
metadata:
  author: liyuheng.erik
  requires:
    bins: ["npx"]
    skills: ["lark-doc", "lark-whiteboard", "lark-shared"]
---

# 飞书画板精美图表

把技术文档里的架构、流程、边界和恢复粒度，画成**飞书原生画板**：读者能在文档里看，同事能点进画板改节点和连线。最终产物是 whiteboard block，不是 PNG，也不是 HTML 小网页。

> **先读底座，再读本文件。** 认证、`--as user`、创建/追加画板、`+export` / `+update`、覆盖确认、Mermaid/PlantUML/SVG/raw 的命令形态，一律按已安装的 [`lark-whiteboard`](https://github.com/larksuite/cli/tree/main/skills/lark-whiteboard) 与 [`lark-shared`](https://github.com/larksuite/cli/tree/main/skills/lark-shared)、[`lark-doc`](https://github.com/larksuite/cli/tree/main/skills/lark-doc) 执行。本 skill **不重写**这些基础用法。

本文件只回答：写文档时要不要画板、画哪种语法、怎样才算你截图那种精排、本地怎么验得过。

## 它不是什么

- 不是 `lark-whiteboard` 的替代品，不复制其 CLI、scene 骨架和身份分流表。
- 不是 `feishu-html-diagram`：不需要动画、Tab、D3 时，不要用 HTML5 冒充画板。
- 不是社区 35 套换肤色板，也不自己实现 Mermaid 渲染。`<whiteboard type="mermaid">` 交给飞书服务端转成画板。
- 社区 `beautiful-feishu-whiteboard` / `feishu-whiteboard-pro` 只吸收 **介质硬规则 + 构图纪律**（原生形状、焦点靠尺寸、反均等卡片），不搬 35 套 `design.md`。

## 适用 / 不适用

| 适用 | 不适用 |
|---|---|
| 写飞书文档时插入架构、流程、闭环、多列运行图、编号层级 | 微信 / Notion / 博客配图 → 走对应发布 skill |
| 需要同事在飞书里继续改节点和连线 | 需要动画、交互、探索式数据 → `feishu-html-diagram` |
| 一张图回答一个论点（职责、流向、恢复什么） | 现场工作坊贴便签 → 空白画板，走 `lark-whiteboard` |
| 用户给了飞书文档 URL，要求「配图 / 画到画板」 | 真实 UI、照片 → `<img>`（按 `lark-doc`） |

同一文档可以有多张画板。一个论点一张图。

## 和官方 SVG 路线的关键分歧

官方 `routes/svg.md` 会劝 agent「打破矩形牢笼」。插画/海报可以那样做。你要的文档精排图，骨架就是**圆角卡片、色边分组、编号签、页脚结论条**。装饰 `path` 会被打成不可编辑的嵌入图。目标是这种气质时，**以本 skill 的视觉和语法为准**，写入仍走 `lark-whiteboard`。

## 介质选择（命中即停）

写入方式以 `lark-whiteboard` / `lark-doc` 为准。这里只决定**画什么**。

| 条件 | 画什么 |
|---|---|
| 用户已给出 Mermaid/PlantUML，或图是思维导图 / 时序 / 类图 / 饼图 / 甘特 | 把源码放进 `<whiteboard type="mermaid">`（或 PlantUML），飞书自动转画板；不要重画成 SVG 架构 |
| 判断多、回路多、需要原生菱形，卡片对齐要求一般 | DSL `dagre` + `diamond`，按官方 DSL 路径 |
| 分层条带、多列运行图、编号层级、页脚结论、层间 API 标注 | **UTF-8 SVG，只用可识别原生形状** |
| 需要运动、Tab、D3 | `feishu-html-diagram` |
| 真实界面或照片 | 图片 |

精美技术文档图**默认走 SVG**。理由见 [介质边界](references/medium.md)。

## 创作 Workflow

### 0. 底座

1. 读取 `lark-shared`（认证）和 `lark-whiteboard`（创作/编辑 workflow）。
2. 在文档里落画板块、拿 `board_token`：按 `lark-doc` 的画板工作流。
3. 再回到下面 1–4 做精排。缺登录时仍可完成本地 SVG/PNG，不要假装已写入飞书。

```bash
bash /resolved/skill-dir/scripts/preflight.sh
```

### 1. 先写论点，再选语法

每张图只回答一个问题。把实体、关系、顺序、状态写成短列表，对到 [布局语法](references/grammars.md) 的一种：

1. 分层条带（职责 / 边界）
2. 任务循环（判断 + 回填）
3. 学习闭环（并行落盘）
4. 多列运行架构（请求向右 / 事件向左）
5. 编号层级（恢复粒度）

没有合适的就用「标题 + 分区卡片 + 少量语义连线 + 页脚结论条」现编，不要硬套。

### 2. 按文档精排上色，并先定焦点

见 [视觉系统](references/visual-system.md) 和 [构图](references/composition.md)。最低要求：浅底 + 同色深边框分组；组内白卡片；蓝=动作、紫=上下文、橙=判断、绿=产出；默认连线灰，只有上行/下行/是/否/回填才彩色；标题是论点，页脚是结论；画布上不要出现 prompt 或风格名。

构图先定 **哪一个节点最大**。染色但和邻居一样大，读者看起来仍是草稿流程图。回填/下一轮用最短正交虚线，不要绕画板外框。列容器高度跟着内容走，不要先画高壳再把卡片贴在顶和底。

### 3. 写 SVG（精排默认路径）

硬约束和实测映射见 [介质约束](references/constraints.md)。最小骨架：

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 820">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="9" refY="4"
            orient="auto" markerUnits="strokeWidth">
      <path d="M0 0 L10 4 L0 8 z"/>
    </marker>
  </defs>
  <text x="40" y="48" font-size="24" font-weight="700" fill="#1F2329">图表标题：一句话论点</text>
  <text x="40" y="76" font-size="14" fill="#64748B">副标题：读者带着什么问题看这张图</text>
  <!-- 只用 rect / circle / ellipse / line / polyline / text；菱形可用 polygon，但会变成嵌入 SVG 节点 -->
  <rect x="40" y="120" width="1360" height="160" rx="16" fill="#EFF6FF" stroke="#2563EB" stroke-width="2"/>
  <line x1="200" y1="200" x2="320" y2="200" stroke="#94A3B8" stroke-width="2" marker-end="url(#arrow)"/>
</svg>
```

文件必须 UTF-8。禁止 `font-family`。箭头只用 `marker-end`。当前写入工具若弄坏 XML 中文，改用 `Path.write_text(..., encoding="utf-8")`。

### 4. 本地审查，然后交给底座写入

```bash
python3 /resolved/skill-dir/scripts/lint_svg.py /absolute/path/to/diagram.svg
npx -y @larksuite/whiteboard-cli@^0.2.13 -i /absolute/path/to/diagram.svg -f svg --check
npx -y @larksuite/whiteboard-cli@^0.2.13 -i /absolute/path/to/diagram.svg -o /absolute/path/to/diagram.png -f svg
```

`--check` 的 error 必须修。编号签压层边框可以是有意重叠。目视 PNG：截断、贴边、无意重叠、缺箭头、中文豆腐，改源文件再渲，最多两轮，不要整张重写。

通过后，用 `lark-whiteboard` 把 SVG/DSL/Mermaid 写入已有 `board_token`。文档正文里先写一句「这张图回答什么」，再放画板块。证据层见 [写入与验证](references/write-verify.md)。

## 相关文件

- [`references/medium.md`](references/medium.md) — 画板 / Mermaid / HTML5 / 图片，以及和官方 skill 的分工
- [`references/grammars.md`](references/grammars.md) — 五种文档精排布局语法
- [`references/composition.md`](references/composition.md) — 间距、字号阶梯、焦点靠尺寸、反套路
- [`references/visual-system.md`](references/visual-system.md) — 色板、字号、间距
- [`references/constraints.md`](references/constraints.md) — 社区经验 + 实测映射
- [`references/write-verify.md`](references/write-verify.md) — 本地验和证据层；写入命令回官方 skill
- [`scripts/lint_svg.py`](scripts/lint_svg.py) — SVG 介质预检
- [`scripts/preflight.sh`](scripts/preflight.sh) — 运行时依赖
- [`evals/scenarios.md`](evals/scenarios.md) — 行为场景
- [`evals/human-eval.md`](evals/human-eval.md) — 飞书 Web/桌面记分卡
- [`evals/fixtures/human-eval/`](evals/fixtures/human-eval/) — 五种语法 + Mermaid/HTML/空白板评测包
