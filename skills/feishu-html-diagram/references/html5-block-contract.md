# html5-block 细节

主流程和最小代码已经写在 [SKILL.md](../SKILL.md)。只有遇到高度模式、更新已有 block、资源加载或回读问题时才需要阅读本页。

## 高度与布局

`html-box-height-mode` 只有两个受支持值：

- `auto`：适合随正文自然展开的普通图表。根容器使用正常文档流，不设置固定高度或根级 `overflow: hidden`；确实需要滚动的局部区域可以自己设置。
- `viewport`：适合明确使用 `100vh`、内部滚动、分页或缩放的单屏界面，例如仪表盘或画布编辑器。

页面加载后再增加或展开内容，不会可靠触发嵌入客户端重新计算 block 高度。使用 `auto` 时，初始文档流高度应足以容纳读者需要看到的内容。

飞书文档常见阅读宽度约为 820px，但可能更窄。根布局应响应容器宽度，实际测试比依赖固定数字更可靠。

## 文件与资源

HTML 文件上限为 500 KiB。内联图片、Base64、字体、大型 JSON/CSV 和模拟数据都计入文件体积。

外部脚本、样式、字体、图片、数据和网络请求可能受客户端、网络或安全策略影响。它们不是禁止项；保留时要把它们当作明确的运行时依赖，在实际目标客户端验证加载、错误状态和核心阅读体验。

## 更新已有 block

新 block 使用：

```xml
<html5-block path="@./diagram.html"/>
```

更新带有 `data-ref` 的已有 block 时，按当前文档写入能力的要求提供该 reference 的映射，不要发明新的 path 语法或 writer flag。

## 回读

文档 fetch 返回的 XML：

```xml
<html5-block data-ref="html5_1"></html5-block>
```

只是占位符。实际 HTML 通常位于：

```text
document.reference_map["html5-block"]["html5_1"].data
```

如果 entry 给出的是 `path`，则从 fetch 资源目录读取对应文件。确认 block 位置、引用 id 和恢复后的 HTML 都与本次目标一致。
