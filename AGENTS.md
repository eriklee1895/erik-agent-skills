# AGENTS.md

## Repository purpose

This repository is the canonical publishing source for Erik's mature,
reusable Agent Skills.

## Layout

- `skills/`: canonical skill source; each skill lives in its own directory.
- `docs/`: repository-level conventions and workflow documentation.
- `evals/`: prompts, fixtures, and evaluation material for skills.
- `scripts/`: validation, linking, and promotion helpers.

## Rules

- Keep `skills/` as the only tracked source of published skills.
- Do not copy secrets, account state, or machine-local runtime data into this repository.
- Writing skills remain sourced from `writing-agent-harness` until explicitly promoted.
- Preserve each skill's self-contained `SKILL.md`, scripts, references, and assets.
