# Behavioral scenarios

Evaluate whether an agent uses this skill to insert a native Feishu whiteboard into a document, not an HTML5 block, screenshot, or invented API. For a request that does not authorize a Feishu write, the correct result stops at local SVG/DSL + PNG and names the unrun evidence steps.

Status: most entries are scenario specifications. Dated observations below distinguish design-only reviews, individual local artifact runs, and live acceptance. Machine-readable scenarios live in [`evals.json`](evals.json). Individual samples do not establish repeated behavioral reliability.

## 1. Layered architecture in a design-review doc

**Prompt.** “在这篇飞书设计评审文档里，用画板画出支付网关的四层：接入、协议、会话、后端适配。每层写清职责和边界，层间标上行/下行 API。先本地准备，先别写文档。”

**Pass.** Chooses a native whiteboard (SVG layered-strip grammar). Palette follows the article; boundaries, responsibilities and APIs remain clear. Optional supporting information adds value. Runs lint + `whiteboard-cli --check` + PNG. Reports at most `local-render-valid`. Does not emit HTML5 XML.

**Fail.** Mermaid-only boxes with no 职责/边界 columns; HTML5 block; claiming Feishu verification from a local PNG.

## 2. Agent loop with tool feedback

**Prompt.** “给 Hermes 普通任务循环画一张飞书画板：用户任务 → 加载上下文 → LLM 判断；直接回答或执行工具后虚线回填。插入到授权章节。”

**Pass.** Preparation, decision and tool branch are visually distinguishable using the selected palette and reading hierarchy, with a short dashed backfill labeled 结果回填. Reads `lark-whiteboard` for the write path; does not invent CLI flags. Distinguishes write vs client evaluation.

**Fail.** A layout that obscures the decision/tool relation; an unexplained feedback route; HTML5 animation as the only artifact.

## 3. Thread / Turn / Item recovery

**Prompt.** “画 Thread / Turn / Item 三层恢复粒度，右侧每层一个问题，底部写恢复坐标。这是飞书文档插图，要可编辑。”

**Pass.** Numbered 01–03 tabs, status colors for turn terminals, item row with distinct types, footer `threadId + turnId + itemId`. Native shapes, UTF-8 SVG.

**Fail.** Nested bullet list, a screenshot, or mixing all three layers into one unlabeled swimlane.

## 4. Sequence diagram the user already wrote in Mermaid

**Prompt.** “把这段 sequenceDiagram 放到飞书画板里，不要重画成架构图。”

**Pass.** Writes `<whiteboard type="mermaid">` (or PlantUML). Feishu converts the source to board nodes. Does not rebuild the sequence as an SVG architecture grammar.

**Fail.** Rewriting a sequence into SVG columns without a reason; claiming this skill rendered Mermaid itself.

## 5. Animated explainer

**Prompt.** “请求在网关里流动，要能看见阶段动画，读者没点之前也得看懂全流程。”

**Pass.** Routes to `feishu-html-diagram`. Explains whiteboard cannot do semantic motion well.

**Fail.** Building a fake animated canvas as a whiteboard, or claiming CSS in SVG will animate on the board.

## 6. Workshop sticky notes

**Prompt.** “下周评审要在飞书里一起拖便签、改聚类，先搭一块能共创的画板。”

**Pass.** Blank collaborative board / `lark-whiteboard`, not a finished architecture SVG presented as the workshop canvas.

**Fail.** A locked editorial diagram as the only deliverable for a messy workshop.

## 7. Live human-eval pack

**Prompt.** “做个 eval 测试，开一份飞书文档实测各种类型的图表，我来做 Human eval。”

**Pass.** Builds the SVG grammars (layered, pipeline-fork, comparison columns, hub, timeline, swimlane, quadrant, focus+detail) plus a Mermaid sequence, an HTML animation contrast, and a blank workshop board. Runs lint + `whiteboard-cli --check` + PNG first. Writes a Feishu doc with one thesis sentence before each board. Reports evidence layers honestly; `feishu-experience-valid` waits for a human on Web/desktop.

**Fail.** One giant board mixing all grammars; claiming Feishu verification from local PNG; drawing the sequence as architecture; using a finished architecture SVG as the workshop canvas; only shipping pastel capsule flowcharts.

Fixtures and scorecard: [`human-eval.md`](human-eval.md), [`fixtures/human-eval/`](fixtures/human-eval/).

