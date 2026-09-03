# Human eval · 飞书画板精美图表

用这份清单评 `feishu-whiteboard-diagram` 的**文档精排画板**，不是评官方 `lark-whiteboard` CLI 教程。本地 PNG 只能证明构图；飞书里能不能点开改节点，必须人在 Web / 桌面上看。

配套产物：[`fixtures/human-eval/`](fixtures/human-eval/)。再生：

```bash
python3 evals/generate_human_eval_fixtures.py
python3 scripts/lint_svg.py evals/fixtures/human-eval/01-layered-strip.svg
npx -y @larksuite/whiteboard-cli@^0.2.13 -i evals/fixtures/human-eval/01-layered-strip.svg -f svg --check
```

写入飞书时，在 `fixtures/human-eval/` 下用 `eval-doc.xml` 调 `lark-cli docs +create --doc-format xml --content @./eval-doc.xml --as user`。

## 证据层（先记层，再打分）

| 层 | 含义 | 本包默认 |
|---|---|---|
| `lint-valid` | `lint_svg.py` 无 error | 写入前必做 |
| `local-render-valid` | `--check` 无 error，并目视过 PNG | 写入前必做 |
| `feishu-write-valid` | 已写入且 fetch 到目标章节、类型正确 | 需登录 |
| `feishu-experience-valid` | 人在飞书 Web 和/或桌面打开过画板 | **Human eval** |

没有登录时停在 `local-render-valid`，不要把 PNG 说成「已在飞书验证」。

## 维度（1–5）

白板图默认是静态的：`Semantic motion` 和 `Interaction` 对 SVG/Mermaid 记 **N/A（有意静态）**，只给 HTML 对照块打这两项。有一项低于 3，或出现阻断项，整张图不通过。

| 维度 | 1 | 3 | 5 |
|---|---|---|---|
| 理解速度 | 看不出这张图在回答什么 | 能看出主论点和关系，但要停一下 | 扫一眼就知道分层 / 循环 / 恢复粒度 |
| 专业观感 | 像草稿、海报或监控大屏 | 能放进技术文档，有小毛边 | 浅底、色边分组、编号签、页脚结论，像精排插图 |
| 语法是否对 | 用错骨架（时序画成架构，闭环没有「否」） | 骨架对，个别标注弱 | 与 [grammars.md](../references/grammars.md) 的关系一致，且没有第二种主语法 |
| 可编辑性 | 飞书里是图片 / HTML / 整块嵌入 SVG | 主结构是原生节点，个别菱形嵌入可接受 | 卡片、条带、连线能点开改；装饰 path 没有当骨架 |
| 默认宽度可读 | 文档默认宽度下核心被裁或要放大 | 核心可读，边角略挤 | 默认文档宽度下标题、卡片、页脚都清楚 |
| 和正文的咬合 | 图和前后文字脱节或互相矛盾 | 有一句「这张图回答什么」 | 图推进该节论点，页脚就是读者该带走的话 |

### 阻断项

- 核心文字截断、无意重叠、中文豆腐。
- 把 HTML 动画或截图当成「画板已验证」。
- 工作坊场景只给一张锁死的精排图、没有空白共创板。
- 用户给了 sequenceDiagram，却被重画成架构分层。
- 虚线回填画成实线正向边，或「下一轮」接到结束态。

## 图清单

| ID | 文件 | 介质 | 你要确认的事 |
|---|---|---|---|
| 01 | `01-layered-strip.svg` | SVG 画板 | 四层等宽，职责/边界成列，上下行 API 分色 |
| 02 | `02-task-loop.svg` | SVG 画板 | 胶囊 + 一个菱形；回填是紫虚线，接到判断，不是接到加载上下文 |
| 03 | `03-learning-loop.svg` | SVG 画板 | 「否」有结束；门禁写扫描/去重/质量；下一轮回到任务完成 |
| 04 | `04-multicolumn-runtime.svg` | SVG 画板 | 上请求向右、下事件向左，页脚四句边界 |
| 05 | `05-recovery-layers.svg` | SVG 画板 | 01–03 编号签，右侧每层一个问题，页脚 threadId+turnId+itemId |
| 06 | `06-sequence.mmd` | Mermaid 画板 | 仍是时序，没有被改成分层架构 |
| 07 | `07-packet-flow.html` | html5-block | **不是画板**；暂停/重放可用，静止时也能读完四层 |
| 08 | blank | 空白画板 | 能拖便签；不要和 01–05 精排图混成一张 |

## 记分卡

复制一表一张图。HTML 对照块才填运动/交互；其它写 N/A。

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
