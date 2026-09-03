# 写入与验证

## 本地产物

建议目录：`./diagrams/YYYY-MM-DDTHHMMSS/`

```
diagram.svg    SVG 路径
diagram.json   DSL 路径
diagram.mmd    Mermaid 路径
diagram.png    本地预览（交给用户看构图）
```

中文 SVG 用 UTF-8 保存。写入工具若会弄坏 XML 中文，用：

```bash
python3 -c 'from pathlib import Path; Path("diagram.svg").write_text(src, encoding="utf-8")'
```

## 预检与渲染

```bash
python3 scripts/lint_svg.py diagram.svg          # 仅 SVG
npx -y @larksuite/whiteboard-cli@^0.2.13 -i diagram.svg -f svg --check
npx -y @larksuite/whiteboard-cli@^0.2.13 -i diagram.svg -o diagram.png -f svg
```

DSL / Mermaid 把 `-f svg` 去掉（或 `-f dsl` / 按扩展名推断）。`--check` 的 error 清零后再写入。

## 插入正在写的文档

需要 `lark-cli` 已 `auth login`，身份 `--as user`。XML 创作（摘自 lark-doc）：

```xml
<title>文档标题</title>
<h1>章节</h1>
<p>这张图画的是……</p>
<whiteboard type="svg" path="@./diagram.svg"></whiteboard>
```

新建文档：

```bash
lark-cli docs +create --api-version v2 --doc-format xml --as user \
  --content @./doc.xml
```

响应里 `document.new_blocks[]` 中 `block_type == "whiteboard"` 的 `block_token` 就是画板 token。追加到已有文档用 `docs +update --command append`。更新已有画板内容用 `whiteboard +update`，不要再插一块空白画板。

覆盖非空画板必须带 `--overwrite`，并先确认会整板重建。幂等 token 至少 10 个字符，同一次逻辑写入在重试时复用，不要每次换时间戳。

```bash
# 推荐：服务端按 SVG 解析，保留中文
lark-cli whiteboard +update --whiteboard-token <token> \
  --input_format svg --source @./diagram.svg --overwrite --as user

# DSL：先转 OpenAPI
npx -y @larksuite/whiteboard-cli@^0.2.13 -i diagram.json --to openapi --format json \
  | lark-cli whiteboard +update --whiteboard-token <token> \
      --source - --input_format raw --idempotent-token <token> --overwrite --as user
```

## 回读

```bash
lark-cli docs +fetch --api-version v2 --doc <url> --as user
lark-cli whiteboard +export --whiteboard-token <token> --output-type preview --output ./feishu.png --as user
```

飞书 preview 常被垫成近方形大画布，宽图会浮在白边里。那是导出行为，不是构图失败。把本地 `diagram.png` 给用户看版式。

## 证据层

| 层 | 含义 | 未做时 |
|---|---|---|
| `lint-valid` | `lint_svg.py` 无 error；DSL/Mermaid 无此层或仅 `--check` | 写明跳过 |
| `local-render-valid` | `--check` 无 error，并目视过 PNG | 不得声称「已在飞书验证」 |
| `feishu-write-valid` | 授权写入且 fetch 到目标位置 | 本地成功 ≠ 已写入 |
| `feishu-experience-valid` | 人在飞书 Web 或桌面打开过画板 | 导出 PNG 不能代替 |

没有 `lark-cli` 登录时，交付本地 SVG/PNG 和插入用的 XML 片段，明确列出未跑的写入步骤。
