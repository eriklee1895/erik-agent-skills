# Human-eval fixtures

Regenerate SVG / Mermaid / HTML / `eval-doc.xml` with:

```bash
python3 ../../generate_human_eval_fixtures.py
```

PNG files are local `whiteboard-cli` previews for `local-render-valid`. They are not proof of Feishu client rendering. Create the live doc from this directory:

```bash
lark-cli docs +create --doc-format xml --content @./eval-doc.xml --as user
```
