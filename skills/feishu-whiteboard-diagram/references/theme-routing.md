# 主题路由与色彩剂量

这页解决一个常见问题：画板有很多好看的色板，但技术文章不应该每次都被套成同一种海报风格。
主题由**阅读场景、图的语义和文章气质**共同决定；色板不是内容分类的贴纸，也不是给每个节点随机换颜色。

## 选择优先级

从上到下取第一个明确约束：

1. **品牌 / 用户明确指定**：指定颜色、参考图、已有画板的视觉身份优先。
2. **已有画板的视觉身份**：改版时默认保留，除非用户明确要求换肤。
3. **图的语义**：架构、流程、状态、评测、时间线等决定结构需要怎样的对比。
4. **文章主题**：技术、可靠性、研究、创意、治理等只决定气质和主强调色，不覆盖语义。
5. **默认主题**：没有足够信息时使用 `light-technical`，不要回退到 Riso Brut。

`diagram_purpose` 决定图怎么读；`article_tone` 决定图给人的气质；`theme` 是两者合并后的明确选择。
如果两者冲突，优先保证语义清楚：一张可靠性状态图可以有温暖气质，但失败 / 中断 / 成功仍要用可解释的状态色。

实际路由由 [scripts/theme_router.py](../scripts/theme_router.py) 固定实现；需要复核时运行：

```bash
python3 scripts/theme_router.py --purpose architecture --tone technical
# light-technical
```

相同的显式输入必须得到相同的主题。`user_theme`、`brand_theme` 和改版时的 `existing_theme` 依次覆盖语义路由；
没有显式主题时，先按 `diagram_purpose`，再按 `article_tone`，最后回退到 `light-technical`。

## 开工契约字段

在不进入画布的事实契约中补充：

```yaml
article_tone: technical | research | product | reliability | creative | governance | benchmark
diagram_purpose: architecture | process | state | comparison | timeline | quadrant | focus-detail | swimlane
formality: restrained | balanced | expressive
theme: light-technical | white-report | riso-brut | coral | grove | avocado-press | riptide-cobalt | pin-paper
theme_reason: 为什么这套主题服务于文章与图的阅读任务
accent_budget: neutral | one-accent | semantic-status
```

字段含义：

- `article_tone` 是文章或章节的整体气质，不等于“技术就必须蓝色”。
- `diagram_purpose` 是这张图要回答的问题，优先影响构图和颜色剂量。
- `formality` 借鉴社区色板目录的 restrained / balanced / bold 思路，在本 skill 中收窄为三档。
- `accent_budget` 防止“每个节点一种颜色”：普通架构图默认 `one-accent`，状态图才用 `semantic-status`。

## 路由表

| 图 / 文章信号 | 主题 | 颜色行为 | 禁止的默认动作 |
|---|---|---|---|
| 技术架构、服务边界、系统拓扑 | `light-technical` / architecture | 白页 + 浅蓝灰分组；蓝色只标当前边界、请求或焦点 | 整个运行时容器涂饱和绿 |
| Agent 流程、任务编排、工具回路 | `light-technical` / process | 浅蓝 + 浅紫上下文；判断或工具回路只保留一个焦点 | 每个 Agent 一种鲜艳颜色 |
| 恢复粒度、状态机、故障路径 | `light-technical` / reliability | 普通节点白底；进行 / 成功 / 中断 / 失败分别用浅蓝 / 浅绿 / 浅黄 / 浅红 | 用绿色表示一个系统边界 |
| 性能、质量、成本、模型基准 | `white-report` | 白底、橙色候选系列、浅灰基线和网格 | 用暖色直接暗示“更优” |
| 阶段、里程碑、变更时间线 | `coral` 或 `light-technical` | 只有高潮节点使用珊瑚色，其余安静 | 所有时间点都染成珊瑚色 |
| 正式评审、治理、可复用性决策 | `grove` | 羊皮纸 / 森林绿 / 陶土红，获胜象限才饱和 | 四象限四种主色平均铺开 |
| 一个主判断带支持点 | `avocado-press` 或 `light-technical` | 左侧大焦点，支持卡片保持白底 | 做成均等卡片墙 |
| 创意、品牌、概念型解释图 | `riso-brut`、`coral` 或用户指定主题 | 可使用奶油底、粗边和硬阴影，但必须服务于焦点 | 把编辑型视觉当成所有技术图默认 |

## `light-technical` 默认主题

这是技术文章和架构图的安全默认，不是“没有设计”：

| Token | Hex | 用法 |
|---|---|---|
| canvas | `#F8FAFC` | 整张画布，接近白页的冷静底色 |
| surface | `#FFFFFF` | 普通卡片和节点 |
| group | `#F1F5F9` | 分组容器，不能承担状态语义 |
| ink | `#1F2937` | 标题、正文、默认连线 |
| muted | `#475569` | 副标题、说明、非焦点标签 |
| border | `#CBD5E1` | 普通边框和分隔线 |
| accent | `#2563EB` | 当前焦点、请求链或主边界 |
| accent-soft | `#EFF6FF` | 主分组浅底 |
| context | `#7C3AED` / `#F5F3FF` | 只有流程需要区分上下文时使用 |
| success | `#16A34A` / `#ECFDF5` | 成功状态，不作容器默认色 |
| warning | `#D97706` / `#FFF7ED` | 中断 / 预警状态 |
| failure | `#DC2626` / `#FEF2F2` | 失败 / 熔断状态 |

颜色剂量按视觉面积控制，而不是按节点数量控制：大部分面积保持 `canvas` / `surface`，分组使用浅底，
饱和色只占焦点、边界或状态的一小部分。普通文字一律使用墨色；浅底上的状态色主要用于边框、标题或标记，
不要让中亮度的绿 / 橙 / 红承载小字号正文。

## 反向检查

在渲染前回答四个问题：

1. 去掉颜色后，位置、边界、编号和箭头仍然能说明关系吗？
2. 绿色、橙色、红色是否各自有明确的状态语义？如果没有，改回中性底色。
3. 第一眼落点是否由尺寸、留白和结构共同决定，而不是靠一块刺眼的颜色抢注意力？
4. 这套颜色是否能在白色文档背景、PNG 预览和飞书真实画板中保持可读？
