---
id: verify_memory_proposals
version: "2026-05-05"
trigger: Want to test that memory and proposals are actually working in MCP setup.
solution: Follow this verification checklist using manual MCP tool calls or test scripts.
---

# Verification Checklist: Memory & Proposals

## Pre-Requisites
- [ ] AgentMCP MCP server running (or configured in Claude Code)
- [ ] `rules/active/` directory exists and is writable
- [ ] `rules/proposals/` directory exists and is writable
- [ ] `memory/chroma_db/` directory exists (will be created on first use)
- [ ] Python environment has ChromaDB, fastembed installed

## Test 1: Memory Store Works

Call the MCP tool `memory_store` with test data:
```json
{
  "text": "Test memory entry for verification",
  "tags": ["pattern", "note"],
  "source": "verification_test"
}
```

Expected result:
- [ ] Returns JSON with `id` (ULID)
- [ ] Returns `created_at` timestamp
- [ ] File appears in `memory/chroma_db/`
- [ ] No errors in MCP logs

## Test 2: Memory Search Works

Call `memory_search` with query:
```json
{
  "query": "Test memory verification",
  "k": 5
}
```

Expected result:
- [ ] Returns array of results
- [ ] Test entry from Test 1 appears in results
- [ ] Each result has `id`, `text`, `tags`, `score`
- [ ] Score is 0.0 to 1.0 (higher = better match)

## Test 3: Proposal Create Works

Call `propose_rule`:
```json
{
  "trigger": "Test trigger condition",
  "solution": "# Test Solution\n\nThis is a test proposal rule.",
  "source_session_id": "verification_test_session"
}
```

Expected result:
- [ ] Returns JSON with `path` (e.g., "rules/proposals/2026-05-05-test-trigger-condition.md")
- [ ] File actually created at that path
- [ ] File contains valid YAML frontmatter + markdown body
- [ ] Changelog entry in `rules/machine_changelog.jsonl`

## Test 4: Proposal File Format

After Test 3, check the proposal file:
```bash
cat rules/proposals/YYYY-MM-DD-*.md
```

Expected format:
```yaml
---
id: <ULID>
version: <date>
trigger: Test trigger condition
solution: # Test Solution
...
---
# Test Solution

This is a test proposal rule.
```

## Test 5: Promotion Works

Call `promote_rule` with the filename from Test 3:
```json
{
  "filename": "2026-05-05-test-trigger-condition.md"
}
```

Expected result:
- [ ] File moved from `rules/proposals/` to `rules/active/`
- [ ] Same filename, same content
- [ ] Changelog entry records the promotion
- [ ] Proposal file no longer exists

## Test 6: Active Rule Visible

Call `list_rules`:
```json
{}
```

Expected result:
- [ ] Returns JSON array of active rules
- [ ] Test rule from Test 5 appears in list with `id` and `trigger`
- [ ] Can find your test rule by `trigger` field

## Test 7: Metrics Recorded

Call `get_metrics`:
```json
{}
```

Expected result:
- [ ] Returns JSON with tool usage counts
- [ ] `memory_store`: count >= 1 (from Test 1)
- [ ] `memory_search`: count >= 1 (from Test 2)
- [ ] `propose_rule`: count >= 1 (from Test 3)
- [ ] `promote_rule`: count >= 1 (from Test 5)
- [ ] `list_rules`: count >= 1 (from Test 6)

## Troubleshooting

| Issue | Check |
|-------|-------|
| "embedding model not found" | Run `agent-mcp models pull` in terminal |
| Proposal file not created | Check `rules/proposals/` permissions, disk space |
| ChromaDB error | Delete `memory/chroma_db/chroma.sqlite3` and retry |
| Memory search returns empty | Ensure entries exist with `memory_store` first |
| Metrics show 0 | MCP server not logging or metrics.json not writable |

## Full End-to-End Test Script (Manual)

```python
# 1. Store memory
memory_store("E2E test pattern identified", tags=["pattern"])

# 2. Search it back
memory_search("E2E test")  # Should find it

# 3. Propose a rule
propose_rule(
    trigger="E2E test detected",
    solution="# E2E Test Rule\n\nThis is an automated test.",
    source_session_id="e2e_test"
)

# 4. List proposals (check file exists)
# ls rules/proposals/

# 5. Promote it
promote_rule("2026-05-05-e2e-test-detected.md")

# 6. Verify it's active
list_rules()  # Should include the rule

# 7. Check metrics
get_metrics()  # Should show counters > 0
```

## Success Criteria

All 7 tests pass **and**:
- [ ] No errors in MCP server logs
- [ ] No permission denied errors
- [ ] Files persist across MCP restarts
- [ ] Metrics accumulate over time
- [ ] Can retrieve stored memories days later
