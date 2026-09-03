---
name: feishu-html-diagram
description: Use when 需要在飞书文档中创建并嵌入可编程 HTML Diagram，使用 HTML/CSS/SVG/Canvas/JavaScript/D3 实现高自由度布局、动态数据流、交互说明或数据可视化；尤其适合 Mermaid、飞书画板、表格或静态图片难以表达的场景，不适用于独立 Web App 或必须原生协作编辑的画板。
metadata:
  author: liyuheng.erik
---

# 飞书文档 HTML Diagram

## 它是什么

`html5-block` 是飞书 Docx XML 中引用 HTML 文件的嵌入块。Agent 在任务工作区创建一个完整的单文件 HTML，再通过 `<html5-block path="@./diagram.html"/>` 写入文档；飞书把文件保存为文档引用资源，并在隔离的 iframe 中渲染。

它不是截图，也不是一种受限的画图 DSL，而是“长在文档里的小网页”：DOM 文本可以保持清晰与可选择，CSS 可以自由排版，SVG/Canvas 可以绘制几何和数据，JavaScript 与 D3 可以表达状态、流向、交互和动态数据叙事。

## Quick Start

### 1. 在任务工作区创建 HTML

从这个最小骨架开始，再自由设计页面：

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="use-iframe" content="true">
  <meta name="html-box-height-mode" content="auto">
  <meta name="description" content="这张图向读者解释什么">
  <title>图表标题</title>
</head>
<body>
  <!-- 使用 HTML/CSS/SVG/Canvas/JavaScript/D3 创作 -->
