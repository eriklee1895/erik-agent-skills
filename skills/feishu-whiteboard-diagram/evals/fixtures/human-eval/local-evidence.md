# Local evidence · 2026-09-03

Highest completed layer: `local-render-valid`.
Not run: `feishu-write-valid`, `feishu-experience-valid` (lark-cli config init waiting for user scan).

| Artifact | lint_svg.py | whiteboard-cli --check | local PNG |
|---|---|---|---|
| 01-layered-strip.svg | ok | errors 0, warnings 0 | 01-layered-strip.png |
| 02-task-loop.svg | warning: one polygon diamond | errors 0, warnings 0 | 02-task-loop.png |
| 03-learning-loop.svg | warning: one polygon diamond | errors 0, warnings 0 | 03-learning-loop.png |
| 04-multicolumn-runtime.svg | ok | errors 0, warnings 0 | 04-multicolumn-runtime.png |
| 05-recovery-layers.svg | ok | errors 0, warnings 0 | 05-recovery-layers.png |
| 06-sequence.mmd | n/a | errors 0, warnings 0 | 06-sequence.png |
| 07-packet-flow.html | html5-block validator exit 0 | n/a | open in browser |

CLI: `@larksuite/whiteboard-cli@0.2.13`. Chinese SVGs written with `Path.write_text(..., encoding="utf-8")`.
