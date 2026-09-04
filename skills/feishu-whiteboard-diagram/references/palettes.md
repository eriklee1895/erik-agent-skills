# 色板（从社区精选，不搬 35 套文件）

社区 `beautiful-feishu-whiteboard` 有 35 套换肤模板；`feishu-whiteboard-pro` 的样板用其中几套把构图做出来。
本 skill **不复制**那些 `templates/*/design.md`。这里只留 6 套已核对、适合技术说明图的色板。
2026-09-03 的上一版曾获 Human eval **Accept**。当前色板为满足小字对比度已做收敛，须按 [human-eval.md](../evals/human-eval.md) 重新确认飞书体验；不要扩成 35 套，也不要退回全蓝 pastel 流程图。
选气质，不要 6 套同时涂在一张图上。

默认：循环、分叉、枢纽用 **Riso Brut**。对比列用 **Riptide Cobalt**。时间线可用 **Coral**。四象限用 **Grove**。焦点+细节可用 **Avocado Press**。分层协议图仍可用浅色分组色板。

## 怎么选

| 气质 | 用 | 不要 |
|---|---|---|
| 技术说明、流程、系统图 | Riso Brut | 全蓝 pastel 流程图 |
| 权衡 / 对比表 | Riptide Cobalt | 每格一种颜色 |
| 温暖一点的闭环 / 时间线 | Coral | 霓虹 |
| 白页双色、一块大焦点 | Avocado Press | 四色全开、均等四宫格 |
| 白页双色、偏品牌 | Pin & Paper | 白贴白没描边 |
| 更克制、决策四象限 | Grove | 海报大字铺满 |

一张图 2–3 个强调色。画布不要纯白（Riso / Coral / Riptide 用奶油底）。结构靠色块和 3–4px 墨边，不要靠浅灰外框。14–18px 普通文字与背景至少 4.5:1；≥24px 或 ≥19px/700 的大字至少 3:1。SVG 中用 `data-bg` 交给 lint 复核。

## Riso Brut（默认 · 解释图）

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
