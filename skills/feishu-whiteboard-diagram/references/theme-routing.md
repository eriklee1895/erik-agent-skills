# 视觉选择：文章、关系与配色

目标是让 agent 为当前文章设计合适的图。主题和色值是可调整的设计资源；事实、可读性、语义一致性与可编辑性是交付要求。图的语法不绑定色板，技术文章也可以采用温暖或有表现力的配色。

## 选择方法

1. **用户 / 品牌要求优先。** 保留指定的颜色、参考图气质与识别元素；与对比度冲突时调整明度或文字配对，并说明原因。
2. **已有视觉身份保持连续。** 改版默认保留色板与阅读顺序；用户要求换肤时按新的视觉目标处理。
3. **综合文章主题与图的语义。** `article_tone` 决定温暖、克制、鲜明等气质；`diagram_purpose` 决定需要角色区分、状态、数据系列或等权比较。两者共同影响方案，不用“架构”标签覆盖文章气质。
4. **选择来源。** 从 [配色家族](palettes.md) 直接选用、调整已有家族，或独立设计。新配色不需要伪装成现有主题或等待额外批准。
5. **检查实际组合。** 配色进入构图后，核对文字 / 背景对比度、视觉重量、颜色含义、默认显示宽度和原生转换；按结果修正。

文章气质和关系不足以形成判断时，可从 `light-technical` 默认主题开始。它是兜底起点，不是所有技术图的强制主题。一个图中保持共同的文字、背景、边框和颜色角色体系；从不同家族取色时重新整合和检查，而非机械拼贴。

## 简短视觉契约

写在工作笔记里，不进入画布。字段取值是例子，开放填写；简单图可合并成几句话。

```yaml
article_tone: reflective-technical
diagram_purpose: architecture
formality: restrained
theme: custom-plum-stone
palette_source: custom # preset | adapted | custom
theme_reason: 温暖中性色适合反思型技术文章，紫色只辅助边界识别
accent_budget: one-accent # neutral | one-accent | semantic-zones | semantic-status | data-series | mixed
color_semantics: 石色表示共同背景，深紫表示边界；不表达优劣或状态
reading_hierarchy: 标题 -> 两个等权方案 -> 对应边界；无获胜项
supporting_region: none # conclusion | boundary | next-steps | source | none
```

`theme` 可以是预置名、改编名或 `custom-<描述>`。`accent_budget` 描述颜色承担的任务，不是颜色数量上限：

| 颜色角色 | 适用任务 | 检查重点 |
|---|---|---|
| `neutral` / `one-accent` | 克制说明、突出一个判断或边界 | 强调色是否把注意力放在读者任务上 |
| `semantic-zones` | 多角色、多职责或分区 | 同一角色同色；位置与标签仍可独立说明结构 |
| `semantic-status` | 恢复、风险、状态转换 | 状态标记和含义一致；用文字补充颜色 |
| `data-series` | 定量对比、多个数据系列 | 颜色标识系列，不自行暗示胜负；图例与标签一致 |
| `mixed` | 角色与状态 / 系列同时存在 | 分别用底色、边框、标记等通道，避免同色多义 |

这些策略可用于任何适合的构图。角色色不需要先满足某个四列模板；状态图也不必使用固定的红黄绿，但应保留可解释的标签与足够区分度。

## 候选方向，不是题材到色板的映射

| 文章 / 阅读任务 | 可考虑的方案 | 设计判断 |
|---|---|---|
| 克制的系统边界说明 | Light Technical、Grove 的浅色改编、自定义暖灰 | 冷暖由文章决定；分组不必逐层换色 |
| 多角色价值链 | 现有家族的协调角色色、自定义浅色组 | 用稳定的多色映射区分职责，参见 [semantic-columns.md](semantic-columns.md) |
| 中性方案对比 | Riptide / Pin & Paper 的中性改编、单色或自定义 | 等权展示；没有来源结论就不设置获胜格 |
| 定量报告 | White Report、品牌色报告、自定义数据系列 | 量纲、尺度、图例规则保持，橙 / 灰可替换 |
| 温暖叙事、时间线或概念说明 | Coral、Grove、Riso Brut、自定义 | 强调程度随叙事变化；不必放大某个时间点 |

## 可选建议脚本

[scripts/theme_router.py](../scripts/theme_router.py) 为缺少设计选择时提供一个可复现的建议，也可接收 agent 的选择：

```bash
python3 scripts/theme_router.py --purpose architecture --tone technical
# light-technical：只有启发式建议
python3 scripts/theme_router.py --purpose architecture --theme custom-plum-stone
# custom-plum-stone：保留 agent 的设计决定
```

优先级是 `--user-theme` → `--brand-theme` → `--existing-theme` → `--theme`；没有这些输入时才根据气质与用途给出建议，最后回退到 Light Technical。脚本不读取文章全文，不验证配色质量，也不决定是否允许交付。无需运行脚本来获得创作许可；选定方案与预设不同也可以继续同一套质量检查。
