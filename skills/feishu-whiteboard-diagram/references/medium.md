# 介质边界

先问「读者要带走什么」，再选载体。载体选错，配色和布局都会浪费。

**怎么创建画板、用哪种 `+update --input_format`、覆盖还是追加：** 读 `lark-whiteboard` 与 `lark-doc` 的画板工作流。本页只做分流判断。

## 对照

| 载体 | 读者得到什么 | 编辑性 | 布局控制 | 典型失败 |
|---|---|---|---|---|
| 飞书原生画板 | 文档里的矢量图，可点进改 | 节点、文字、连线可改 | SVG 精确 / DSL 自动 / Mermaid 受限 | 用插画 path 换「设计感」，变成嵌入图 |
| Mermaid 画板 | 标准流程/时序，生成快 | 飞书按源码生成节点；复杂语法常 warning 2107 | 自动布局，难做编号签和页脚条 | subgraph、超长 label；把时序重画成 SVG 架构 |
| DSL 画板 | 分层、组织、dagre 流程 | 节点可改 | Flex / Dagre 强，重叠与跨层标注弱 | `fill-container` 死锁、connector 放进 children |
| HTML5 块 | 动画、Tab、D3 | 改的是 HTML | CSS/JS 上限最高 | 被当成「更漂亮的画板」 |
| 图片 | 真实 UI、照片 | 不可编辑 | 像素级 | 把架构图做成截图 |

## 和官方 lark-whiteboard 的分工

| 问题 | 谁回答 |
|---|---|
| 如何 login、查 token、export、update、overwrite | `lark-whiteboard` + `lark-shared` |
| 文档 XML 里如何插入 `<whiteboard>` | `lark-doc` 画板工作流 |
| 写文档时要不要画板、和 HTML5/图片怎么选 | 本 skill |
| 精排图用 SVG 还是 DSL、官方「少用矩形」听不听 | 本 skill：文档精排听本 skill |
| scene 里的架构/鱼骨/飞轮骨架 | 官方 `scenes/`；与精排语法冲突时用本 skill 的 [grammars.md](grammars.md) |

## 和 feishu-html-diagram 的分工

需要运动或 Tab 才能看懂 → HTML5。需要同事改节点和连线 → 画板。两者都要就拆成两块，不要混。

## Mermaid：写源码，飞书转画板

时序 / 思维导图 / 类图 / 饼图 / 甘特，或用户已经给了 Mermaid：

```xml
<whiteboard type="mermaid">sequenceDiagram
    ...
</whiteboard>
```

飞书服务端把源码转成画板节点。本 skill **没有**第二套 Mermaid 渲染器，也不要把 `sequenceDiagram` 改画成分层条带。复杂 subgraph、超长中文可能 warning 2107，那时再降级，不要一上来用 SVG 重排。

## 从社区收进来的判断（不复制其 skill）

吸收的是 `beautiful-feishu-whiteboard` RULES 和 `feishu-whiteboard-pro` 的构图纪律，不是 35 套换肤模板、也不是他们的海报字号。

- 精排默认 SVG + 原生形状，不要靠装饰 path。
- 箭头用 `marker-end`，不要手画三角箭头。
- `opacity` 不可靠，浅色用实心更浅 hex。
- 焦点靠 **尺寸**，染色但一样大仍像草稿流程图。
- 反均等卡片、反绕场虚线、反空列壳。细节见 [composition.md](composition.md)。
- 本地 PNG 看构图；飞书导出常被垫成方画布，且文字颜色不一定准。
- 官方 DSL 适合自动分层和原生菱形；层间双侧 API、编号签、跨列页脚仍用 SVG。
