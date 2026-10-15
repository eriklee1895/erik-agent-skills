# 配色家族：可选预置与验证状态

这里保留 8 个参考家族。它们是自主设计的起点，可以直接采用、改编或跳过；`theme` 允许自定义名称。先按 [选择方法](theme-routing.md) 判断文章气质、读者与颜色任务，再挑需要的条目，不必加载完整模板库。

## 选型索引

| 家族 | 气质与颜色关系 | 可尝试的场景 | 文字搭配 |
|---|---|---|---|
| Light Technical | 近白、蓝灰、轻边界 | 克制的说明或系统边界 | 深灰配近白；白字配深蓝 |
| Riso Brut | 奶油、墨色、绿 / 橙，可有硬阴影 | 表现力较强的概念解释 | 奶油字配深绿；橙底配墨字 |
| Coral | 奶油、珊瑚、深墨 | 温暖叙事、时间线、技术随笔 | 珊瑚底配墨字 |
| White Report | 白、灰、橙色系列 | 静态报告，可改为品牌系列色 | 橙条内深字，白底标签用深橙 |
| Riptide Cobalt | 奶油、钴蓝、深墨 | 清晰对比、结构说明 | 白字配钴蓝；深墨配奶油 |
| Avocado Press | 白、深蓝、浅 lime | 清爽说明、局部强调 | 深蓝配白 / lime；白字配深蓝 |
| Pin & Paper | 白、钴蓝、浅黄 | 有识别度的轻快排版 | 深蓝配白 / 黄 |
| Grove | 羊皮纸、森林绿、陶土 | 温暖克制的技术、治理或评审文章 | 森林绿配羊皮纸；浅字配陶土 |

场景是建议，同一张架构图或时间线都可以使用不同家族。整个图保持一致的背景、文字、边框与角色映射；一致性不等于固定双色或固定一个强调色。

## 验证状态与使用范围

2026-10-15 重新计算下文声明的小字配对，均以未舍入值达到 4.5:1；这只覆盖指定配对。计算使用 [lint_svg.py](../scripts/lint_svg.py) 的对比度实现，不证明整张图的观感。

| 家族 | 本次配对最低对比度（约） | 现有可运行构图样例 / 本地证据 | 飞书体验状态 |
|---|---|---|---|
| Light Technical | 5.17:1 | [15-light-architecture.svg](../evals/fixtures/human-eval/15-light-architecture.svg)；[semantic-value-chain.svg](../evals/fixtures/semantic-value-chain.svg) 是角色色改编，另有本地记录 | 当前样例未获逐图体验认可 |
| Riso Brut | 4.86:1 | [02-task-loop.svg](../evals/fixtures/human-eval/02-task-loop.svg)，有 2026-09-04 本地渲染记录 | 历史整体 Qualitative Accept，不覆盖当前版本 |
| Coral | 5.10:1 | [11-timeline.svg](../evals/fixtures/human-eval/11-timeline.svg)，有 2026-09-04 本地渲染记录 | 历史整体 Qualitative Accept，不覆盖当前版本 |
| White Report | 4.56:1 | 本目录仅配色与 [报告规则](data-report-style.md)，尚无固定构图 fixture | 无当前体验证据 |
| Riptide Cobalt | 5.05:1 | [09-comparison.svg](../evals/fixtures/human-eval/09-comparison.svg)，有 2026-09-04 本地渲染记录 | 历史整体 Qualitative Accept，不覆盖当前版本 |
| Avocado Press | 6.17:1 | [14-focus-detail.svg](../evals/fixtures/human-eval/14-focus-detail.svg)，有 2026-09-04 本地渲染记录 | 历史整体 Qualitative Accept，不覆盖当前版本 |
| Pin & Paper | 7.44:1 | 配色配对已检查，尚无固定构图 fixture | 无当前体验证据 |
| Grove | 4.96:1 | [13-quadrant.svg](../evals/fixtures/human-eval/13-quadrant.svg)，有 2026-09-04 本地渲染记录 | 历史整体 Qualitative Accept，不覆盖当前版本 |

