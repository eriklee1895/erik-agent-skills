# Evaluating the skill

See [validation.md](validation.md) for the recorded validation and its limits.

`evals.json` follows the repository's skill-creator style: realistic user
prompts, expected output and assertions. Sixteen cases marked `automated` have
executable artifact checks. Cases 13–16 assess agent decisions and actual use.

## Automated artifacts

```bash
uv run "$SKILL_DIR/evals/run_evals.py" --suite smoke --out /tmp/earshot-eval
uv run "$SKILL_DIR/evals/run_evals.py" --suite bank --out /tmp/earshot-bank-eval
uv run --no-project python -m unittest discover -s "$SKILL_DIR/tests" -p 'test_*.py' -v
```

Choose a fresh output directory for each run. Artifacts, stdout JSON, stderr
logs and report.json stay outside the skill. Add `--offline` after warming the
wrapper's uv environment to test cache-only execution. Full-bank adds 201 real
renders to smoke, so it takes longer and retains more WAVs. `--jobs` controls
concurrent full-bank rendering (default 2, at most 8).

The runner decodes actual PCM_24 bytes with the standard library, independently
calculates the 5 ms RMS peak, and verifies frame counts, placement, hashes,
repeatability, native output rates, kit cache, custom recipes and failure
behavior. It uses the real wrapper and actual Earshot, not mocked synthesis.
`audio.checks` warnings are retained; known stylistic warnings are not disguised
as failed rendering or erased to make the bank appear uniformly clean.

This runner evaluates **artifact contracts**, not whether an Agent followed the
skill. It explicitly marks agent evaluation and human listening as not run.

## Independent agent use

Give a fresh agent one prompt from cases 13–16, this skill's path, and an empty
temporary project directory. Do not give the intended answer, prior traces or
implementation advice. Let it query the bank/read references/execute scripts.
Inspect its actual files, commands and JSON against each case's assertions.
Record evidence and failures rather than relying on final prose.

For a comparison, give the same task to another fresh agent without this skill
but with the pinned upstream source. Keep time/tool budgets comparable. The
baseline may succeed; do not manufacture a failure or claim skill uplift from
a single task. Compare completion, repeated setup, errors, timing honesty,
preservation and unnecessary model calls as well as the final artifacts.

## Listening (optional, human)

For candidate preferences, compare at a matched playback level and hide labels
when possible. Judge action/material fit, attack/tail, distraction and fit with
narration. A technical pass, VLM opinion or model similarity cannot stand in for
human taste. No listening score is required for ordinary generation, and the
skill does not add an audio-model critic to the runtime.
