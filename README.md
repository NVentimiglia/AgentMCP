# SkillsMCP

## Problem
I am vibe coding with multiple agents, each wanting to save duplicated
configurations and skill in various locations. My projects were starting
to look like the [Cursed Repo](https://github.com/Hacksore/cursed-repo).

To solve this I placed my common rules and skills inside a shared MCP server.

## Overview
- Local MCP server (`skills-mcp`) exposes **skills** and **rules** only (stdio MCP).
- `skills-mcp init` creates empty `skills/` + `rules/` layout and copies a minimal `config.toml`.
- Users add Markdown skills and guardrail rules on disk (`paths.skills`, `paths.rules`).
- Supports Cursor, Antigravity, Claude, and all other MCP capable harnessess.

## Skills
- Follow the [Agent Skills specification](https://agentskills.io/specification);
  see also [Anthropic overview](https://docs.anthropic.com/en/agents-and-tools/agent-skills/overview).
- On disk: `paths.skills` (default `skills/`): flat `*.md` or `SKILL.md` in a
  bundle; optional `references/`, `scripts/`, `assets/`.
- `list_skills` returns metadata only; `read_skill(name)` returns the full doc.
- Required frontmatter: `name`, `description`.
- Optional frontmatter: `triggers`, `license`, `compatibility`, `metadata`,
  `allowed-tools`.
- Naming and validation: `src/skills_mcp/skills/schema.py`.
- `paths.shared_skills`: merged with the project; on `name` collision the
  project file wins (`skill_origin: library` on shared rows in `list_skills`).

## Rules
- Guardrail Markdown: one file per rule under `paths.rules` (default `rules/`).
- Required frontmatter: `id`, `version`, `trigger`, `solution`; body optional.
- Schema: `src/skills_mcp/rules/schema.py`.
- On MCP `configure`, parseable `rules/*.md` files concatenate into server
  `instructions`.
- Hosts that drop `instructions` should read those files from disk.
- Use `list_rules` and `read_rules(id)` for selective loading.
- Disk edits need a `skills-mcp` restart (or a new session) to refresh
  `instructions`.

## MCP tools
- `verify_setup`: JSON snapshot with `paths`, `skills_count`, `rules_count`,
  `issues`, `checked_at`.
- `list_skills`: JSON metadata catalog.
- `read_skill`: full Markdown for one skill.
- `list_rules`: JSON rows with `id`, `trigger`, `file`.
- `read_rules`: full Markdown for one rule by YAML `id`.

## Install
```bash
uv pip install -e ".[dev]"
skills-mcp init .
skills-mcp doctor
skills-mcp serve
```

## Configuration (`config.toml`)
- `[paths]`: `skills`, `rules` (directories of Markdown); optional `shared_skills`.

## MCP `instructions`
- Hosts that expose server `instructions` get every parseable
  `paths.rules/*.md`.
- Editing rules while the server runs can leave `instructions` stale until
  restart.
