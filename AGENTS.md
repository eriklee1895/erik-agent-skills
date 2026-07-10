# AGENTS.md

## Repository purpose

This repository is the canonical publishing source for Erik's mature,
reusable Agent Skills.

## Layout

- `skills/`: canonical skill source; each skill lives in its own directory.
- `docs/`: bilingual skill catalog, repository conventions, and workflow documentation.
- `evals/`: prompts, fixtures, and evaluation material for skills.
- `scripts/`: validation, linking, and promotion helpers.

## Rules

- Keep `skills/` as the only tracked source of published skills.
- Keep skill directories flat as direct children of `skills/`; categories belong in the catalog.
- Keep `README.md` and `README.zh-CN.md` aligned.
- Keep README counts and status badges aligned with the current skill catalog.
- Update both `docs/skills-catalog.en.md` and `docs/skills-catalog.zh-CN.md`
  whenever a skill is added, removed, or renamed.
- Do not copy secrets, account state, or machine-local runtime data into this repository.
- Writing skills remain sourced from `writing-agent-harness` until explicitly promoted.
- Preserve each skill's self-contained `SKILL.md`, scripts, references, and assets.
