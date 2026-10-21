# 安装指南

[English](installation.en.md) | [简体中文](installation.zh-CN.md) · [返回 README](../README.zh-CN.md)

本仓库可以使用 [Skills CLI](https://github.com/vercel-labs/skills) 安装。仓库结构专门保持为兼容 GitHub 源安装的形式：`skills/` 下的每个一级子目录都包含一个 `SKILL.md`。

## 开始之前

需要先安装 Node.js，并确保可以使用 `npx`。本仓库使用的命令是 `npx skills add`，不是 `npx install`。

## 一键安装全部 skills

默认按项目级安装，并写入 CLI 检测到的 Agent 目录：

```bash
npx skills add eriklee1895/erik-agent-skills --all
```

如果要为所有检测到的 Agent 做全局安装：

```bash
npx skills add eriklee1895/erik-agent-skills --all -g
```

## 单独安装某个 skill

将 `--skill` 后的名称替换为[Skills 目录](../skills/README.zh-CN.md)中的任意名称：

```bash
npx skills add eriklee1895/erik-agent-skills --skill seed-audio-gen
```

例如，为 Codex 做全局安装：

```bash
npx skills add eriklee1895/erik-agent-skills --skill seed-audio-gen -g -a codex -y
```

## 先查看再选择

只列出本仓库可用的 skills，不执行安装：

```bash
npx skills add eriklee1895/erik-agent-skills --list
```

[Skills 列表](../skills/README.zh-CN.md)可直达各 skill 的使用说明；将对应名称用于 `--skill` 即可。

## 安装范围与常用选项

- 不加 `-g`：项目级安装。
- 加上 `-g`：全局用户级安装。
- 加上 `-a codex`：明确指定安装到 Codex，也可以替换为其他受支持的 Agent ID。
- 在脚本或 CI 中使用 `-y`：跳过确认提示；`--all` 已经会启用非交互模式。
- 使用 `--copy`：复制文件，而不是使用 CLI 默认的链接方式。

CLI 的行为和支持的 Agent ID 可能会变化；把命令接入自动化流程前，可以运行 `npx skills add --help` 查看当前版本说明。

## 安装之后

安装会添加 skill 的说明和配套文件。运行工具、服务凭据及所需的辅助 skills
需要另行配置；第一次使用前，请阅读所选 skill 的前置条件和认证说明。
