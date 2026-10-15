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

本 skill 规定事实、可读性、语义一致性和可编辑性的质量要求；配色与构图由 agent 结合文章自主选择。它不能放宽底座的权限与覆盖门禁。

## 它不是什么

- 不是 `lark-whiteboard` 的替代品，不复制其 CLI、scene 骨架和身份分流表。
- 不是 `feishu-html-diagram`：不需要动画、Tab、D3 时，不要用 HTML5 冒充画板。
- 不是社区 35 套 `design.md` 文件仓库。只保留少量可解释的主题家族，见 [palettes.md](references/palettes.md) 和 [主题路由](references/theme-routing.md)。
- 按关系选原型：分叉、对比列、枢纽、时间线、泳道、四象限、焦点+细节。原型提供结构参考，不绑定色板、唯一大卡或页脚，见 [composition.md](references/composition.md)。
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

官方 `routes/svg.md` 会劝 agent「打破矩形牢笼」。文档解释图则优先保证**可编辑原生形状、稳定间距、清楚的阅读层级与关系**。阅读重心可以是单卡、相邻区域、主线或等权比较；辅助区域按内容选择结论、边界、步骤、来源，或省略。饱和色与硬阴影是否合适，由文章气质和可读性决定。装饰 `path` 的可编辑性取决于 parser，结构件默认不用；带 marker 的曲线路径可成为原生 connector。写入仍走 `lark-whiteboard`。社区实践吸收范围见 [community-practice.md](references/community-practice.md)；历史 Human eval 与当前候选状态见 [evals/human-eval.md](evals/human-eval.md)。

## 介质选择（命中即停）

写入方式以 `lark-whiteboard` / `lark-doc` 为准。这里只决定**画什么**。

| 条件 | 画什么 |
|---|---|
| 用户已给出 Mermaid/PlantUML，或图是思维导图 / 时序 / 类图 / 饼图 / 甘特 | 把源码放进 `<whiteboard type="mermaid">`（或 PlantUML），飞书自动转画板；不要重画成 SVG 架构 |
| 判断多、回路多、需要原生菱形，卡片对齐要求一般 | DSL `dagre` + `diamond`，按官方 DSL 路径 |
| 分层条带、多列运行图、编号层级、页脚结论、层间 API 标注；以及分叉 / 定性对比 / 枢纽 / 时间线 / 泳道 / 四象限 / 焦点+细节 | **UTF-8 SVG，只用可识别原生形状** |
| 来源明确、指标精简且需节点可编辑的静态模型评测 / 基准对比 | **UTF-8 SVG + [定量报告规则](references/data-report-style.md)**；配色按品牌与文章选择，按指标选版式 |
| 需要动画、Tab、动态筛选或交互式数据探索 | `feishu-html-diagram` |
| 真实界面或照片 | 图片 |

精美技术文档图**默认走 SVG**。理由见 [介质边界](references/medium.md)。

## 视觉选择（质量底线 + 自主设计 + 参考色板）

先遵守用户 / 品牌要求，改版保留已有视觉身份；再结合文章气质、读者、图的用途与信息密度自主决定配色和层级。可以直接用预置、改编预置，也可以设计新配色；主题名不是允许列表。线索不足时才以 Light Technical 为起点。

按 [选择方法](references/theme-routing.md) 记录简短的视觉理由与颜色角色；[色板目录](references/palettes.md) 提供 8 个可选家族、搭配和验证状态。单强调色、角色分区色、状态色、数据系列色都可正常选择；颜色数量取决于表达任务，不固定为一个。可用 `scripts/theme_router.py --theme <选定名称>` 记录选择；脚本未给选择时只提供建议，不审批准入。

不论是否使用预置，均需通过同一套事实、对比度、文字适配、原生转换和目视检查。预置的局部通过证据不自动覆盖改色后的图，也不代表已获飞书体验认可。

## 创作 Workflow

先按请求选一条路：

| 请求 | 行动 |
|---|---|
| 新建解释图 | 建事实与设计契约，再走下面 0–4 |
| 改版已有画板 | 先按 `lark-whiteboard` 只读导出；保持未被点名的事实、关系、几何和视觉身份，只改用户指定轴 |
| 只做审查 | 读取现有 SVG/预览/真实画板证据，按 [事实与交付复核](references/brief-review.md) 给结论；用户没要求修就不写回 |

### 0. 底座

1. 读取 `lark-shared`（认证）和 `lark-whiteboard`（创作/编辑 workflow）。
2. 先做下面 1–4 的设计和本地审查；本地准备不需要 `board_token`，用户要求暂不写飞书时到本地产物为止。
3. 已授权写入且本地审查通过后，再按 `lark-doc` 的画板工作流创建画板块、拿 `board_token`；改版复用已有 token。缺登录时仍可完成本地 SVG/PNG，不要假装已写入飞书。

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
6. 对比列（选项、差异或权衡；可中性比较）
7. 枢纽（一个核心带 N 个方面）
8. 时间线（高潮在哪一段）
9. 泳道（多角色握手）
10. 四象限（两个维度、四个去处）
11. 焦点+细节（一块大卡 + 右侧支持）
12. 定量评测（同尺度指标配对条形图、时间 / 成本双面板，或指标主图 + 结论卡片；细则见 [定量报告规则](references/data-report-style.md)）
13. 语义分区价值链（来源 → 两层分析 → 行动；来源明确给出回流、直达和落地顺序时，见 [semantic-columns.md](references/semantic-columns.md)）

没有合适的就按实体与关系自定结构。等权对比可以等大，主线可以承担阅读重心；辅助区域只保留读者需要的新信息。

### 2. 选择配色与阅读层级

按 [选择方法](references/theme-routing.md) 判断气质与颜色角色，再读取 [视觉系统](references/visual-system.md) 和相关 [构图](references/composition.md)。预置可从 [色板目录](references/palettes.md) 选一两套比较，不必加载完整模板库；新配色也按实际前景 / 背景组合检查。定量报告另外读取 [数据规则](references/data-report-style.md)，系列颜色可适配品牌。确定读者先看哪里、如何比较、最后带走什么，不要求每图有一张最大卡或固定页脚。

### 3. 写 SVG（精排默认路径）

硬约束和实测映射见 [介质约束](references/constraints.md)。最小骨架：

下面只示范 **Light Technical + 单卡重心** 的一种组合。可按文章选择其它预置或自定义配色，也可采用区域、主线或等权比较的层级；代码中的颜色和卡片尺寸不是全局规则。

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
  <!-- 示例组合：近白页、蓝色主卡；其它视觉选择遵循同样的原生形状约束 -->
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

文件必须 UTF-8。禁止 `font-family`。有向边标 `data-role="edge"` 并用 `marker-end`；无向关系线（含辐射）、坐标轴和分隔线分别标 `spoke`、`axis`、`divider`。文字落在非白色块上时写 `data-bg="#背景色"`，让 lint 校验对比度。若中文已被写坏，停止并从未损坏源重新生成，不要对乱码做原地“转码修复”。

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
