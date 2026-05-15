# Learn Pass

Run this prompt in Claude Code or Cursor when you want to distill recent
sessions into skill updates. Point the agent at this file and say "run the learn pass."

---

## Instructions for the agent running this pass

You are performing a learn pass on the SkillsMCP knowledge base.

### Inputs
- `sessions/*.md` — raw conversation logs (source of truth, never modify)
- `skills/*.md` — existing skill files (you will update these)
- `skills/index.md` — catalog of all skills (update summaries here)
- `skills/_candidates.md` — stubs for emerging patterns (review and update)
- `sessions/log.md` — append-only learn log (append one entry when done)

### Workflow

1. Read `sessions/log.md`. Note the date of the last learn pass.
2. Read `skills/index.md` and `skills/_candidates.md` to understand current coverage.
3. List all files in `sessions/` modified after that date.
   If no log entry exists, process all session files.
4. For each new session file:
   a. Read it fully.
   b. Extract: techniques used, mistakes corrected, patterns that worked,
      prompts that were effective, rules that were reinforced or violated.
   c. For each extracted insight, decide:
      - Does an existing skill cover this? → update that skill.
      - Is this a new pattern worth capturing? → create a new skill file or add to `_candidates.md`.
      - Is this a one-off? → skip.
5. When updating a skill:
   - Preserve existing content; add or revise sections.
   - Keep the required frontmatter (`name`, `description`).
   - Add a `## Learned` section if none exists; append bullet points.
   - Do not remove content unless it directly contradicts new evidence.
6. When creating a skill:
   - Use the existing `skills/` file format and frontmatter schema.
   - File name: kebab-case topic (e.g. `react-state-patterns.md`).
   - Required frontmatter: `name`, `description`.
   - Write a `## Summary`, `## When to use`, `## Steps or patterns`, `## Examples` (if any).
7. Update `skills/index.md` with any new skills or updated descriptions.
8. After processing all sessions, append one entry to `sessions/log.md`:

```
## [TODAY] learn | <one-line summary of what changed>
- Sessions ingested: file1.md, file2.md
- Skills updated: skill-a.md, skill-b.md
- Skills created: new-skill.md (if any)
- Notes: <flag contradictions, gaps, or skills that need human review>
```

### Rules
- Never modify session files.
- Never delete skill content; only add or revise.
- If a session contradicts an existing skill, flag it in the log — do not silently overwrite.
- If a session is too short or generic to yield a skill insight, skip it and note it in the log.
- One learn pass should touch at most 10–15 skill files. If more are warranted, do a second pass.
