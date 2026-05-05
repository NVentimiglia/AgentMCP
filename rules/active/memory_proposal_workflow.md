---
id: memory_proposal_workflow
version: "2026-05-05"
trigger: Agent encounters repeated patterns, recurring bugs, or lessons learned.
solution: Call memory_store() and propose_rule() to persist knowledge and create reusable guardrails.
---

# Memory & Proposal Workflow

## How This Works

The MCP server provides three key tools for self-improvement:

1. **memory_store(text, tags, source="agent")** — Save patterns, decisions, errors to ChromaDB
2. **memory_search(query, k=5)** — Search stored memory for related knowledge
3. **propose_rule(trigger, solution, source_session_id)** — Create reusable rules

## Checklist: When to Invoke

### Store to Memory (Low Friction)
- [ ] Root cause identified? (Why did this happen? How prevent?)
- [ ] Worth remembering? (Decision, pattern, error, insight)
- Yes → call `memory_store(..., tags=[...])`
- First occurrence is fine; memory handles duplicates

### Propose a Rule (Higher Bar)
- [ ] Pattern seen 2+ times in same session or across sessions?
- [ ] Solution is reusable and generalizable?
- [ ] Would save time on future occurrences?
- All yes → call `propose_rule(trigger, solution, source_session_id)`

### NOT Worth Capturing
- One-off mistakes (typo, unique context)
- Project-specific quirks (non-reusable)
- Already documented (check rules/active/ first)

## Example Scenarios

### Scenario 1: Forgot to Install Dependency
```
First time: memory_store("pytest import failed — use configure_python_environment before running tests", tags=["error"])
Second time: memory_search("pytest import") → found note
            propose_rule("pytest import fails in new session", "Run configure_python_environment before test commands")
```

### Scenario 2: Repeated Code Style Issue
```
memory_store("Limit line length to 80 chars in Markdown per persona.md", tags=["preference"])
propose_rule("Markdown line length exceeds 80 chars", "Use persona.md Writing section as reference")
```

### Scenario 3: Build/Config Bug
```
memory_store("pyproject.toml [build-system] missing backend — causes pip install -e . failure", tags=["problem"])
propose_rule("pip install -e . fails on new clone", "Check pyproject.toml has [build-system] with backend specified")
```

## Implementation Tips

1. **Call memory_store immediately** — no risk, helps future context
2. **Wait for pattern confirmation before propose_rule** — avoids noise
3. **Keep triggers specific** (condition-based, not vague)
4. **Write solutions as markdown** (agents read markdown naturally)
5. **Tag accurately** — memory search uses tags for filtering
6. **Source session ID** — helps trace which session created rule

## What Happens Next

- **Proposals in rules/proposals/** — Await user review
- **User promotes via promote_rule()** — Moves to rules/active/
- **Rules auto-loaded at startup** — Available to all future sessions
- **Changelog recorded** — rules/machine_changelog.jsonl tracks everything
- **Rollback available** — If rule causes problems, revert via rollback_rule()

## Integration with session_start

When a new session begins:
1. Agent calls `list_rules()` to load active rules
2. Agent searches memory for context: `memory_search(task_description)`
3. Agent applies persona.md + loaded rules
4. During session, stores new patterns + proposes new rules

This creates a **self-improving feedback loop** without manual intervention.
