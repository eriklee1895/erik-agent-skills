# 介质硬约束（社区经验 + 实测）

DSL 字段和官方 parser 清单以 `lark-whiteboard` 的 `elements/`、`routes/svg.md` 为准。本页只保留精排时容易踩错、且已用 `whiteboard-cli@0.2.13` 对过的映射。本地 `--check` 能抓溢出和重叠，不能证明飞书客户端体验。

## SVG：可识别 vs 降级

画板把能识别的元素变成可编辑节点，其余变成 `type: svg` 嵌入图（能看见，不能当普通形状改）。

| 源元素 | 转换结果（实测） | 用法 |
|---|---|---|
| `rect`（`rx` 中等） | `composite_shape` / `round_rect` | 层容器、卡片、页脚条 |
| `rect`（`rx` 很大，胶囊） | `round_rect2` | 流程步骤 |
| `circle` / `ellipse` | `ellipse` | 编号签、起止点 |
| `line` / 正交 `polyline` + `marker-end` | `connector`，`right_angled_polyline` 或 `straight`，箭头 `empty_triangle_arrow` | 默认连线 |
| `stroke-dasharray` 的 polyline | `border_style: dash` | 回填、反馈 |
| 三次 `path` 曲线 + `marker-end` | `connector` / `shape: curve` | 少量跨层曲线可以 |
| `polygon` 菱形 | **`type: svg` 嵌入图** | 1–2 个判断节点可接受；多菱形改走 DSL `diamond` |
| 装饰 `path` 图标 | `type: svg` 嵌入图 | 不要当结构件 |
| `opacity="0.4"` | OpenAPI 里 `fill_opacity: 40`；飞书端常按不透明绘制 | 浅色请用实心更浅 hex |
| `linearGradient` | 变成第一个 stop 的实心色 | 不要依赖渐变表达分组 |
| `feDropShadow` | 本地仍是普通 `round_rect` | 需要阴影时用同形状实心偏移副本 |
| `clipPath` / `mask` / `pattern` / `foreignObject` | 渲染异常或整段丢失 | 禁止 |
| `font-family` | 画板硬编码 Noto Sans SC，声明被忽略 | 禁止 |

文字必须是 `<text>`，不能 outline 成 path。中文文件必须是 UTF-8；用错误编码保存后，`--to openapi` 会把汉字写烂，PNG 出现豆腐。

## SVG 构图规则

- 逻辑画布约 1400–1600 宽，高度随内容；不要假 16:9。
- 容器宽度按 CJK ≈ 1em、Latin ≈ 0.6em 预留，宁可过宽。
- 箭头：`<defs>` 里一个 `marker`，线或折线写 `marker-end="url(#arrow)"`。禁止在线头再画三角形。
- 变换只用 `translate` / `rotate` / `scale`；避免 `skewX` / `skewY` / `matrix(...)`。
- 编号签压住层边框是有意重叠，`--check` 可能 warn；无意的卡片互压必须改。
- 不要把用户的任务说明、风格名、文件路径写进画布。

## DSL

适合整齐分层、组织树、以及需要**原生菱形**的分支流程。

硬规则：

1. 含文字节点 `height` 用 `'fit-content'`。
2. `fill-container` 的祖先链必须有固定宽度，否则尺寸变成 0。
3. `layout: "none"` 的容器必须有固定宽高。
4. `connector` 只能放在根 `nodes`，不能放进 `children`。
5. Flex 子节点的 `x/y` 会被忽略。
6. `gap` / `padding` / `layout` 必须显式写。
7. 同排等高卡片：`alignItems: "stretch"`（默认是 `start`）。
8. 虚 frame（无填充无边框）可能被优化掉，不要把 connector 接到它的 id。
9. Dagre 的 `edges` 写在最外层；`isCluster: true` 才允许连线穿透子图。
10. `cylinder` 用固定宽度 120–200，不要 `fill-container`。

DSL 分层图默认「层标签在外 + 层内白色节点」。它画不出层间左右双侧的 API 标注，也很难做跨列页脚条——那些回到 SVG。

## Mermaid

只用于时序、思维导图、类图、饼图、甘特，或用户已经给了源码。流程图即使能画，也缺少文档精排的分组色和结论条。复杂 subgraph / 超长中文在飞书直传时经常 warning 2107。

## 不要用手写 OpenAPI raw

`+update --input_format raw` 的 JSON 由 `whiteboard-cli --to openapi` 生成，不要直接编飞书节点字段。
