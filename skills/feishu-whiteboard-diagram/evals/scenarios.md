# Behavioral scenarios

Evaluate whether an agent uses this skill to insert a native Feishu whiteboard into a document, not an HTML5 block, screenshot, or invented API. For a request that does not authorize a Feishu write, the correct result stops at local SVG/DSL + PNG and names the unrun evidence steps.

## 1. Layered architecture in a design-review doc

**Prompt.** “在这篇飞书设计评审文档里，用画板画出支付网关的四层：接入、协议、会话、后端适配。每层写清职责和边界，层间标上行/下行 API。先本地准备，先别写文档。”

**Pass.** Chooses a native whiteboard (SVG layered-strip grammar). Pastel fill + same-hue border, inner white cards, footer or thesis line. Runs lint + `whiteboard-cli --check` + PNG. Reports at most `local-render-valid`. Does not emit HTML5 XML.

**Fail.** Mermaid-only boxes with no 职责/边界 columns; HTML5 block; claiming Feishu verification from a local PNG.

## 2. Agent loop with tool feedback

**Prompt.** “给 Hermes 普通任务循环画一张飞书画板：用户任务 → 加载上下文 → LLM 判断；直接回答或执行工具后虚线回填。插入到授权章节。”

**Pass.** Quiet ink boxes, orange color-block for 判断, enlarged tool-loop band, short dashed backfill labeled 结果回填. Reads `lark-whiteboard` for the write path; does not invent CLI flags. Distinguishes write vs client evaluation.

**Fail.** All-blue Mermaid flowchart with no role colors; wrap-around dashed loop around the canvas; HTML5 animation as the only artifact.

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
