# AgentMCP Project

This file is loaded automatically by Claude Code at startup — no MCP server
required. It bootstraps the session before any tools are available.

## Session Start

At the start of every session:

1. Summarize the task in one line.
2. Read `MEMORY.md` from the project memory directory and scan for entries
   relevant to the task.
3. Apply any returned decisions, patterns, or preferences before editing code.
4. If no relevant memory exists, proceed normally. Save useful findings to
   a new memory file before finishing.

If the AgentMCP MCP server is running, also call `list_rules` to load the
full active rule set from `rules/active/`.

## Prompt Rewriting

Before acting on a vague request, silently clarify it internally:

- Add missing success criteria, scope, and constraints.
- Reference specific files or tools when the codebase is known.
- For destructive actions, state the plan and confirm before executing.
- Do not invent requirements — preserve user intent.
