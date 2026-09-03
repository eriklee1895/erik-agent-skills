# 写入与验证

**创建文档、插入画板块、用 token 更新内容、覆盖确认、导出预览：** 按 `lark-doc` / `lark-whiteboard` 做。本页不列 CLI 百科。

本页只固定精排交付时的本地环和证据口径。

## 本地产物

建议目录：`./diagrams/YYYY-MM-DDTHHMMSS/`

```
diagram.svg    SVG 路径
diagram.json   DSL 路径
diagram.mmd    Mermaid 路径
diagram.png    本地预览（交给用户看构图）
```

中文 SVG 必须 UTF-8。写入工具弄坏 XML 中文时：

```bash
python3 -c 'from pathlib import Path; Path("diagram.svg").write_text(src, encoding="utf-8")'
```

## 本地审查（写入前）

```bash
python3 scripts/lint_svg.py diagram.svg          # 仅 SVG
npx -y @larksuite/whiteboard-cli@^0.2.13 -i diagram.svg -f svg --check
npx -y @larksuite/whiteboard-cli@^0.2.13 -i diagram.svg -o diagram.png -f svg
```

`--check` 的 error 清零后再交给 `lark-whiteboard` 写入。DSL / Mermaid 按官方路径渲染，同样先看 PNG。

精排默认把 **SVG 源**交给官方 `+update --input_format svg`（或文档里的 svg 画板块），不要为了中文再绕一圈本地 `--to openapi`，除非官方 workflow 要求 raw。

正文里先用一两句说明这张图回答什么，再放画板，避免图和章节脱节。

## 证据层

| 层 | 含义 | 未做时 |
|---|---|---|
| `lint-valid` | `lint_svg.py` 无 error | 写明跳过 |
| `local-render-valid` | `--check` 无 error，并目视过 PNG | 不得声称「已在飞书验证」 |
| `feishu-write-valid` | 已按官方 skill 写入且 fetch 到目标位置 | 本地成功 ≠ 已写入 |
| `feishu-experience-valid` | 人在飞书 Web 或桌面打开过画板 | 导出 PNG 不能代替 |

飞书 preview 常被垫成近方形大画布，宽图会浮在白边里。那是导出行为。把本地 `diagram.png` 给用户看版式。没有登录时，交付本地文件，并列出未跑的官方写入步骤。
