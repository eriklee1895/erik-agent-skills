# 写入与验证

文档创建、画板块、token、身份、更新与覆盖操作按 `lark-doc` / `lark-whiteboard` / `lark-shared`。本页负责本地检查顺序与交付证据；仅做设计或只读审查时，按能取得的材料报告，不强制走成品写入流程。

## 与介质匹配

| 产物 | 验证路径 |
|---|---|
| 新建 / 修改的 SVG 候选 | 下方几何、lint、parser、原生转换与目视检查 |
| DSL | 底座规定的布局、parser 与渲染检查；不运行 SVG 专用 lint |
| Mermaid / PlantUML | 底座对应源码检查与转换路径；Mermaid 本地候选命令见下方，PlantUML 使用其官方路线；服务端直传与本地预览分别记录 |
| 已有画板审查 / 参考研究 | 读取已有预览、raw 和正文；缺少哪种证据就明确哪种未知，不为审查重建整板 |

## SVG 本地验证

本 skill 的固定 parser 基线是 **0.2.13**；底座示例可能使用兼容版本范围，本地复现采用这里的固定版本。以下命令在 skill 目录执行，`diagram.svg` 替换为实际候选；产物建议放在任务输出目录。UTF-8 文字损坏时从完好的文本源重新生成，不对乱码做猜测式转码。

```bash
python3 scripts/fit_check.py diagram.svg --json
python3 scripts/lint_svg.py diagram.svg
npx -y @larksuite/whiteboard-cli@0.2.13 -i diagram.svg -f svg --check
npx -y @larksuite/whiteboard-cli@0.2.13 -i diagram.svg -f svg --to openapi --format json > diagram.openapi.json
npx -y @larksuite/whiteboard-cli@0.2.13 -i diagram.svg -f svg -o diagram.png
```

工具已可用时不必重复 preflight。若 npx 卡在 registry / 网络解析，而本机已有该版本的安装，可确认 `package.json` 与 `-v` 后，直接使用 `node <已验证安装目录>/bin/cli.js` 执行同样的参数；无需改全局 registry 或登录配置。实际运行其它版本时记录版本，不能沿用 0.2.13 的映射结论。

### 各检查证明什么

| 检查 | 覆盖 | 仍需人工核对 |
|---|---|---|
| `fit_check.py` | 可测量几何的出血、外边距、大块空白；不支持的几何报 `unmeasured-*` | 估算文字宽度、事实、阅读顺序 |
| `lint_svg.py` | 介质限制、marker 引用、声明了 `data-bg` 的文字对比度 | 未声明的配对、颜色语义 |
| parser `--check` | 解析后文字溢出、节点重叠和遮挡诊断 | 有意重叠、完整画面与语义 |
| `--to openapi` | 实际节点类型、箭头字段、坐标或绑定端点 | 客户端的编辑和拖动行为 |
| PNG 目视 | 字形、裁切、间距、走线与颜色；另按预期显示宽度查看 | 飞书正文中的真实显示与交互 |

核对转换结果时逐条检查有向关系：起点、终点、方向与内容应符合事实契约；分隔线和轴不计入有向边。要求可编辑的结构须保持原生；允许局部不可编辑元素时，列明 `image` / `svg` 降级及其影响。`position` 只给坐标，`attached_object` 才记录绑定，二者都不替代实际拖动测试。

错误先修；warning 汇总后判断是否符合设计意图。声明的硬阴影、编号签等重叠可保留，固定 fixture 记录预期 warning。`--margin` / `--deadband` 可按设计契约设置，不能靠放宽参数掩盖出血或未测量几何。

一轮局部修改后确认受影响检查。只有诊断说明当前介质无法保留关键关系或编辑要求时，才按底座切换路线；不要因普通间距问题或缺登录而重画成另一种格式。

## Mermaid 本地候选

需要本地预览或转换证据时，保留 `diagram.mmd`，按官方 `routes/mermaid.md` 的本地路线检查；不运行 SVG 的 fit / lint。下面的命令已用本包 [时序样例](../evals/fixtures/human-eval/06-sequence.mmd) 验证，不代表所有 Mermaid 图类均受支持。

```bash
npx -y @larksuite/whiteboard-cli@0.2.13 -i diagram.mmd -f mermaid --check
npx -y @larksuite/whiteboard-cli@0.2.13 -i diagram.mmd -f mermaid --to openapi --format json > diagram.openapi.json
npx -y @larksuite/whiteboard-cli@0.2.13 -i diagram.mmd -f mermaid -o diagram.png
```

目视 PNG，核对参与者、关系、顺序和转换类型。转换失败时保留源码与诊断，注明本地未验证；用户明确保留格式时不自行改画 SVG。用户已有 Mermaid 源码的写入使用底座 `+update` 的 `mermaid` 输入路径；本地 OpenAPI 是检查材料，不自动替换源格式或证明远端转换结果。

## 写入并回读

已授权写入且候选通过后，将 SVG / DSL / 源码交给相应底座。`--to openapi` 用于检查不意味着必须改用 raw 写入；实际输入格式按官方 workflow。已有画板复用 token，损失语义或整板重建按其覆盖规则处理。

文档前后用一句话说明图的论点，回读确认目标位置与画板类型，再按需要导出 preview。服务端 preview 可能补白或出现文字颜色差异，应区分导出表现与客户端体验；不要为了修预览白边而改坏真实布局。

## 证据与交付口径

| 证据 | 可以声称 | 不能据此声称 |
|---|---|---|
| `lint-valid` | 当前 SVG 通过 lint 的覆盖项 | 全部颜色配对、事实或布局都正确 |
| `local-render-valid` | 当前 parser 检查无阻断错误，PNG 已目视 | 已写入飞书或客户端体验通过 |
| 原生转换 / 绑定检查 | 结构类型、方向和已检查端点字段符合预期 | 节点拖动后一定跟随 |
| `feishu-write-valid` | 写入成功且回读到目标位置 | 客户端可读、可编辑或拖动通过 |
| `feishu-experience-valid` | 在记录的 Web / 桌面表面确认了可读与可编辑 | 未测表面或拖动行为也通过 |
| 拖动绑定实测 | 在记录的客户端移动指定节点后端点跟随 | 其它节点、连接器与表面都已测试 |

交付提供产物位置、关键设计取舍、已完成检查和未测项。仅有方案、源码或截图时如实描述已有证据；审查可以以问题报告完成。需要逐图人工验收时用 [Human eval](../evals/human-eval.md)，保留历史记录。
