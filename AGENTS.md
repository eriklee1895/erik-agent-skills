# AGENTS.md

## Repository purpose

This repository is the canonical publishing source for Erik's mature,
reusable Agent Skills.

## Layout

- `skills/`: canonical skill source; each skill lives in its own directory.
- `skills/README.md` and `skills/README.zh-CN.md`: the bilingual skill catalog.
- `docs/`: installation guides and compatibility links for the former catalog paths.
- `assets/`: repository-level visual assets.
- Skill-specific `scripts/`, `tests/`, and `evals/` stay inside their skill directory.

## Rules

- Keep `skills/` as the only tracked source of published skills.
- Keep skill directories flat as direct children of `skills/`; categories belong in the catalog.
- Keep `README.md` and `README.zh-CN.md` aligned.
- Keep README counts and status badges aligned with the current skill catalog.
- Update both `skills/README.md` and `skills/README.zh-CN.md` whenever a skill
  is added, removed, or renamed; classify each by its primary user outcome.
- Keep `docs/skills-catalog.en.md` and `docs/skills-catalog.zh-CN.md` as
  compatibility links, not duplicate catalogs.
- Do not copy secrets, account state, or machine-local runtime data into this repository.
- Writing-workflow skills (ideation, polishing, readiness checks, WeChat/blog
  publishing, post-publication closeout) are coupled to the
  writing-agent-harness project layout and stay sourced there; this repo
  publishes only standalone, cross-project skills.
- Preserve each skill's self-contained `SKILL.md`, scripts, references, and assets.
