# SkillsMCP Project

This file is loaded automatically by Claude Code at startup — no MCP server
required. It bootstraps the session before any tools are available.

## Session Start

At the start of every session:

1. Summarize the task in one line.
2. Read **`paths.rules`** (default **`rules/*.md`**) and apply those guardrails before substantive edits. MCP **`instructions`** echo the same when the harness passes them through.
3. Use **`list_skills` / `read_skill`** via MCP when the project’s **`skills/*.md`** files help.

See [README.md](README.md).

## Self-Learning

This repo supports a learn loop. Sessions are stored in `sessions/`.
Skills are updated from sessions by running the learn pass in `LEARN.md`.

At the END of a session where a notable pattern, correction, or insight occurred:
1. Suggest the user save this session to `sessions/YYYY-MM-DD-topic.md`.
2. Briefly describe what would be extracted (one sentence).
3. Do not run the learn pass automatically — the user triggers it manually.