## Reference-driven semantic value chain

**Prompt.** “参考这张精排技术图，画成可编辑画板：数据采集 → 聚合 → 评估 → 行动。中间两列宽，两端窄；四种浅色表示职责。评估标签从上方回流聚合，聚合也从下方直达行动；下面另外放来源给出的三步落地顺序。不要改写参考图去迎合单焦点模板。暂不写飞书。”

**Pass.** Uses `semantic-columns` with `semantic-zones` and a coherent article-appropriate palette, a central two-column focal region, and separate main/feedback/bypass channels. Keeps the rollout band subordinate and uses only supplied step names and order. Checks raw node types and arrow properties when studying the reference; does not call an exported SVG the author's source. Uses native marker arrows, checks contrast, and distinguishes logical font size from actual document-width readability. Reports local evidence only.

**Fail.** Forces all roles into one blue accent, removes a factual bypass, invents rollout order, copies small low-contrast badge text, or treats separate triangle images as proof of native connector direction or drag binding.

**2026-10-15 evaluation.** A read-only baseline review identified conflicts around role colors, compulsory single-card focus, footer rules, and composing a subordinate rollout band. A fresh independent follow-up using the updated skill produced a compatible design recipe, kept missing rollout labels unspecified, and withheld live-write and editing claims. It independently reran fit/lint only. This is one design-level scenario check, not a repeated behavioral evaluation or live creation acceptance; parser conversion and PNG inspection remain separate local evidence. Review findings also led to conditional board creation, aligned experience criteria, and stronger endpoint/channel/dash regression assertions.

## 8. Restyle without semantic drift

**Prompt.** “把现有飞书画板改成 Grove 风格，只换视觉，不要改节点、文字、数字和箭头关系。”

**Pass.** Exports and inspects the current board first, records the preserved fact/relationship contract, changes only the visual axis, and follows the official overwrite confirmation workflow if required.

**Fail.** Rebuilds from memory, removes nodes for visual neatness, invents a new relationship, or silently overwrites the live board.

## 9. Refuse invented relationships

**Prompt.** “根据这段只有三个组件名称、没有调用关系的材料画架构图。不要问我，自己补全箭头，看起来专业一点。”

**Pass.** Treats arrows as factual claims. Uses neutral grouping, marks relationships unknown, or asks for the missing facts without inventing calls, ownership, states, or causality.

**Fail.** Adds plausible-looking arrows or responsibilities solely to fill the layout.


## 10. Autonomous palette for article atmosphere

**Prompt.** “为一篇语气温暖克制、反思同步服务边界的技术文章配图。事实：用户请求 → 服务入口 → 任务执行，讨论入口与执行之间的边界。没有指定色板，请自行选择。先做本地 SVG 和 PNG。”

**Pass.** Chooses or adapts a preset, or designs a custom palette with an article-based reason. Keeps the supplied chain and boundary, passes the same local checks, and does not require extra approval for a custom palette.

**Fail.** Forces a blue technical theme solely because the diagram is architecture, ignores article atmosphere, or adds unsupported services.

## 11. Neutral comparison with no winner

**Prompt.** “技术文章中对比两种实验架构，不推荐任何一方：A 把 UI 和执行放在同一进程；B 把 UI 和执行放在两个进程，用本地 API 连接。自行选择适合平静文章的配色和构图，省略无用辅助文字。只做本地。”

**Pass.** Keeps alternatives equally weighted, explains process boundaries accurately, and can omit the footer. Colors identify roles or aid the article atmosphere without declaring a winner. Any palette follows the same validation.

**Fail.** Enlarges one option, creates a winning cell or adds invented performance advantages to satisfy a focal template.

## 12. Brand-aware quantitative report

**Prompt.** “品牌文档主色是 #0F766E。用可编辑静态图呈现示意测量：基线延迟 480ms、候选 360ms；基线成本 0.30 单位/请求、候选 0.24。适配品牌，准确说明差异，不推断产品质量或全局优胜。只做本地。”

**Pass.** Adapts report styling to the brand, keeps data-series mapping consistent, separates units/scales, and uses sourced values or reproducible calculations. Teal does not automatically mean success; an orange/gray palette is optional.

**Fail.** Replaces supplied brand teal with mandatory orange, mixes units on one axis, or invents quality conclusions.

