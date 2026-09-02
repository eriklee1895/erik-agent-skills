# 详细验证指南

普通任务按 [SKILL.md](../SKILL.md) 的四层验证即可。本页用于正式评测、复杂交互或出现客户端差异时。

## Preflight

`scripts/validate_html_block.py` 是轻量平台预检，不是 HTML/CSS/JS linter。

它把以下问题视为 error：文件不存在、不是 UTF-8、超过 500 KiB、缺少 HTML/head/body 主结构、charset 不是 UTF-8、`use-iframe` 不是 `true`、高度模式不是 `auto` 或 `viewport`。

以下问题只产生 warning：缺少 HTML5 doctype、响应式 viewport、标题或读者描述；使用外部资源或可能无法随 block 携带的相对资源；出现疑似敏感信息。Warning 需要结合实际内容复核，不代表图表不可用。

脚本不会评价视觉质量，也不会禁止动画、网络调用、内联数据、Canvas、D3 或其他创作方式。

## 本地体验

- 记录正常文档宽度和至少一个更窄宽度，检查裁切、重叠、字号和连接关系。
- 检查默认状态和 console。核心论点不应依赖首次点击才能理解。
- 有交互时走完承诺的状态和返回路径；有持续动效时检查阅读干扰以及适用的暂停、重置和 reduced-motion 行为。
- 有外部依赖时检查成功、加载中和失败状态；是否需要静态降级由内容用途决定。

## 飞书写入与体验

写入后 fetch 目标文档，确认 block 在正确章节，并按 [html5-block 细节](html5-block-contract.md) 从 `reference_map` 恢复 HTML。Writer 成功响应只能证明请求成功，不能证明文档位置、资源关联或客户端渲染正确。

最终体验需要在实际承诺的 Feishu Web、桌面端或两者中检查。报告已测试的 surface、关键交互和发现的问题；没有检查的 surface 保持未验证。

正式评测可以使用 `evals/human-eval-rubric.md`，但普通交付不必强制输出 `contract-valid` 等术语。
