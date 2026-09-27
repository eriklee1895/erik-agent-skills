# 社区实践吸收清单

本 skill 借鉴两个公开社区项目的可验证做法，但不复制它们的模板库、脚本或完整工作流：

- [beautiful-feishu-whiteboard](https://github.com/zarazhangrui/beautiful-feishu-whiteboard)：色板目录、飞书 SVG 介质限制、原生形状、渲染后目视修正和“不要把提示词写进画布”。
- [feishu-whiteboard-pro](https://github.com/LcpMarvel/feishu-whiteboard-pro)：8px 节奏、构图原型、焦点必须靠尺寸建立、渲染前 fit-check，以及机械检查和设计评审分离。

## 吸收的玩法

### 1. 先选气质，再开唯一色板

社区目录按 restrained / balanced / bold 和 formality 选风格；本 skill 将它收窄成 `formality + article_tone + diagram_purpose`，
先选 `theme`，再只读取对应色板说明。不要为了比较颜色而一次加载多套 `design.md`，也不要一张图混用多套主色板。

### 2. 把构图当作语法

使用固定的 8px 间距节奏、约 80px 外边距、约 40px 同排沟槽和约 32px 卡片内边距；标题默认左对齐。
从流水线、泳道、枢纽、对比列、分层、时间线、四象限、焦点+细节中按关系选一个主骨架，而不是从均等卡片开始。

### 3. 焦点由尺寸和颜色共同建立

饱和色本身不等于焦点。真正的焦点要更大、留白更多，竞争节点要降级；否则一张图会有多个“第一视觉”。
浅色技术主题也要保留一个明确焦点，只是用浅底、边框和轻量色带代替大面积饱和块。

### 4. 先 fit-check，再 render → look → fix

`scripts/fit_check.py` 负责可预测的画布出血、外边距和大块空白；`lint_svg.py` 负责介质、箭头和对比度；
`whiteboard-cli --check` 负责 parser 层面的溢出 / 重叠；PNG 和真实飞书画板负责最终视觉判断。
发现问题时批量做一次局部修正，再做一次确认渲染，不开启无限审美循环。

### 5. 画布只放成品内容

不把用户提示词、来源说明、色板名称、文件路径、评测标签、版本号或工具过程写进画布。它们可以出现在对话或交付说明中，
但画板本身只保留读者需要理解主题的内容。

## 不吸收的做法

- 不把 35 套模板整包带入本 skill；只保留少量可解释的主题。
- 不把社区示例的海报字号、品牌色或具体业务文案当成通用规则。
- 不把本地 PNG 通过当作飞书真实体验通过；写入、fetch 和人在飞书表面确认仍是更高证据层。

