# 介质硬约束（社区经验 + 实测）

DSL 字段和官方 parser 清单以 `lark-whiteboard` 的 `elements/`、`routes/svg.md` 为准。本页只保留精排时容易踩错、且已用 `whiteboard-cli@0.2.13` 对过的映射。本地 `--check` 能抓溢出和重叠，不能证明飞书客户端体验。官方文档与真实转换冲突时，以 `tests/fixtures/parser-contract.svg` 的固定版本回归为当前证据，并把差异记在这里。

## SVG：可识别 vs 降级

画板把能识别的元素变成可编辑节点，其余变成 `type: svg` 嵌入图（能看见，不能当普通形状改）。

| 源元素 | 转换结果（实测） | 用法 |
|---|---|---|
| `rect`（`rx` 中等） | `composite_shape` / `round_rect` | 层容器、卡片、页脚条 |
| `rect`（`rx` 很大，胶囊） | `round_rect2` | 流程步骤 |
| `circle` / `ellipse` | `ellipse` | 编号签、起止点 |
| `line` / 正交 `polyline` + `marker-end` | `connector`，`right_angled_polyline` 或 `straight`，箭头字段非 `none`，具体样式取决于 marker | 默认连线 |
| `stroke-dasharray` 的 polyline | `border_style: dash` | 回填、反馈 |
| 三次 `path` 曲线 + `marker-end` | `connector` / `shape: curve` | 标 `data-role="edge"`；少量跨层曲线可以 |
| `polygon` 菱形 | **`type: svg` 嵌入图** | 需要原生判断节点时用 DSL `diamond`；允许局部降级时单独披露 |
| 装饰 `path` 图标 | `type: svg` 嵌入图 | 不要当结构件 |
| `opacity="0.4"` | OpenAPI 里 `fill_opacity: 40`；飞书端常按不透明绘制 | 浅色请用实心更浅 hex |
| 两 stop `linearGradient`（默认 objectBoundingBox） | OpenAPI 保留 `fill_gradient` 和两个 stop | 当前可用，但技术文档精排仍优先纯色；复杂参数按官方边界 |
| `feDropShadow` | 本地仍是普通 `round_rect` | 需要阴影时用同形状实心偏移副本 |
| `clipPath` / `mask` / `pattern` / `foreignObject` | 渲染异常或整段丢失 | 禁止 |
| `font-family` | 画板硬编码 Noto Sans SC，声明被忽略 | 禁止 |

文字必须是 `<text>`，不能 outline 成 path。中文文件必须是 UTF-8；用错误编码保存后，`--to openapi` 会把汉字写烂，PNG 出现豆腐。

## SVG 构图规则

- 逻辑画布约 1400–1600 宽，高度随内容；不要假 16:9。
- 容器宽度按 CJK ≈ 1em、Latin ≈ 0.6em 预留，宁可过宽。
- 箭头：`<defs>` 里一个 `marker`，线或折线写 `marker-end="url(#arrow)"`。禁止在线头再画三角形。
- 有向边写 `data-role="edge"`；无向关系线（含辐射）、坐标轴、分隔线分别取 `data-role="spoke"`、`data-role="axis"`、`data-role="divider"`。来源只给出连接关系、未给调用方向时，可用 `spoke`，不补造箭头。lint 据此区分漏箭头与合法无向线，并核对 marker ID 是否存在。
- 文字放在非白色块上时写 `data-bg="#实际背景色"`。lint 对普通文字要求至少 4.5:1；≥24px 或 ≥19px/700 的大字允许 3:1。背景发生变化时同步改 `data-bg`。
- parser 可识别部分 `translate` / `rotate` / `scale`，但当前 `fit_check.py` 不测量任何 transform，也不测量相对 path。默认展开成显式坐标与绝对 path；出现 `unmeasured-*` 不能当作检查通过。避免 `skewX` / `skewY` / `matrix(...)`。
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

## Parser contract 回归

本 skill 的可复现基线为 `@larksuite/whiteboard-cli@0.2.13`。`tests/test_parser_contract.py` 验证 polygon、曲线 connector 和双 stop gradient 的实际类型。评估新版本时先运行原有 fixture 并查看实际差异，再决定是否更新期望和说明；不要先把期望改到“通过”，也不要只改版本号。

## 渲染前 fit-check

社区实践把可预测的几何缺陷放在渲染前处理。本 skill 提供轻量的
`python3 scripts/fit_check.py diagram.svg --json`：它检查 UTF-8 / `viewBox`、rect / circle / line / polygon / path / text
内容是否出血、外边距是否明显不足，以及右侧 / 底部是否存在大块 dead space。对无法安全估算的相对 path 或 transform，
它会 **fail closed**，不会把“未测量”报告成通过。它不能代替 PNG 目视，也不能判断事实是否正确；`lint_svg.py`、
`whiteboard-cli --check` 和真实飞书体验仍各自负责自己的证据层。

默认目标是约 80px 外边距和 80px 以上才报告的大块空白，可用 `--margin` / `--deadband` 配合设计契约调整。固定 fixture 可以记录有意 warning，但新增 warning 必须解释。

DSL 分层图默认「层标签在外 + 层内白色节点」。它画不出层间左右双侧的 API 标注，也很难做跨列页脚条——那些回到 SVG。

## Mermaid

用户提供或指定 Mermaid 时保留其格式；时序、思维导图、类图、饼图、甘特也适合该路线。按底座将源码转成画板，不为统一样式重排其语义。未指定格式的说明型流程图可按排版需要选择 SVG。复杂 subgraph / 超长中文应检查转换诊断，不能把某次通过推广到所有语法。

## 不要用手写 OpenAPI raw

`+update --input_format raw` 的 JSON 由 `whiteboard-cli --to openapi` 生成，不要直接编飞书节点字段。
