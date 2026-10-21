# Human eval · 飞书画板精美图表

用这份清单评 `feishu-whiteboard-diagram` 的**文档精排画板**，不是评官方 `lark-whiteboard` CLI 教程。本地 PNG 只能证明构图；飞书里能不能点开改节点，必须人在 Web / 桌面上看。

## 候选与证据索引

2026-09-04 的原始 fixture 验证保留在 [`current-local-evidence.md`](fixtures/human-eval/current-local-evidence.md)。后续主题、构图与独立应用样本的日期和范围见 [scenarios.md](scenarios.md)；各样本分别记录最高证据，不汇总成整个 skill 已获飞书体验认可。`15-light-architecture.svg` 与新样例的客户端体验需各自验收。

在 Web / 桌面重新打开并逐图填写记分表之前，**不得沿用旧版的 `feishu-experience-valid`**。

## 历史定稿（2026-09-03）

| 项 | 记录 |
|---|---|
| 结论 | **Qualitative Accept**。评测人确认当时的飞书效果可以定稿；没有填写逐图分数。 |
| 评测人 / 日期 | 李玉恒 · 2026-09-03 |
| 最高证据层 | 当时有人在飞书打开并确认，但在线记分表为空；不视为逐图可审计证据。 |
| 评测文档 | https://bytedance.my.larkoffice.com/docx/MoiudXbwaonw61xo2Uem0E9qyQg |
| 历史视觉基准 | 旧版 fixtures：奶油底 + 4px 墨边 + 一个更大的饱和焦点；分层条带才用浅色分组。它不覆盖新的 Light Technical 默认主题。 |

这份历史结论只覆盖当时的色板与 fixtures。后续改构图、parser 或默认色板，先跑本地验证，再建新的评测文档；不要覆盖历史文档伪装成同一轮结果。

