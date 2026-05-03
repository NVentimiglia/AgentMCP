# AgentMCP v0.1 — Design

## Goals

- Run one local MCP server. Single user. Stdio transport.
- Share skills, memory, and rules across Cursor, Claude Code, and Antigravity.
- Improve over time: log problems, propose rules, promote on review.
- Rewrite low-quality prompts before they run.
- Stay minimal. No nested LLMs. No subprocesses. No frameworks.

## Non-goals (deferred to v0.2)

- Sub-agents with tool access. Roles ship as skills instead.
- Automatic session hooks. Callers invoke memory tools explicitly.
- Floating-point confidence and decay. Use three discrete states.

## Features

- Skills registry. Markdown files with progressive disclosure. Roles are skills.
- Persistent memory. Vector + lexical search, local embeddings.
- Rules engine. Dual mode: proposal (default) or auto with changelog.
- Prompt rewriter. Lives as a skill, not a tool. The parent harness applies it.
- Problem identifier. Flags recurring issues into the rules queue.
- Cross-harness. Same MCP server registered in all three clients.

## Architecture

```
+-----------+   +-------------+   +-------------+
|  Cursor   |   | Claude Code |   | Antigravity |
+-----+-----+   +------+------+   +------+------+
      \                |                 /
       \               | stdio MCP      /
        \              |               /
         +-------------+--------------+
                       |
              +--------v---------+
              |   agent-mcp      |
              +--------+---------+
                       |
        +--------+-----+-----+--------+
        |        |           |        |
     +--v--+ +---v---+   +---v---+ +--v---+
     |Skill| |Memory |   |Rules  | |Flag  |
     |loadr| |store  |   |engine | |queue |
     +--+--+ +---+---+   +---+---+ +--+---+
        |        |           |        |
     skills/  memory/      rules/     rules/
     *.md     (chroma)     active/    proposals/
                           proposals/
                           CHANGELOG.md
```

Tools exposed over MCP:

- list_skills, read_skill
- memory_search, memory_store, memory_reinforce
- list_rules, propose_rule, promote_rule, rollback_rule
- flag_problem

That is the entire surface.

## Identity

- Repo: AgentMCP
- Package: agent_mcp
- CLI: agent-mcp
- MCP server name in harness configs: agent-mcp

## Installation

```
git clone <repo> AgentMCP
cd AgentMCP
uv venv && source .venv/bin/activate
uv pip install -e .
agent-mcp init
agent-mcp models pull
```

Folder layout after init:

```
AgentMCP/
  src/agent_mcp/
  config.toml
  skills/
    roles/           # role skills replace sub-agents
    prompt-rewriter.md
    session-start.md
  rules/
    active/
    proposals/
    CHANGELOG.md
  memory/            # gitignored, vector store
  state/             # gitignored, server bookkeeping
    clusters.json
  tests/
```

## Setup per harness

Cursor — edit `~/.cursor/mcp.json`:

```json
{ "mcpServers": { "agent-mcp": { "command": "agent-mcp", "args": ["serve"] } } }
```

Claude Code:

```
claude mcp add agent-mcp -- agent-mcp serve
```

Antigravity — Manage MCP Servers, View raw config, paste the same block.

Verify: invoke `list_skills` in each harness.

## Daily ritual

- Start session. Run the `session-start` skill. It calls `memory_search` with the task.
- Work normally.
- Call `flag_problem` when something goes wrong.
- Before exit, call `memory_store` for anything worth remembering.

## Weekly ritual

- Open `rules/proposals/`. Review each. Edit, delete, or run `promote_rule <file>`.
- Skim `rules/CHANGELOG.md` if running auto mode. Run `rollback_rule <id>` for regressions.
- Run `agent-mcp memory prune` to drop stale entries.

## Configuration

`config.toml`:

```
[mode]
rules = "proposal"     # or "auto"

[paths]
skills = "skills"
rules_active = "rules/active"
rules_proposals = "rules/proposals"
memory = "memory"

[memory]
backend = "chromadb"
embedding_model = "BAAI/bge-small-en-v1.5"   # via fastembed
inject_token_budget = 2000

[problems]
similarity_threshold = 0.72
recurrence_count = 3

[rules]
max_auto_promotions_per_day = 5
```

### Hybrid search

Fixed defaults in code. Optional overrides in `[memory]`:

```python
# defaults (when keys omitted)
VECTOR_WEIGHT = 0.7
LEXICAL_WEIGHT = 0.3
```

Optional additions (omit any or all to use defaults and built-in relevance behavior):

