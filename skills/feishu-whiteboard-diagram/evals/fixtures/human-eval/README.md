# Human-eval fixtures

2026-09-03 Human eval **Accept**。这一包就是文档精排画板的视觉基准：奶油底、墨边、单焦点；分层条带才浅色分组。

Regenerate SVG / Mermaid / HTML / `eval-doc.xml` with:

```bash
python3 ../../generate_human_eval_fixtures.py
```

PNG files are local `whiteboard-cli` previews for `local-render-valid`. They are not proof of Feishu client rendering. Create the live doc from this directory:

```bash
lark-cli docs +create --doc-format xml --content @./eval-doc.xml --as user
```
