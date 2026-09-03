---
name: feishu-whiteboard-diagram
description: Use when 需要在飞书文档中插入可二次编辑的精美画板图表（分层架构、任务循环、多列运行图、编号层级、学习闭环等）；指导 agent 用 SVG / DSL / Mermaid 写入原生 whiteboard，而不是截图或 HTML5。不适用于需要动画交互的 HTML Diagram，也不替代 lark-cli 认证。
metadata:
  author: liyuheng.erik
  requires:
    bins: ["npx"]
    skills: ["lark-doc", "lark-whiteboard", "lark-shared"]
---

# 飞书画板精美图表

把技术文档里的架构、流程、边界和恢复粒度，画成**飞书原生画板**：读者能在文档里直接看，同事能点进画板改节点、改字、改连线。最终产物是 whiteboard block，不是 PNG，也不是 HTML 小网页。

本 skill 解决的是「这类图画什么、用哪条介质、怎样才算精美、怎样写进文档」。CLI 认证、XML 标签细节、已有画板的探测与覆盖策略，委派给已安装的 `lark-doc` / `lark-whiteboard` / `lark-shared`。

## 它不是什么

- 不是官方 `lark-whiteboard` 的替代品，不复制其 scene 模板和身份分流表。
- 不是 `feishu-html-diagram`：不需要动画、Tab、D3 或可编程交互时，不要用 HTML5 块冒充画板。
- 不是 35 套装饰色板，也不是「禁止矩形」的插画风。文档精排图的骨架就是圆角卡片、色边分组、编号签和结论条；靠信息层级而不是装饰 path 取胜。

## 适用 / 不适用

| 适用 | 不适用 |
|---|---|
| 写飞书文档时插入架构、流程、闭环、多列运行图、编号层级 | 微信 / Notion / 博客配图 → 走对应发布 skill |
| 需要同事在飞书里继续改节点和连线 | 需要动画、交互、探索式数据 → `feishu-html-diagram` |
| 一张图回答一个论点（职责、流向、恢复什么） | 现场工作坊贴便签、自由涂鸦 → 空白画板 + 人工共创 |
| 用户给了飞书文档 URL，要求「配图 / 画到画板」 | 真实 UI、照片、截图证据 → `<img>` |

同一文档可以有多张画板。一个论点一张图；不要把全篇塞进一张大海报。

## 介质选择（命中即停）

| 条件 | 介质 | 写入 |
|---|---|---|
| 用户已给出 Mermaid/PlantUML，或图是思维导图 / 时序 / 类图 / 饼图 / 甘特 | 代码图 | `<whiteboard type="mermaid\|plantuml">` |
| 判断多、回路多、需要原生菱形，且卡片对齐要求一般 | DSL `layout: "dagre"` + `diamond` | 先 `whiteboard-cli` 渲染，再 `+update --input_format raw` 或插入空白画板后更新 |
| 分层条带、多列泳道、编号层级、页脚结论条、层间 API 标注、编辑式精排 | **UTF-8 SVG，只用可识别原生形状** | `<whiteboard type="svg" path="@./diagram.svg">` 或 `+update --input_format svg` |
| 需要运动、Tab、D3、可探索状态 | HTML5 | `feishu-html-diagram` |
| 真实界面或照片 | 图片 | `<img>` |

精美技术文档图**默认走 SVG**。Mermaid 能画通流程，但画不出 wiki 那种分组色边、编号签和结论条。DSL Flex 适合整齐分层，但很难做层间双侧箭头、重叠编号签和跨列页脚。官方 SVG 路线里「不要用矩形」会把图标 path 打成不可编辑的嵌入图；本 skill 明确用矩形卡片做骨架。

## 创作 Workflow

### 1. 先写论点，再选语法

每张图只回答一个问题，例如：「四层各自屏蔽什么？」「LLM 和运行时谁做决策？」「中断后客户端恢复哪一层？」把实体、关系、顺序、状态写成短列表，再对到 [布局语法](references/grammars.md) 中的一种：

1. 分层条带（职责 / 边界）
2. 任务循环（判断 + 回填）
3. 学习闭环（并行落盘）
4. 多列运行架构（请求向右 / 事件向左）
5. 编号层级（恢复粒度）

没有合适的语法时，用「标题 + 分区卡片 + 少量语义连线 + 页脚结论条」现编，不要硬套。

### 2. 按文档精排视觉系统上色

完整色板和字号见 [视觉系统](references/visual-system.md)。最低要求：

- 分组靠**浅底 + 同色深边框**识别，组内节点白色卡片、边框跟随分组。
- 颜色表示角色，不表示装饰：蓝=动作/传输，紫=上下文/会话，橙=判断，绿=产出/成功，红=失败，灰=结束。
- 默认连线灰 `#94A3B8`；只有「上行 / 下行 / 是 / 否 / 回填」这类语义路径才用彩色。
- 标题说明论点，页脚写一句结论。不要把 prompt、风格名、来源路径写上画布。

