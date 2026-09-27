# 色板（精选，不搬 35 套文件）

社区 `beautiful-feishu-whiteboard` 有 35 套换肤模板；`feishu-whiteboard-pro` 的样板用其中几套把构图做出来。
本 skill **不复制**那些 `templates/*/design.md`。这里只留 8 个可解释的主题家族：一个技术文档默认主题、五个概念 / 决策主题、一个时间线主题，以及一套定量报告主题。
2026-09-03 的上一版曾获 Human eval **Accept**；该结论不覆盖新增的 White Report。新模式的实际飞书体验仍待评审；不要把旧结论写成新色板的通过证据，也不要扩成 35 套或退回全蓝 pastel 流程图。
选气质，不要把多套色板同时涂在一张图上。

默认：技术架构、流程、分层和系统边界用 **Light Technical**。定性权衡用 **Riptide Cobalt**。量化评测与基准报告用 **White Report**。时间线可用 **Coral**。四象限用 **Grove**。焦点+细节可用 **Avocado Press**。只有文章明确需要编辑型 / 概念型视觉时，循环、分叉、枢纽才使用 **Riso Brut**。

## 怎么选

| 气质 | 用 | 不要 |
|---|---|---|
| 技术架构、系统边界、流程说明 | Light Technical | 把整层涂成饱和色、把绿色误当成功态 |
| 文章明确需要编辑型 / 概念型视觉 | Riso Brut | 把编辑型海报风当成技术图默认 |
| 定性权衡 / 选项对比 | Riptide Cobalt | 每格一种颜色 |
| 模型评测、性能 / 成本基准 | White Report | 不同单位共用坐标轴、用颜色暗示未经说明的结论 |
| 温暖一点的闭环 / 时间线 | Coral | 霓虹 |
| 白页双色、一块大焦点 | Avocado Press | 四色全开、均等四宫格 |
| 白页双色、偏品牌 | Pin & Paper | 白贴白没描边 |
| 更克制、决策四象限 | Grove | 海报大字铺满 |

一张图只用一套主色板。Light Technical、White Report、Avocado Press、Pin & Paper 用白或近白底；Riso / Coral / Riptide 用奶油底；Grove 用羊皮纸底。Light Technical 结构靠边界、位置、字号和浅色分组，普通边框 1.5–2px，不使用硬阴影；编辑型概念图才使用 3–4px 墨边和声明过的硬阴影。14–18px 普通文字与背景至少 4.5:1；≥24px 或 ≥19px/700 的大字至少 3:1。SVG 中用 `data-bg` 交给 lint 复核。

## Light Technical（技术文档默认）

这是面向技术文章、架构设计、服务边界和 Agent 运行图的中性浅色主题。它把“颜色是语义”的原则放在“颜色好看”之前。

| Token | Hex | 用法 |
|---|---|---|
| canvas | `#F8FAFC` | 画布 |
| surface | `#FFFFFF` | 普通节点 / 卡片 |
| group | `#F1F5F9` | 分组容器，不表示成功或失败 |
| ink | `#1F2937` | 标题、正文、默认连线 |
| muted | `#475569` | 副标题、辅助说明 |
| border | `#CBD5E1` | 普通边框和分隔线 |
| accent | `#2563EB` | 当前主边界、请求链、焦点边框 |
| accent-soft | `#EFF6FF` | 主分组浅底 |
| context | `#7C3AED` / `#F5F3FF` | 上下文 / 会话，需要时才启用 |
| success | `#16A34A` / `#ECFDF5` | 成功状态 |
| warning | `#D97706` / `#FFF7ED` | 中断 / 预警状态 |
| failure | `#DC2626` / `#FEF2F2` | 失败 / 熔断状态 |

默认剂量：大部分面积是 `canvas` / `surface`；分组用浅底；一张图最多一个主强调色，状态图才按状态语义启用浅绿 / 浅黄 / 浅红。
普通文字用 `ink`，不要让中亮度色块承载小字号正文。边框颜色、位置、编号和连线必须在去色后仍能说明结构。

## Riso Brut（编辑型解释图）

| Token | Hex | 用法 |
|---|---|---|
| cream | `#EFE9D9` | 画布 |
| cream-2 | `#E4DCC4` | 次级底 |
| ink | `#0F0F0F` | 边框、正文、默认连线、默认硬阴影 |
| green | `#167342` | 主强调 / 成功；奶油字 4.86:1 |
| orange | `#E85A1F` | 焦点阴影或判断色块；小字用墨色，不用奶油色 |
| pink | `#F06CA8` | 第二强调，少用 |
| yellow | `#F5C518` | 编号、点 |

硬阴影：同形状副本偏移 **+10px**，无 blur。卡片 `stroke-width="4"`，连线 `3`，圆角默认 **0**。焦点块用饱和填充 + 奶油/白字，且 **比邻居大**。

## Coral

cream `#F5F0E8` · coral `#E85D5D` · ink `#1A1A1A` · white `#FFFFFF`。白卡片坐在奶油底上，珊瑚作顶边 4px 或整块焦点；珊瑚块上的小字用 ink。

## White Report（定量评测 / 报告）

| Token | Hex | 用法 |
|---|---|---|
| canvas | `#FFFFFF` | 画布 |
| ink | `#171717` | 标题、正文、橙色条内的小字号标签 |
| muted | `#777773` | 副标题、辅助说明；白底对比度 4.50:1 |
| orange | `#F36B2B` | 候选系列、重点条形和标题记号；不自动表示更优 |
| orange-text | `#B5471D` | 白底上的小字号橙色标签；对比度 5.41:1 |
| orange-soft | `#FFF0E8` | 主结论卡片的浅色底 |
| baseline | `#D9D9D9` | 基线系列 |
| grid | `#E9E9E5` | 坐标网格和细分隔线 |
| border | `#D9D9D4` | 面板细边 |

不要在 `#F36B2B` 条形上用白色小字；用 ink 保持对比度。若需额外状态色，先明确它表达的业务含义，并遵守同一套对比度门槛。

## Riptide Cobalt

cream `#FDF0E0` · cobalt `#375DFE` · ink `#1A2240` · paper `#FFFFFF`。严格双色。对比表里「该行更优」用钴色块。

## Avocado Press

white `#FFFFFF` · blue `#0055A4` · lime `#DCF4A2`。白页双色；字在白底上用蓝，不要用 lime 当小字。

## Pin & Paper

white `#FFFFFF` · cobalt `#2A3C99` · yellow `#F1E84E`。白卡片必须有 2–3px 蓝边，否则白贴白。

## Grove

parchment `#E8E4D6` · forest `#192B1B` · terracotta `#B0443E`。最克制，适合正式评审；浅字对 terracotta ≥4.5:1。

## 和浅色分组色板的关系

[visual-system.md](visual-system.md) 的蓝/紫/橙/绿浅底，只留给 **分层条带、编号层级** 这种「每一层一种职责色」的图。
循环、对比、枢纽、时间线不要再用那套均等胶囊，否则会画成 draw.io。