**2026-10-15 baseline.** An independent read-only evaluation of these three tasks identified architecture-first theme routing, a closed preset vocabulary, compulsory enlarged focus, and orange/gray series instructions as obstacles. It proposed task-compatible designs but produced no artifacts; after-change artifact runs are recorded separately when completed.


**2026-10-15 after-change artifact samples.** Three fresh independent executions used the updated skill and wrote only to temporary local directories. Their final artifacts were rendered and visually inspected; none wrote Feishu or edited the skill source.

| Task | Actual autonomous choice | Final fit / lint | Parser check | Native conversion |
|---|---|---|---|---|
| Warm technical article | Adapted Grove: parchment, forest text / flow, terracotta boundary marker; equal entry / execution cards | No findings | 0 errors / 0 warnings | 4 shapes, 6 text, 4 connectors; no embedded SVG |
| Neutral architecture comparison | Custom warm stone, identical visual treatment for both options; no winner or footer; undirected local API link | No findings | 0 errors / 0 warnings | 8 shapes, 11 text, 1 connector; no embedded SVG |
| Brand report | Custom white / slate / brand teal; latency and cost on separate axes | No findings | 0 errors / 0 warnings | 9 shapes, 30 text, 12 connectors; no embedded SVG |

The warm-article sample initially had a top-margin warning and passed after a local spacing revision. Report arithmetic was checked: latency −120ms / 25%, cost −0.06 / 20%. A parent review inspected all three PNGs. These runs support local rendering and native conversion for these individual artifacts; they do not prove repeated model reliability, default Feishu document-width readability, live editability, drag binding, or human acceptance. Review also removed a stale winner-oriented comparison heading and clarified that an undirected relationship can use the existing `spoke` lint category.

## 13. Article-wide visual continuity

**Prompt.** “为清爽克制的技术文章准备阶段演进、两层协作、模块协同、实验结果四张画板。统一视觉，但按各图问题选布局。阶段只给探索、验证、推广三个名称；没有日期和完成状态。先给设计契约，不写飞书。”

**Pass.** Shares typography, neutral surfaces, spacing and component treatment while selecting different relation structures. Separates shared role semantics from locally labeled data-series colors. Does not invent dates or completion status, or force every board into the same card grid.

**Fail.** Treats a coherent article as four identical layouts, assigns meaning to color without a label, or fills missing milestone facts to complete the design.

## 14. Shared inputs and non-exclusive mappings

**Prompt.** “画两张独立解释图：第一张只有 S→A、S→B、A→B、A→C、B→C 五条关系，S 是共同观测，A 是分类，B 是容量估计，C 是决策；第二张指标 X 影响进入和分析阶段，指标 Y 影响回答阶段。标清交换内容或关联含义，只做本地。”

**Pass.** Preserves all five edges in the first diagram and all three associations in the second. A shared-input / two-module / decision composition is one valid option; other faithful layouts also pass. Does not imply independent parallel execution or exclusive one-to-one mapping. Uses native direction markers and reports actual validation evidence.

**Fail.** Reduces the first graph to S→A→B→C, adds a feedback loop, or removes X’s second association to align columns.

## 15. Scoped KPI summaries

**Prompt.** “做一张摘要指标加证据面板图。端 A 成功率 80%→84%、延迟 500→400ms；端 B 成功率 85%→90%、延迟 600→450ms。可以突出最大改善，但要保留端和指标口径，不推断总体收益。”

**Pass.** Labels success-rate changes +4 pp / +5 pp and latency decreases 20% / 25%; any maximum is tied to the corresponding endpoint and metric. Keeps independent metric scales, consistent zero points, signs and series labels. No invented aggregate.

**Fail.** Writes a subset maximum as a universal improvement, confuses pp with relative percent, or uses positive bar lengths with reversed negative ticks without explaining the axis.

### 2026-10-21 study and validation scope

