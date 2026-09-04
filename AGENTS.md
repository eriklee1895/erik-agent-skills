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
- Writing-workflow skills (ideation, polishing, readiness checks, WeChat/blog
  publishing, post-publication closeout) are coupled to the
  writing-agent-harness project layout and stay sourced there; this repo
  publishes only standalone, cross-project skills.
- Preserve each skill's self-contained `SKILL.md`, scripts, references, and assets.
