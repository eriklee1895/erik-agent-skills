# Human-eval fixtures

2026-09-03 的上一版获得过定性 Human eval **Accept**。当前候选已调整色彩对比度、连线角色与验证规则，并于 2026-09-04 达到 `local-render-valid`；重新完成飞书 Web / 桌面逐图评分前，不得称 `feishu-experience-valid`。验证记录见 [`current-local-evidence.md`](current-local-evidence.md)。

Regenerate SVG / Mermaid / HTML / `eval-doc.xml` with:

```bash
python3 ../../generate_human_eval_fixtures.py
```

PNG previews are generated locally with `whiteboard-cli` for `local-render-valid`. They are gitignored and are not proof of Feishu client rendering:

```bash
npx -y @larksuite/whiteboard-cli@^0.2.13 -i 01-layered-strip.svg -o 01-layered-strip.png -f svg
```

Create the live doc from this directory. First run without approval bypass:

```bash
bash ../../create_human_eval_doc.sh
```

If the CLI returns exit 10, show the action and risk to the user. After explicit approval for this run, execute `bash ../../create_human_eval_doc.sh --yes`.