配套产物：[`fixtures/human-eval/`](fixtures/human-eval/)（入库的是 SVG / Mermaid / HTML；PNG 预览本地生成，不提交）。再生：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 skills/feishu-whiteboard-diagram/evals/generate_human_eval_fixtures.py
python3 skills/feishu-whiteboard-diagram/scripts/lint_svg.py skills/feishu-whiteboard-diagram/evals/fixtures/human-eval/01-layered-strip.svg
npx -y @larksuite/whiteboard-cli@0.2.13 -i skills/feishu-whiteboard-diagram/evals/fixtures/human-eval/01-layered-strip.svg -f svg --check
# 可选：本地 PNG 预览（gitignored）
npx -y @larksuite/whiteboard-cli@0.2.13 -i skills/feishu-whiteboard-diagram/evals/fixtures/human-eval/01-layered-strip.svg -o /tmp/feishu-whiteboard-diagram-01.png -f svg
```

写入飞书时，登录后在仓库根目录先执行不带确认参数的命令：

```bash
bash skills/feishu-whiteboard-diagram/evals/create_human_eval_doc.sh
```

脚本会解析 `eval-doc.xml` 并尝试以用户身份创建文档。遇到 exit 10 时，把返回的 action、risk 和关键参数展示给用户；只有用户针对本次创建明确同意后，才重跑：

```bash
bash skills/feishu-whiteboard-diagram/evals/create_human_eval_doc.sh --yes
```

脚本不自动追加 `--yes`，也不因普通失败改目标目录重试。

## 先记证据，再打分

按 [写入与验证](../references/write-verify.md#证据与交付口径) 区分 lint、本地渲染、原生转换、飞书写入、客户端体验与拖动实测。逐图填写实际表面、文档宽度与未测项；仅导出 preview 或打开页面不等于已确认可编辑。拖动跟随另行测试，不由原生节点类型推断。

## 维度（1–5）

白板图默认是静态的：`Semantic motion` 和 `Interaction` 对 SVG/Mermaid 记 **N/A（有意静态）**，只给 HTML 对照块打这两项。有一项低于 3，或出现阻断项，整张图不通过。

| 维度 | 1 | 3 | 5 |
|---|---|---|---|
| 理解速度 | 看不出这张图在回答什么 | 能看出主论点和关系，但要停一下 | 扫一眼就知道分层 / 循环 / 恢复粒度 |
| 专业观感 | 阅读路径不明、无意义绕线、列壳大半是空 | 能放进技术文档，有小毛边 | 层级符合任务；配色协调；单卡、区域、主线或等权比较均清楚；辅助区域有用或合理省略 |
| 语法是否对 | 用错骨架（时序画成架构，闭环没有「否」） | 骨架对，个别标注弱 | 与来源关系一致，主阅读任务清楚；[grammars.md](../references/grammars.md) 提供可选骨架 |
| 可编辑性 | 飞书里是图片 / HTML / 整块嵌入 SVG | 主结构是原生节点，个别菱形嵌入可接受 | 卡片、条带、连线能点开改；装饰 path 没有当骨架 |
| 默认宽度可读 | 文档默认宽度下核心被裁或要放大 | 核心可读，边角略挤 | 默认文档宽度下标题、卡片、页脚都清楚 |
| 和正文的咬合 | 图和前后文字脱节或互相矛盾 | 有一句「这张图回答什么」 | 图推进该节论点，配色气质与文章一致；结论、步骤、来源等辅助信息按需呈现 |

### 阻断项

- 核心文字截断、无意重叠、中文豆腐。
- 把 HTML 动画或截图当成「画板已验证」。
- 工作坊场景只给一张锁死的精排图、没有空白共创板。
- 用户给了 sequenceDiagram，却被重画成架构分层。
- 反馈方向、线型含义或状态流转与来源契约冲突。

## 历史 fixture 图清单

以下描述这些固定样例的设计意图，不是所有新图都要遵守的焦点、颜色或布局规则。

| ID | 文件 | 介质 | 你要确认的事 |
|---|---|---|---|
| 01 | `01-layered-strip.svg` | SVG 画板 | 四层等宽，职责/边界成列，上下行 API 分色 |
| 02 | `02-task-loop.svg` | SVG 流水线+分叉 | 工具回路放大；短虚线回填，不绕场 |
| 03 | `03-learning-loop.svg` | SVG 门禁+三列 | 三列写满对比项；下一轮是标签 |
| 04 | `04-multicolumn-runtime.svg` | SVG 多列 | 运行时最大；请求向右、事件向左 |
| 05 | `05-recovery-layers.svg` | SVG 编号层级 | 右侧每层一个问题 |
| 06 | `06-sequence.mmd` | Mermaid 直传 | 飞书自动转画板 |
| 07 | `07-packet-flow.html` | html5-block | 不是画板 |
| 08 | blank | 空白共创 | 能拖便签 |
| 09 | `09-comparison.svg` | SVG 对比列 | 钴色是该行去处 |
| 10 | `10-hub.svg` | SVG 枢纽 | Agent Loop 最大，线不穿字 |
| 11 | `11-timeline.svg` | SVG 时间线 · Coral | completed 是高潮 |
| 12 | `12-swimlane.svg` | SVG 泳道 | Agent 车道上色 |
| 13 | `13-quadrant.svg` | SVG 四象限 · Grove | 右上 SKILL.md 最大 |
| 14 | `14-focus-detail.svg` | SVG 焦点+细节 · Avocado | 左边判断最大 |
| 15 | `15-light-architecture.svg` | SVG 技术架构默认主题 · Light Technical | 近白画布、浅色执行边界、蓝色只保留给主语义 |

## 记分卡

复制一表一张图。HTML 对照块才填运动/交互；其它写 N/A。所有格仍是 `—` 时只能表示“待评”，不能汇总成 Accept。

| 项 | 记录 |
|---|---|
| 图 ID / 论点 | |
| 评测人 / 日期 | |
| 表面（Web / 桌面）与文档宽度 | |
| 最高证据层 | |
| 理解速度 1–5 | |
| 专业观感 1–5 | |
| 语法是否对 1–5 | |
| 可编辑性 1–5 | |
| 默认宽度可读 1–5 | |
| 和正文的咬合 1–5 | |
| 运动 / 交互（仅 07） | |
| 阻断项 | |
| 未测表面 | |
| 结论 | 无阻断且每项 ≥ 3 才 Accept |
