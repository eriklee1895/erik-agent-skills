# 事实契约与交付复核

新建、改版、只审查都先固定事实，再判断构图。契约写在工作笔记里，不要画到画板上。

## 开工契约

字段与取值为填写示例，颜色角色、气质与主题名称可按文章扩展；简单任务可合并为简短笔记。

```yaml
thesis: 一张图只回答的一句话
audience: 谁在什么文档宽度下阅读
article_tone: technical | research | product | reliability | creative | governance | benchmark
diagram_purpose: architecture | process | state | comparison | timeline | quadrant | focus-detail | swimlane
formality: restrained | balanced | expressive
source_facts:
  - 原文明确给出的实体、数字、状态和职责
relationships:
  - from: A
    to: B
    meaning: 请求 / 返回 / 包含 / 依赖
allowed_inferences: []
unknowns: []
grammar: layered-strip | task-loop | comparison | hub | timeline | swimlane | quadrant | focus-detail | semantic-columns | custom
focal: 阅读重心，可为单卡、复合区域、主线或等权比较
reading_hierarchy: 读者先看什么、怎样比较、如何理解关系
theme: 预置名、改编名或 custom-描述；不是允许列表
palette_source: preset | adapted | custom
theme_reason: 为什么这套主题服务于文章与图的阅读任务
accent_budget: neutral | one-accent | semantic-status | semantic-zones | data-series | mixed
color_semantics: 角色、状态、系列映射，以及背景、层级和文章气质的视觉用途
supporting_region: conclusion | boundary | next-steps | source | none
cuts: 为默认文档宽度主动删掉或拆到下一张图的内容
```

规则：

- 箭头、数字、角色、状态、所有者和因果关系都是事实声明。来源没有，就不补造。
- 不确定但必须呈现的内容标成「待确认」；不要用确定连线伪装。
- 默认不超过 12 个主信息块。超过时拆成「总览 + 细节」，而不是缩到 12px。
- 一张图保持清楚的主阅读任务。单卡、复合区域、主线或等权比较都可建立层级；辅助说明不应压过主任务。
- 品牌 / 用户明确指定优先，改版保留已有视觉身份；再综合图的语义与文章主题自主设计。`light-technical` 仅在缺少线索时提供起点。
- 可用预置、改编或自定义配色，均说明与文章和阅读任务的关系，使用相同的检查标准；无需因自定义配色额外申请许可。
- 颜色可表达语义、组织层级或呼应文章气质。去掉颜色后，事实关系仍应能靠位置、边界、文字、编号和箭头读懂。
- 颜色数量和面积服务于层级、角色、状态或数据系列。等权方案可以同大同重，结论强调必须有来源依据。
- 辅助区域可放结论、边界、后续步骤或来源，也可省略；步骤顺序有来源依据，内容不重复正文导语。

## 改版契约

先按 `lark-whiteboard` 导出源、raw 或预览，再列出改动轴：

| 轴 | 默认行为 |
|---|---|
| 事实与文案 | 保持 |
| 实体与关系 | 保持 |
| 几何与阅读顺序 | 保持，除非用户要求重构 |
| 色板与视觉身份 | 保持，除非用户要求换肤 |
| 密度 | 只删除用户同意删减或可安全折叠的内容 |

修复是局部修改；重构改变信息架构；换肤只改变视觉系统。不要把其中一个悄悄做成另一个。

## 交付门禁

先检查证据，再评视觉：

1. **事实**：逐条核对契约中的实体、文字、数字与关系；没有虚构箭头。
2. **层级**：标题、主体与必要细节可区分；视线路径清楚，等权比较没有被无依据地突出一方。
3. **平衡**：视觉重量没有全部堆在一角，留白是有意的。
4. **密度**：默认文档宽度下能读；没有靠缩小字号硬塞。
5. **色彩语义**：配色与文章气质、图的用途一致；角色、状态、数据系列按声明核对。装饰色可辅助层级与气质，不应制造事实、胜负或状态暗示。
6. **对比度**：`data-bg` 已标注的文字通过 lint；其余目视无弱对比。
7. **对齐与留白**：卡片边缘、文字起点和 connector 端点落在共同栅格，画布没有大块无意空白。

每项记 `pass / weak / fail`，只修最弱的一项并合并其它机械错误，一次重渲确认。无 `fail` 且最多一个 `weak` 才交付。只审查请求到此停止；用户没要求修，不写回飞书。

## 交付口径

- 本地 lint 和 PNG 只能到 `local-render-valid`。
- 写入并 fetch 到正确位置才是 `feishu-write-valid`。
- 人在指定 Web / 桌面表面打开、确认可读与可编辑，才是 `feishu-experience-valid`。
- 历史 fixture 的人工认可不自动覆盖新的 parser、色板或构图版本。
