Perform a complete installation of the SkillsMCP server from the current
directory.

## Bootstrapping note

`CLAUDE.md` is loaded by Claude Code at startup with no server required.
Markdown rules live under **`paths.rules`** — default **`rules/*.md`** —
and optionally mirror via MCP **`instructions`** during sessions.
Without MCP or **`instructions`**, **`CLAUDE.md`** remains the portable bootstrap alongside on-disk **`rules/*.md`**.

## Steps

1. Server setup: **`pip install -e .`** (or **`uv pip`**), **`skills-mcp init .`**.
2. MCP integration — same JSON block as **`README.md`**, **`SKILLS_MCP_ROOT`** pointing at the project directory.
3. Confirm **`CLAUDE.md`** exists. Session-start rituals should **not** live only behind MCP tooling.
4. Permissions: locate/edit harness config under `%APPDATA%`, `~/.cursor`, etc.

Report back plus **`skills-mcp doctor`** result.
