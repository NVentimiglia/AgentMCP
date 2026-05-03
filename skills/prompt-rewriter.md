---
name: prompt-rewriter
description: Rewrite a weak or vague user prompt into a clear,
  well-structured instruction. Use when the request is missing success
  criteria, context, constraints, or step ordering. Triggers: prompt,
  rewrite, clarify.
---

# Prompt Rewriter

Given a vague or incomplete request, rewrite it into a clear prompt
before acting on it.

## Rewrite Goals
- Preserve user intent; do not invent requirements.
- Add missing structure: objective, acceptance criteria, scope.
- Reference specific files or tools when the codebase is known.
- For destructive actions (delete, wide refactor, migrations),
  add an explicit confirmation step.

## When to Trigger
- Missing success criteria ("make it faster", "clean this up").
- Missing context ("fix the bug") with no location or reproduction.
- Missing constraints (performance, backwards compatibility).
- Multi-step workflows with no ordering.

## Output Format
Return only the rewritten prompt in Markdown, prefixed with:

`Rewritten prompt:`

## Example

**Before:** "fix auth"

**After:**
`Rewritten prompt:` Identify where authentication is implemented.
Describe the smallest fix for [specific symptom]. Propose a patch
with tests. List all files touched.
