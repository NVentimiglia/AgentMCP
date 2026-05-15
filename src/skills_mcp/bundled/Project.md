# Project

<!-- Add project goals, conventions, key decisions, and anything agents need to know.
     The skills-mcp:begin/end block below is auto-managed by `skills-mcp analyze` — edit freely outside it. -->

## About this project

<!-- Describe what this project is and what agents should know before starting work. -->

## Rituals

**Session start** — agent does this automatically via MCP instructions:
1. `read_project_doc(project_path=<this directory>)` — loads this file
2. `list_skills` — checks for applicable skills
3. Active rules are already injected into the session

**Session end** — when a notable pattern, correction, or decision emerged:
1. Save conversation → `sessions/YYYY-MM-DD-topic.md`
2. Agent calls `write_project_doc` to persist context here
3. If `sessions_pending` ≥ 3 → run the learn pass (`LEARN.md`)

## Open threads

<!-- Running list of decisions, blockers, and context that should carry into the next session. -->