```
[memory]
vector_weight = 0.7      # optional
lexical_weight = 0.3     # optional
relevance_floor = 0.5    # optional, drops weak hits
```

**Normalization**

- If neither weight is set, use the defaults above.
- If one weight is set, derive the other so they sum to `1.0`.
- If both are set, normalize so they sum to `1.0`.

Most users never touch these; they are tuning knobs, not architectural choices.

### Cluster bookkeeping

Recurring-proposal state lives next to `config.toml`, not inside `memory/`. **No config knob** — path is hardcoded relative to the project root (`state/`).

`memory/` holds content (vector store). `state/` holds server bookkeeping so pruning and memory tooling stay simple. One JSON file is enough at v0.1; upgrade to SQLite if it grows. A future override could add `[paths] state = "state"`; not in v0.1.

`state/clusters.json` shape:

```json
{
  "clusters": [
    {
      "id": "cl_01H...",
      "member_ids": ["mem_01H...", "mem_01H..."],
      "proposed": true,
      "proposal_filename": "2026-05-02-flaky-tests.md",
      "last_updated": "2026-05-02T10:14:00Z"
    }
  ]
}
```

## Schemas

Skill — markdown with frontmatter:

```
---
name: reviewer
description: Code review role. Read-only. Use Read, Grep, memory_search.
triggers: ["review", "audit"]
---
You are reviewing code. Use only the listed tools...
```

Memory entry:

```
id: ulid
text: str
tags: enum[problem|decision|pattern|preference|error|note]
state: enum[new|reinforced|stale]
created_at: datetime
last_used_at: datetime
use_count: int
source: str
```

Rule — markdown with frontmatter:

```
---
id: ulid
version: 2026-05-02
trigger: "vague test failures with no traceback"
solution: "always print pytest --tb=short"
---
Body explaining context.
```

## Security

- All file tools take basenames, not paths. Server resolves under fixed roots.
- `promote_rule` and `rollback_rule` touch only `rules/`.
- `memory_store` writes only under `memory/`. Tags validated against enum.
- Cluster / recurrence bookkeeping writes only under `state/` (e.g. `clusters.json`).
- Auto mode caps promotions per day. Excess routes to proposals.
- Auto mode cannot delete active rules. Only adds or supersedes.

---

# Development Plan

Instructions for the implementing agent. Execute phases in order. Run tests after each. Stop and prompt the user on ambiguity. Log mistakes to `AGENT.md`.

## Phase 0 — Scaffold

- T0.1 Create repo `AgentMCP/`. Add `pyproject.toml` with deps: `mcp`, `pydantic`, `tomli`, `chromadb`, `fastembed`, `rank_bm25`, `pytest`.
- T0.2 Add `config.toml` with the block from Configuration.
- T0.3 Create folders: `skills/roles/`, `rules/active/`, `rules/proposals/`, `memory/`, `state/`, `tests/`. Add `.gitignore` for `memory/`, `state/`, and `.venv/`.
- T0.4 Implement `agent-mcp init <path>`. Writes the layout into a target (including `state/`; `clusters.json` created when first needed or as empty scaffold per implementation).
- T0.5 Implement `agent-mcp models pull`. Triggers fastembed model download into `~/.agent-mcp/models`.
- T0.6 Implement `server.py` with stdio MCP and one tool: `ping`.
- T0.7 Test: register in Claude Code. Call `ping`. Confirm round-trip.

## Phase 1 — Skills

- T1.1 Define skill schema (frontmatter + body). Add `src/agent_mcp/skills/schema.py`.
- T1.2 Implement `skills/loader.py`. Scan `skills/**/*.md`. Parse, validate, cache.
- T1.3 Implement `list_skills` → `[{name, description, path}]`.
- T1.4 Implement `read_skill(name)` → full body. Resolve by name. Reject paths.
- T1.5 Author starter skills:
  - `skills/session-start.md` (one paragraph, calls memory_search)
  - `skills/prompt-rewriter.md` (full rewrite logic, examples, voice rules)
  - `skills/roles/reviewer.md`
  - `skills/roles/refactorer.md`
  - `skills/roles/researcher.md`
- T1.6 Tests: missing frontmatter rejected; duplicate names rejected; path traversal in `read_skill` rejected.
- T1.7 Register in all three harnesses. Confirm `list_skills` matches.

## Phase 2 — Memory