历史本地证据见 [current-local-evidence.md](../evals/fixtures/human-eval/current-local-evidence.md)，历史人工结论及其边界见 [human-eval.md](../evals/human-eval.md)。不能把一轮整体认可写成逐家族或所有新图“验证过好看”；修改配色、构图或 parser 后按当前产物重验。

普通小字对比度 ≥4.5:1；≥24px 或 ≥19px/700 的大字 ≥3:1。`data-bg` 声明实际背景；原生形状与 parser 边界保持不变。自定义配色与预置使用相同质量要求，不增加额外许可步骤。

## Light Technical（中性浅色）

近白底、深正文、轻边框，适合克制说明。蓝色是这套预置的强调色，可按文章改编；它不是技术图必须使用的颜色。

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

示例剂量：大部分面积是 `canvas` / `surface`；分组用浅底。按阅读任务选择单强调色、协调角色色、状态色或数据系列色；固定角色映射比固定颜色数量更重要。
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

参考表现：同形状副本偏移约 **+10px** 的实心硬阴影、约 4px 墨边和方角，可增强编辑感。可减少线宽或阴影来适应文章；大色块用何种文字色按实际对比度决定，橙色上的小字用 ink。阅读层级也可以靠位置、留白和主线建立。

## Coral

cream `#F5F0E8` · coral `#E85D5D` · ink `#1A1A1A` · white `#FFFFFF`。白卡片坐在奶油底上，珊瑚作顶边 4px 或整块焦点；珊瑚块上的小字用 ink。

## White Report（定量评测 / 报告）

| Token | Hex | 用法 |
|---|---|---|
| canvas | `#FFFFFF` | 画布 |
| ink | `#171717` | 标题、正文、橙色条内的小字号标签 |
| muted | `#767672` | 副标题、辅助说明；白底对比度约 4.56:1，按未舍入值通过 4.5 门槛 |
| orange | `#F36B2B` | 示例中的候选系列、条形和标题记号；可用品牌色替换，不自动表示更优 |
| orange-text | `#B5471D` | 白底上的小字号橙色标签；对比度 5.41:1 |
| orange-soft | `#FFF0E8` | 主结论卡片的浅色底 |
| baseline | `#D9D9D9` | 基线系列 |
| grid | `#E9E9E5` | 坐标网格和细分隔线 |
| border | `#D9D9D4` | 面板细边 |

不要在 `#F36B2B` 条形上用白色小字；用 ink 保持对比度。若需额外状态色，先明确它表达的业务含义，并遵守同一套对比度门槛。

## Riptide Cobalt

cream `#FDF0E0` · cobalt `#375DFE` · ink `#1A2240` · paper `#FFFFFF`。可采用克制的双色关系。中性对比保持两边等权；来源明确给出结论时，才用强调色突出相应结果。

## Avocado Press

white `#FFFFFF` · blue `#0055A4` · lime `#DCF4A2`。可用白页双色；蓝色文字配白底或浅 lime，lime 不适合直接作白底小字。

## Pin & Paper

white `#FFFFFF` · cobalt `#2A3C99` · yellow `#F1E84E`。白卡片用蓝边、留白或浅底区分层级；黄底小字用深蓝。

## Grove

parchment `#E8E4D6` · forest `#192B1B` · terracotta `#B0443E`。温暖克制，可用于正式评审或反思型文章。浅字 `#F4F1E6` 对 terracotta 约 4.96:1；其它浅字组合另算。

## 组合、改编与新配色

每个家族提供气质与可用搭配，不绑定构图原型。可以调整强调色、引入协调的角色色，或从文章重新设计；改编后在工作契约记录 `palette_source: adapted` / `custom`，逐项检查实际文字 / 背景配对。

角色分区的可运行例子见 [semantic-columns.md](semantic-columns.md)；这套方法也可用于泳道、分层和其它多角色说明。颜色与状态、数据系列共存时，区分其视觉通道，不用同一色在同图表达互相冲突的含义。
