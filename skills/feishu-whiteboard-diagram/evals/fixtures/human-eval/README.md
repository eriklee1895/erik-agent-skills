# Human-eval fixtures

2026-09-03 Human eval **Accept**。这一包就是文档精排画板的视觉基准：奶油底、墨边、单焦点；分层条带才浅色分组。

Regenerate SVG / Mermaid / HTML / `eval-doc.xml` with:

```bash
python3 ../../generate_human_eval_fixtures.py
```

PNG previews are generated locally with `whiteboard-cli` for `local-render-valid`. They are gitignored and are not proof of Feishu client rendering:

```bash
npx -y @larksuite/whiteboard-cli@^0.2.13 -i 01-layered-strip.svg -o 01-layered-strip.png -f svg
```

Create the live doc from this directory:

```bash
lark-cli docs +create --doc-format xml --content @./eval-doc.xml --as user
```
