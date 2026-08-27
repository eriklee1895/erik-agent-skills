# Installation guide

[简体中文](installation.zh-CN.md) | [English](installation.en.md) · [Back to README](../README.md)

This repository can be installed with the [Skills CLI](https://github.com/vercel-labs/skills). The repository layout is intentionally compatible with its GitHub source installation flow: each direct child of `skills/` contains a `SKILL.md`.

## Before you start

You need Node.js and `npx`. The CLI command is `npx skills add`; `npx install` is not the installation command for this repository.

## Install all skills

By default, installation is project-level and targets the detected agents:

```bash
npx skills add eriklee1895/erik-agent-skills --all
```

To install the complete collection globally for all detected agents:

```bash
npx skills add eriklee1895/erik-agent-skills --all -g
```

## Install one skill

Replace the value passed to `--skill` with any name from the [skills catalog](skills-catalog.en.md):

```bash
npx skills add eriklee1895/erik-agent-skills --skill seed-audio-gen
```

For a global Codex installation:

```bash
npx skills add eriklee1895/erik-agent-skills --skill seed-audio-gen -g -a codex -y
```

## Browse and choose

List the skills available in this repository without installing anything:

```bash
npx skills add eriklee1895/erik-agent-skills --list
```

The [skills catalog](skills-catalog.en.md) also includes a ready-to-copy install command for every skill.

## Scope and options

- Omit `-g` for a project-level installation.
- Add `-g` for a global user-level installation.
- Use `-a codex` to target Codex explicitly, or use another supported agent ID.
- Use `-y` to skip confirmation prompts in scripts or CI. `--all` already enables non-interactive mode.
- Use `--copy` if you want copied files instead of the CLI's default linking behavior.

The CLI's behavior and supported agent IDs may evolve. Check `npx skills add --help` when integrating this into automation.