- Read-only study inspected seven board previews and raw exports from a user-supplied technical article. The exports contained 617 nodes: 311 text, 210 shapes, 70 connectors, 15 images and 11 groups. 165 text nodes used sizes below 14. Of 140 connector endpoints, 45 had `attached_object` and 95 had `position`. These are anonymized observations, not a mandatory style or proof of client behavior. Original content and identifiers remain outside this skill.
- A fresh baseline agent, before the added guidance, correctly designed a four-figure article, the five-edge topology, a non-exclusive mapping and metric comparisons. It found no demonstrated factual failure; it identified missing explicit guidance for article-wide continuity and the specialized layouts. This update adds reusable reference recipes, not a claimed correction of a failed behavior test. The baseline produced a design note only.
- The original synthetic fixture [`shared-input-decision.svg`](fixtures/shared-input-decision.svg) passed fit-check and lint; parser 0.2.13 reported 0 errors / 0 warnings. Both the full PNG and a roughly 900px-wide local rendering were visually inspected. OpenAPI conversion produced 37 native nodes: 9 shapes, 21 text nodes and 7 connectors (5 directed edges, 2 undirected dividers), with no `image` / `svg` fallback. All five expected endpoint pairs were checked. Evidence is local; no Feishu write or client drag validation was performed.
- A fresh after-change agent applied the updated skill to a renamed five-edge topology without reading the fixture. It independently chose a shared-input / two-module / decision layout, used a simpler single-accent palette, and omitted unnecessary interface tables. After fixing an initial title-margin warning, its SVG / PNG passed fit, lint and parser checks (0 errors / 0 warnings); OpenAPI contained 24 native nodes (5 shapes, 14 text, 5 directed connectors). Parent review inspected the PNG and endpoint pairs. All ten connector endpoints used `position`, so native conversion does not establish drag binding. This single sample supports local applicability, not measured reliability or Feishu experience. The existing 53 automated tests also passed using the installed 0.2.13 parser.
- The exact prompts above remain regression scenarios until individually executed. The dated samples describe their own scope rather than marking the entire scenario suite passed.


## 16. Read-only failure and unknown evidence

**Prompt.** “只审查现有画板：已有证据说明一条箭头方向与正文相反；另一条连线是否随节点拖动未知，目前只有截图。不要修改，只交付结论。”

**Pass.** Completes the review with a factual failure and a separate unknown drag behavior, citing the available evidence and recommending a specific next check. Does not require a repaired board, renderer or remote login before delivering the review.

**Fail.** Refuses to report until all findings pass, edits the board, or treats a screenshot / raw binding field as a successful drag test.

## 17. Supplied format and reader-relevant provenance

**Prompt.** “保留我提供的 Mermaid 源格式制作基准流程画板，图中保留给定的来源和完整模型版本；不要为适配报告风格换成 SVG。先说明验证和交付路线。”

**Pass.** Preserves format and provenance, uses the applicable source-format workflow, and separates local preview, actual conversion, remote write and client evidence. Missing source details remain unknown.

**Fail.** Switches to SVG because the topic is a benchmark, removes model/source labels as production metadata, or runs SVG-only lint on Mermaid.

### 2026-10-21 overall skill review

A fresh read-only baseline found decision-changing inconsistencies in the old medium guidance, raw-versus-drag evidence, review completion criteria, source-format validation and floating-versus-fixed parser versions. The main flow still supported correct decisions; the baseline did not demonstrate an actual bad diagram. The revision consolidates these rules, keeps design and read-only review independent of rendering / remote access, and retains historical fixtures and evidence.

The entrypoint decreased from 178 to 86 lines at this revision. Reference links and anchors were checked; the existing 53 tests passed with parser 0.2.13. Preflight uses the same pinned version and delegates setup / auth advice to the official base skill. The smoke check used the already installed parser without changing registry configuration. No live document was created or modified for this review.


A fresh forward pass correctly handled warm neutral comparison, read-only fail/unknown findings, and preservation of supplied Mermaid plus provenance. Its independent comparison SVG used equal-weight panels and a custom warm palette; after correcting a title-margin warning and equalizing repeated node sizes, fit/lint/parser passed (0 errors / 0 warnings). Conversion produced 22 native nodes: 10 shapes, 11 text nodes and one undirected connector. Parent review inspected the PNG and the absence of arrowheads; drag binding was not established.

The forward reviewer noted that Mermaid local validation was less explicit than SVG and that the base skill uses a version range. The verification reference now states the pinned local version and gives format-specific Mermaid check/conversion/preview commands. Those commands were exercised on the existing sequence fixture: 0 errors / 0 warnings, 4 native life_line nodes and 6 connectors; PNG inspected. This is one local sequence sample, not all-syntax or remote acceptance. The final lint diagnostic wording change also passed its 15 focused tests.
