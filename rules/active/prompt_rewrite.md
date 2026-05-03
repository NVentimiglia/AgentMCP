---
id: prompt_rewrite
version: "2026-05-02"
trigger: User request is vague, missing success criteria, location, or constraints.
solution: Silently clarify the request internally before acting on it.
---

# Prompt Rewriting

Before acting on a vague request, silently rewrite it into a clear instruction internally.

## When to apply
- Missing success criteria ("make it faster", "clean this up")
- Missing context ("fix the bug") with no file or reproduction
- Missing constraints (performance, backwards compatibility)
- Multi-step workflows with no ordering

## Rules
- Preserve user intent; do not invent requirements
- Add missing structure: objective, scope, acceptance criteria
- Reference specific files or tools when the codebase is known
- For destructive actions (delete, wide refactor, migrations), state the plan and confirm before executing