### 3. 写 SVG（精排默认路径）

画布逻辑宽度 1400–1600，高度随内容。文件必须是 **UTF-8**（中文被写坏时，本地 PNG 会出豆腐，OpenAPI 里的字也会乱码）。硬约束见 [介质约束](references/constraints.md)。最小骨架：

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 820">
  <defs>
    <marker id="arrow" markerWidth="12" markerHeight="12" refX="9" refY="4"
            orient="auto" markerUnits="strokeWidth">
      <path d="M0 0 L10 4 L0 8 z"/>
    </marker>
  </defs>
  <text x="40" y="48" font-size="24" font-weight="700" fill="#1F2329">图表标题：一句话论点</text>
  <text x="40" y="76" font-size="14" fill="#64748B">副标题：读者带着什么问题看这张图</text>
  <!-- 只用 rect / circle / ellipse / line / polyline / text；菱形可用 polygon，但会变成嵌入 SVG 节点 -->
  <rect x="40" y="120" width="1360" height="160" rx="16" fill="#EFF6FF" stroke="#2563EB" stroke-width="2"/>
  <line x1="200" y1="200" x2="320" y2="200" stroke="#94A3B8" stroke-width="2" marker-end="url(#arrow)"/>
</svg>
```

禁止设置 `font-family`。文字只用 `<text>` / `<tspan>`。箭头只用 `marker-end`，不要再画一个小三角。中文按 CJK ≈ 1em、拉丁 ≈ 0.6em 给足宽度。

把文件写成 UTF-8。若当前写入工具会弄坏 XML 里的中文，改用 Python `Path.write_text(..., encoding="utf-8")`。

### 4. 本地渲染审查

将脚本路径解析为相对于本 `SKILL.md` 的文件，然后：

```bash
python3 /resolved/skill-dir/scripts/lint_svg.py /absolute/path/to/diagram.svg
npx -y @larksuite/whiteboard-cli@^0.2.13 -i /absolute/path/to/diagram.svg -f svg --check
npx -y @larksuite/whiteboard-cli@^0.2.13 -i /absolute/path/to/diagram.svg -o /absolute/path/to/diagram.png -f svg
```

`--check` 的 error 必须修。`node-overlap` 对编号签压在层边框上可能是 warn，目视确认是故意重叠再保留。打开 PNG：文字截断、贴边、无意重叠、箭头没有箭头、中文豆腐，都要改源文件再渲，不要整张重写。最多两轮。

DSL / Mermaid 同样先 `--check` 再出 PNG。DSL 约束见 [介质约束](references/constraints.md#dsl)。

### 5. 写入飞书文档

认证和 `--as user` 遵循 `lark-shared`。推荐把图画进正在写的那篇文档，而不是另存一张孤岛：

```xml
<h2>本节标题</h2>
<p>先用一两句说明这张图回答什么，再插入画板。</p>
<whiteboard type="svg" path="@./diagram.svg"></whiteboard>
```

代码图用 `type="mermaid"` / `type="plantuml"`。已有空白画板则：

```bash
npx -y @larksuite/whiteboard-cli@^0.2.13 -i diagram.svg -f svg --to openapi --format json \
  | lark-cli whiteboard +update --whiteboard-token <token> --source - --input_format raw \
      --idempotent-token <时间戳-board-1> --overwrite --as user
```

中文 SVG 也可直接 `--input_format svg --source @./diagram.svg`，避免不必要的本地 OpenAPI 中转。覆盖非空画板前要确认。完整命令和证据分级见 [写入与验证](references/write-verify.md)。

### 6. 回读再交

写入成功不等于飞书里好看。`docs +fetch` 确认 block 在目标章节；`whiteboard +export --output-type preview` 看飞书端图。飞书预览常被垫成大方画布，**交付本地 `diagram.png` 给用户看构图**，用飞书导出只核颜色和节点是否可编辑。

只报告实际做过的证据层：`lint-valid` / `local-render-valid` / `feishu-write-valid` / `feishu-experience-valid`。没有登录飞书时，停在本地层并写出未做的步骤。

## 前置检查

```bash
bash /resolved/skill-dir/scripts/preflight.sh
```

缺 `lark-cli` 或未 `auth login` 时，仍可完成本地 SVG/DSL 与 PNG；不要假装已经写进飞书。

## 相关文件

- [`references/grammars.md`](references/grammars.md) — 五种文档精排布局语法
- [`references/visual-system.md`](references/visual-system.md) — 色板、字号、间距
- [`references/constraints.md`](references/constraints.md) — SVG / DSL 硬约束与实测映射
- [`references/write-verify.md`](references/write-verify.md) — 插入文档、更新画板、证据层
- [`references/medium.md`](references/medium.md) — 与 Mermaid / HTML5 / 图片的边界
- [`scripts/lint_svg.py`](scripts/lint_svg.py) — SVG 介质预检
- [`scripts/preflight.sh`](scripts/preflight.sh) — 运行时依赖
