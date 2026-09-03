# 介质边界

写飞书文档时，先问「读者要带走什么」，再选载体。载体选错，后面的配色和布局都会浪费。

## 对照

| 载体 | 读者得到什么 | 编辑性 | 布局控制 | 典型失败 |
|---|---|---|---|---|
| 飞书原生画板（本 skill） | 文档里的矢量图，可点进改 | 节点、文字、连线可改 | SVG 精确 / DSL 自动 / Mermaid 受限 | 用插画 path 换「设计感」，结果变成嵌入图 |
| Mermaid 画板 | 标准流程/时序，生成快 | 源码可再导入；复杂语法常 warning 2107 | 自动布局，难做编号签和页脚条 | subgraph、超长 label、中英混排溢出 |
| DSL 画板 | 分层、组织、dagre 流程 | 节点可改 | Flex / Dagre 强，重叠与跨层标注弱 | `fill-container` 死锁、connector 放进 children |
| HTML5 块 | 动画、Tab、D3、可编程布局 | 改的是 HTML，不是画板节点 | CSS/SVG/JS 上限最高 | 被当成「更漂亮的画板」；默认状态空白 |
| 图片 | 真实 UI、照片、不可重建的视觉证据 | 不可编辑 | 像素级 | 把架构图做成截图，丢失协作 |

## 和官方 lark-whiteboard 的分工

官方 skill 负责：认证、`+export` / `+update`、已有画板探测、Mermaid/PlantUML/SVG/raw 的命令形态、覆盖确认。

本 skill 负责：在**写文档**的情境下决定要不要画板、画哪种语法、怎样才算精美、SVG 默认路径如何通过 `--check`。

官方 SVG 路线强调「打破矩形牢笼」。那在插画/海报场景成立；在技术文档里，wiki 级精排图恰恰是**有层级的圆角卡片系统**。本 skill 以实测为准：可识别的 `rect` / `ellipse` / `line` / `polyline` + `marker-end` 才能保持可编辑。

## 和 feishu-html-diagram 的分工

| 问自己 | 若是 → |
|---|---|
| 需要运动才能看懂流向，或需要 Tab/筛选才能看完对比？ | HTML5 |
| 需要同事拖节点、改一句职责、把连线接到另一个盒子？ | 画板 |
| 两者都想要？ | 先交一张静态可编辑画板；交互说明另做 HTML5，不要混在一个块里 |

## 文档内怎么用

飞书 XML（`lark-cli docs +create/+update`，`--doc-format xml`）：

```xml
<whiteboard type="svg" path="@./diagram.svg"></whiteboard>
<whiteboard type="mermaid" path="@./diagram.mmd"></whiteboard>
<whiteboard type="plantuml" path="@./diagram.puml"></whiteboard>
<whiteboard type="blank"></whiteboard>
```

Markdown 导入模式也可识别内联 `<whiteboard>`。复杂 Mermaid 直传经常失败；精排图不要赌 Mermaid。

画板是块级内容。先写一句「这张图回答什么」，再放画板，避免图和正文脱节。