</body>
</html>
```

普通文档图默认使用 `auto`，让内容按文档流自然撑高；只有仪表盘、编辑器等明确需要单屏视口和内部滚动的内容才使用 `viewport`。高度模式的边缘行为见 [html5-block 细节](references/html5-block-contract.md)。

### 2. 写入前做轻量预检

将脚本路径解析为相对于本 `SKILL.md` 的 `scripts/validate_html_block.py`，然后运行：

```bash
python3 /resolved/skill-dir/scripts/validate_html_block.py /absolute/path/to/diagram.html
```

这个脚本只检查飞书嵌入边界，不评价设计，也不限制动画、交互、D3、网络请求或内联数据。Error 必须先修复；warning 需要结合实际用途判断。

### 3. 写入飞书 Docx XML

在用户授权的目标章节插入：

```xml
<html5-block path="@./diagram.html"/>
```

`@./` 指向本次文档写入携带的本地文件。修改已有 HTML block 时，需要保留并按文档写入能力要求提供原有 `data-ref` 的引用映射；细节见 [html5-block 细节](references/html5-block-contract.md)。

### 4. 回读并验证

写入成功不等于内容已经正确关联或渲染。重新读取文档，确认 block 位于目标章节。回读 XML 通常只显示：

```xml
<html5-block data-ref="html5_1"></html5-block>
```

真正的 HTML 在 `document.reference_map["html5-block"]["html5_1"].data`，或者该引用给出的本地资源路径中。核对它与预期文件一致，再到实际飞书 Web/桌面端查看布局、动效和交互。

## 为什么选择 HTML Diagram

- **排版自由。** CSS Grid、Flex、卡片、分层、标签和响应式布局可以做出 Mermaid 难以控制的信息层级。
- **表达上限高。** SVG 适合连线、拓扑和动态路径；Canvas 适合密集或自定义绘制；D3 适合数据驱动布局、过渡和探索。
- **动态有语义。** 流动箭头、状态迁移、时间演进和逐步解释可以直接展示静态图无法表达的过程。
- **可以交互。** Tab、筛选、切换、展开和可重放演示能承载渐进披露，同时保留完整默认状态。
- **适合文档阅读。** 图与正文处于同一阅读流，不需要跳转到外部网页；源码仍是可维护、可复用、可版本管理的 HTML。

## 适用场景与边界

| 需求重点 | 优先选择 |
| --- | --- |
| 文档内需要动画、交互或 CSS 自由排版的架构 / 数据流 / 状态机 | 本 skill |
| 标准流程、时序或依赖关系，重视简洁文本语法 | Mermaid |
| 文档内可二次编辑的精美架构 / 流程 / 分层画板 | `feishu-whiteboard-diagram` |
| 多人拖拽、贴便签、现场共创和飞书内原生编辑 | `lark-whiteboard` |
| 数据计算、筛选、透视和普通统计图 | 飞书表格/图表 |
| 展示真实 UI、现场证据或追求最大静态兼容性 | 图片/截图 |
| 认证、持久状态、多页面路由、公开 URL 或完整业务操作 | 独立 Web 开发流程 |

## 创作方法

Agent 已经擅长 Web 创作；本 skill 不提供生成器，也不规定图表语法。先明确读者需要理解的论点、实体、关系、顺序、数量和状态，再选择最自然的 Web 原语：

- 卡片、分层、对比和说明性排版优先使用 HTML/CSS。
- 精确连接、拓扑、路径动画和复杂空间关系使用 SVG。
- 大量像素、自定义渲染或高频绘制使用 Canvas。
- 数据驱动布局、探索和过渡可使用 D3 或其他合适的 H5/JS 库。
- JavaScript 只需服务于真实的状态、交互或叙事，不必为了“动态”而动态。

模板只是灵感，不是白名单。因果回路、运行模型、渐进披露、地图、时间演进或尚未命名的新视觉语法都可以使用，只要更有助于读者理解。

## 最低平台护栏

- HTML 文件不超过 500 KiB；大图片、字体或数据集应评估体积和加载方式。
- 根布局使用 `width: 100%`、`max-width: 100%` 和 `box-sizing: border-box`，不要假设宽屏画布。
- `auto` 模式避免固定根高度和根级 `overflow: hidden`；动态追加内容不会可靠触发 block 重新测高。
- 默认状态必须有意义，不能只有点击或依赖加载成功后才出现核心信息。
- 外部库、字体、图片、接口和数据源可以使用，但它们是需要在实际飞书客户端验证的运行时依赖。
- 不要在 HTML、注释或内嵌数据中写入凭证、token、私有签名 URL 或其他敏感信息。
- 持续动效应考虑阅读干扰、暂停/重置和 reduced-motion；这些是设计判断，不是 preflight 脚本的硬编码策略。

## 验证与交付

验证分为四个事实层级，不必为了流程而制造形式：

1. **文件契约：** preflight 没有 error，warning 已人工判断。
2. **本地体验：** 在正常文档宽度和更窄宽度检查默认状态、console、必要的交互和动效。
3. **飞书写入：** 回读 XML、位置和 `reference_map`，确认关联的是预期 HTML。
4. **飞书体验：** 在实际承诺的 Web 和/或桌面端由人检查最终阅读与交互效果。

只报告真正完成的层级；本地预览或 XML 写入成功不能证明飞书客户端体验。需要正式评测或排查时再阅读 [详细验证指南](references/validation.md)。

## 可选起点（参考样例）

[分层系统架构](assets/templates/layered-system-architecture.html)、[动态数据流](assets/templates/animated-data-flow.html)、[标签页式说明](assets/templates/tabbed-explainer.html)、[D3 数据叙事](assets/templates/d3-data-story.html)、[多标签动态架构](assets/templates/tabbed-animated-architecture.html) 和 [Three.js 嵌入场景](assets/templates/threejs-embedded-scene.html) 是可拆解的起点。后两个样例用于复用容易出错的动画生命周期与三维嵌入骨架；它们不是图表类型白名单。可以借用局部原语，也可以完全重新设计。

交付时说明图的读者目的、HTML 文件位置、目标文档章节、使用了哪些动态/交互/外部依赖，以及哪些本地或飞书端验证已经实际完成。