- T2.1 Implement `memory/store.py` over chromadb. Methods: `add(entry)`, `search(query, k)`, `reinforce(id)`, `prune()`.
- T2.2 Embedding via fastembed. Cache path from config. Fail loud if model missing.
- T2.3 Hybrid scoring: chromadb vector + rank_bm25 over text. Default weights in code (`VECTOR_WEIGHT` / `LEXICAL_WEIGHT`); optional `vector_weight`, `lexical_weight`, `relevance_floor` in `[memory]` with the normalization rules under **Hybrid search**.
- T2.4 Implement `memory_store(text, tags, source="user")`. Default state `new`. Validate tags.
- T2.5 Implement `memory_search(query, k=5)`. Return entries above relevance floor.
- T2.6 Implement `memory_reinforce(ids)`. State `new` → `reinforced`. Updates `last_used_at`.
- T2.7 Implement `prune()`. Drops entries with state `new` and `last_used_at` older than 30 days. Reinforced entries never auto-prune.
- T2.8 Tests: tag enum enforced; reinforce idempotent; prune respects state; hybrid search returns expected ranking on fixtures.

## Phase 3 — Rules engine

- T3.1 Define rule schema. Add `src/agent_mcp/rules/schema.py`.
- T3.2 Implement `rules/loader.py`. Load `rules/active/*.md` at startup and on file change.
- T3.3 Implement `list_rules` → `[{id, trigger}]`.
- T3.4 Implement `propose_rule(trigger, solution, source_session_id)`. In proposal mode: write to `rules/proposals/YYYY-MM-DD-<slug>.md`. In auto mode: write to `rules/active/`, append `CHANGELOG.md`, enforce daily cap.
- T3.5 Implement `promote_rule(filename)`. Move from proposals to active. Append CHANGELOG. Reload.
- T3.6 Implement `rollback_rule(changelog_id)`. Reverse the change byte-for-byte. Append rollback entry.
- T3.7 Tests: proposal mode never writes to active; auto mode always writes CHANGELOG; daily cap enforced; rollback restores prior content; path basenames only.

## Phase 4 — Problem identification

- T4.1 Implement `flag_problem(description, context)`. Stores into memory with tag `problem`.
- T4.2 On each call: hybrid-search prior `problem` entries. Count matches above similarity threshold.
- T4.3 If count ≥ `recurrence_count` and cluster not yet flagged: call `propose_rule` automatically with aggregated trigger and source IDs. Mark cluster as proposed. Read/write cluster state in `state/clusters.json` (see **Cluster bookkeeping**).
- T4.4 Tests: three near-duplicates fire one proposal; unrelated entries fire none; fourth duplicate after firing does not re-trigger.
- T4.5 Tests: proposed-cluster persistence across server restarts (`state/clusters.json`).

## Phase 5 — Hardening

- T5.1 Structured logging to `~/.agent-mcp/log/`. One file per session. Redact memory `text` field.
- T5.2 Implement `agent-mcp doctor`. Checks config, layout, harness registrations, embedding cache.
- T5.3 Integration test: spin up server, call every tool against fixtures, verify outputs.
- T5.4 Write `AGENT.md` at repo root. One section per tool: contract, inputs, outputs, failure modes.
- T5.5 Tag v0.1.0.

## Stop conditions

Stop and prompt the user when:

- A schema choice has more than one reasonable shape.
- A dependency would add significant surface area.
- A test fails after two repair attempts.
- Two phases produce overlapping logic. Propose abstraction first.

---

## Rules Engine Clarifications (Amendment)

This section merges clarifications previously tracked in `Design_2.md`. Where this section conflicts with earlier rules details in this document, this section is authoritative for Phase 3 and the rules-related parts of Phase 4.

### Clarified scope

- Add optional `scope` to rule frontmatter.
- Define deterministic dedup, conflict detection, rollback verification, and staleness review flow.
- Define cluster bookkeeping fields for recurrence (`proposal_filename`, `promoted_rule_id`, centroid link).
- Add optional `[rules]` config keys with code defaults.
- Expand required Phase 3/4 test matrix for rules and clustering behavior.

### Rule schema (clarified)

Rule file under `rules/active/` or `rules/proposals/`:

```md
---
id: rule_01HZX...                # ulid, generated on write
trigger: "vague test failures with no traceback"
solution: "always run pytest with --tb=short"
scope: ["skill:reviewer"]        # optional; omitted/empty = global
version: 2026-05-02T14:00:00Z
last_referenced: 2026-05-02T14:00:00Z
reinforcement_count: 0
source_session_ids: ["sess_..."]
---
Optional body. Free-form notes the user adds during review.
```

Cluster record in `state/clusters.json`:

```json
{
  "clusters": [
    {
      "id": "cl_01HZ...",
      "centroid_embedding_id": "mem_01HZ...",
      "member_ids": ["mem_01HZ...", "mem_01HZ..."],
      "proposed": false,
      "proposal_filename": null,
      "promoted_rule_id": null,
      "last_updated": "2026-05-02T14:00:00Z"
    }
  ]
}
```

### Config additions (optional with defaults)

Add these optional keys under `[rules]`:

```toml
[rules]
mode = "proposal"                    # or "auto"
max_auto_promotions_per_day = 5
inject_token_budget = 2000
dedup_active_threshold = 0.85
dedup_proposals_threshold = 0.80
conflict_trigger_similarity = 0.75
conflict_solution_similarity = 0.40
stale_after_days = 90
```

### Algorithms (clarified)

#### A. Apply rules at session start

- Add MCP tool: `get_active_rules(context_tags: list[str] | None = None)`.
- Load active rules (mtime cache allowed), filter by scope, sort by `reinforcement_count desc` then `last_referenced desc`.
- Pack by `inject_token_budget` using 4-chars/token approximation.
- Return one markdown block; update `last_referenced` for returned rules only.
- If clipped by budget, log warning with clipped count.

#### B. Propose a rule

Tool signature:

```py
propose_rule(trigger: str, solution: str, source_session_id: str, scope: list[str] | None = None)
```

Behavior:

- Build combined text from trigger+solution and embed.
- Dedup against active:
  - If similarity >= `dedup_active_threshold`, bump matched active rule (`reinforcement_count`, `last_referenced`, `source_session_ids`) and return duplicate action.
- Dedup against proposals:
  - If similarity >= `dedup_proposals_threshold`, merge `source_session_ids` and return merged action.
- Otherwise create new proposal (or direct active in auto mode when cap permits).
- Auto mode above daily cap falls back to proposal path.

#### C. Promote

- `promote_rule(filename: str, force: bool = False)`.
- Reject paths (basename-only).
- Re-run dedup against active and block if duplicate now exists.
- Conflict candidate when:
  - trigger similarity >= `conflict_trigger_similarity`
  - and solution similarity <= `conflict_solution_similarity`
- If conflicts and not `force`, return conflict candidates and do not promote.
- On promote: move proposal to active, append changelog, and if linked cluster exists set `promoted_rule_id`.

#### D. Rollback

- `rollback_rule(changelog_id: str)`.
- Parse changelog, locate entry, compute inverse op.
- Refuse rollback-of-rollback.
- Verify current file hash matches changelog `after_sha256` before applying inverse.
- Append a new rollback changelog entry (never mutate history).

#### E. Cluster recurrence

`flag_problem(description, context, source_session_id)` flow:

- Store problem memory and capture `problem_id`.
- Assign to existing cluster by centroid similarity threshold, else create cluster.
- When cluster reaches recurrence threshold and not yet proposed:
  - synthesize simple v0.1 trigger/solution (no LLM),
  - call `propose_rule`,
  - persist `proposed = true` and `proposal_filename`.
- Return `cluster_id` and whether proposal fired.

#### F. Staleness review

Add CLI:

```bash
agent-mcp rules review
```

- Print rule summary including stale marker when `days_since(last_referenced) > stale_after_days`.
- Suggest follow-up actions, but do not auto-delete.

### Safety clarifications

- Rule-facing file params are basenames or ids only.
- Reject `/`, `\`, `..`, and null bytes.
- Resolve under fixed roots only (`rules/active`, `rules/proposals`, `state`).
- Refuse symlinks escaping roots.

### Required test additions

Add/ensure tests for:

- dedup active and dedup proposals behavior
- auto mode changelog and daily-cap fallback
- duplicate blocking on promote
- conflict detection and `force=True` override
- rollback bytes restore and external-change refusal via hash mismatch
- scope filtering and token-budget clipping behavior
- path traversal rejection
- cluster one-shot proposal trigger, no re-trigger, persistence, promotion linkage

### Implementation ordering clarification

For rules module work, implement in this order:

1. schema models (`rules/schema.py`)
2. loader/cache (`rules/loader.py`)
3. embedding wrapper (`rules/embed.py`)
4. dedup helper (`rules/dedup.py`)
5. changelog helper (`rules/changelog.py`)
6. MCP tools including `get_active_rules`
7. cluster persistence (`rules/clusters.py`)
8. `flag_problem` wiring
9. `agent-mcp rules review`
10. full rules/cluster test matrix