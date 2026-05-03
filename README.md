# AgentMCP — User Guide

AgentMCP is a local MCP server (`agent-mcp`) that gives you shared skills, memory, and rules across Cursor, Claude Code, and Antigravity.

## Overview

AgentMCP is designed for one local user and stdio transport.

- Single-user, local-first workflows
- Skill-driven behavior (`skills/*.md` and `skills/roles/*.md`)
- Persistent hybrid memory (vector + lexical)
- Proposal-first rules workflow with promotion and rollback
- Problem recurrence tracking through `flag_problem`

```text
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

## High-Level Features

- **Skills registry**: markdown skills with frontmatter and role-based specialization.
- **Full skill spec support**: directory-based skills with `SKILL.md` plus optional `references/`, `scripts/`, and `assets/`.
- **Persistent memory**: searchable memory entries for decisions, patterns, and problems.
- **Rules engine**: one guardrail per Markdown file under `rules/active/`; proposals in `rules/proposals/`; optional bounded auto mode.
- **Changelog and rollback**: track rule lifecycle and recover from regressions.
- **Cross-harness**: same server entry in Cursor, Claude Code, and Antigravity.
- **Usage metrics**: persistent counters for tool use, per-skill reads, memory stored (including character totals), and rule/problem actions (`get_metrics`).

## MCP Tool Surface

| Tool | Description |
| --- | --- |
| `list_skills` | Lists available skills from the skills registry. |
| `read_skill` | Returns full content for a named skill. |
| `list_skill_files` | Lists files inside a skill root (optionally `references`, `scripts`, or `assets`). |
| `read_skill_file` | Reads a file from within a skill root (path traversal protected). |
| `memory_search` | Searches stored memory with hybrid retrieval. |
| `memory_store` | Stores a new memory entry with tags and source. |
| `memory_reinforce` | Reinforces existing memory entries by id. |
| `list_rules` | Lists active rules (one rule per `rules/active/*.md`; see Add/Update/Remove Rules). |
| `propose_rule` | Creates a new rule proposal for review. |
| `promote_rule` | Promotes a proposal into active rules. |
| `rollback_rule` | Reverts a prior rules change via changelog id. |
| `flag_problem` | Logs a problem report and tracks recurrence signals. |
| `get_metrics` | Returns JSON usage counters (tool calls, per-skill touches, memory/rule/problem aggregates). Persisted under `state/metrics.json`. |

## Install and Setup (Quick Start)

### Prerequisites

- Python 3.11+
- `uv` installed
- One supported harness: Cursor, Claude Code, or Antigravity

### 1) Install AgentMCP

```bash
git clone <repo> AgentMCP
cd AgentMCP
uv venv
source .venv/bin/activate
uv pip install -e .
agent-mcp init
agent-mcp models pull
```

### 2) Confirm Project Layout

```text
AgentMCP/
  src/agent_mcp/
  config.toml
  skills/
    roles/
    prompt-rewriter.md
    session-start.md
  rules/
    active/
    proposals/
    CHANGELOG.md
  memory/            # gitignored
  state/             # gitignored
    clusters.json
    metrics.json   # created after first MCP tool invocation
  tests/
```

### Usage metrics

The server persists aggregate counters in `state/metrics.json` (gitignored alongside other state). Values update on each MCP tool call:

- **`tools`**: counts per MCP tool name (including `get_metrics`).
- **`skills`**: how often a named skill was touched via `read_skill`, `list_skill_files`, or `read_skill_file` (not incremented for `list_skills` alone).
- **`memory`**: `stores`, `searches`, `reinforces`, and `context_chars_stored` (sum of lengths of texts passed to `memory_store`).
- **`rules`**: `list`, `propose`, `promote`, `rollback` tallies aligned with rule tools.
- **`problems`**: `flagged` count from `flag_problem`.

Call **`get_metrics`** from your harness anytime to inspect the snapshot. Counters accumulate across server restarts until you delete `metrics.json`.

### 3) Connect a Harness

### Cursor

Edit `~/.cursor/mcp.json`:

```json
{ "mcpServers": { "agent-mcp": { "command": "agent-mcp", "args": ["serve"] } } }
```

### Claude Code

```bash
claude mcp add agent-mcp -- agent-mcp serve
```

### Antigravity

In Antigravity, open **Manage MCP Servers**, switch to **View Raw Config**, and add the same `agent-mcp` server block:

```json
{ "mcpServers": { "agent-mcp": { "command": "agent-mcp", "args": ["serve"] } } }
```

### 4) Verify Connection

Run `list_skills` in each harness and confirm you get results.

## User Journeys

### 1) Start a Work Session

**What it is**

Bootstrapping context before work starts.

**Why we do it**

Reduces re-discovery and aligns work with prior decisions.

**Manual flow**

1. Run `read_skill("session-start")`.
2. Summarize your current task.
3. Call `memory_search(query=<task summary>, k=5)`.
4. Start work using relevant hits.

**Automation workaround (Cursor/Antigravity hooks)**

```text
onSessionStart:
  - call_tool: read_skill(name="session-start")
  - prompt_or_derive: task_summary
  - call_tool: memory_search(query="${task_summary}", k=5)
  - attach_results_to_context: top_hits
```

### 2) Capture Durable Knowledge

**What it is**

Saving high-value decisions/patterns/issues for future retrieval.

**Why we do it**

Builds institutional memory and reduces repeated mistakes.

**Manual flow**

Call this right after important decisions, tricky fixes, repeatable discoveries, at end-of-task/session, or before context-switching.

1. Call `memory_store(text, tags, source)`.
2. Use meaningful tags (`decision`, `pattern`, `preference`, `problem`, `error`, `note`).
3. Reinforce important items with `memory_reinforce`.

**Automation workaround (`memory_store` hook)**

Trigger on milestone-like events (PR summary, task complete, incident fixed):

```text
onTaskComplete:
  - summarize_outcome: concise_lesson
  - infer_tags: ["decision"|"pattern"|"error"|...]
  - call_tool: memory_store(text="${concise_lesson}", tags="${infer_tags}", source="auto-hook")
```

### 3) Handle Recurring Problems

**What it is**

Tracking operational failures to detect repeat patterns.

**Why we do it**

Recurring failures should become rules, not repeated toil.

**Manual flow**

Call this every time a meaningful failure occurs (build break, runtime error, flaky test, or repeated operational issue), especially if you think it may happen again.

1. Call `flag_problem(description, context)` on failure.
2. Check if a proposal was generated after recurrence threshold.
3. Review proposal before promotion.

**Automation workaround**

```text
onErrorClassified:
  - collect_error_context: message, command, file
  - call_tool: flag_problem(description="${message}", context="${context_blob}")
  - notify_if: proposal_generated
```

### 4) Evolve Team Guardrails

**What it is**

Converting lessons into explicit, reviewable rules.

**Why we do it**

Prevents regressions and keeps behavior consistent across sessions.

**Manual flow**

1. Draft with `propose_rule`.
2. Review `rules/proposals/`.
3. Promote with `promote_rule(filename)` when validated.
4. Use `rollback_rule(changelog_id)` for regressions.

**Automation workaround**

```text
scheduledRulesReview:
  - list_proposals: rules/proposals/*.md
  - score_candidates: recency + recurrence_signal
  - prompt_user_review: top_candidates
  - user_confirmed -> call_tool: promote_rule(filename=...)
```

### Automation guardrails (for all journeys)

- Keep hooks idempotent (safe to run twice).
- Keep context/token usage bounded.
- Require explicit confirmation before destructive or irreversible actions.
- If hooks fail, fall back to manual steps above.

## Ceremonies and Rituals

### Daily Ritual

- Start with `session-start` + `memory_search`.
- Work normally.
- Call `flag_problem` on issues.
- Store useful outcomes with `memory_store` before ending.

### Weekly Ritual

- Review files in `rules/proposals/`.
- Promote useful rules and clean stale proposals.
- Skim `rules/CHANGELOG.md`.
- Roll back regressions with `rollback_rule`.
- Run `agent-mcp memory prune`.

## Add / Update / Remove Skills

Skills live under `skills/` and can be authored in two formats:

1. **Legacy single-file** (backward-compatible): `skills/<name>.md` or `skills/roles/<name>.md`
2. **Spec directory format** (recommended): `skills/<skill-name>/SKILL.md`

Directory format can include:

- `references/` for docs
- `scripts/` for runnable helpers
- `assets/` for templates/resources

Example:

```text
skills/
  pdf-processing/
    SKILL.md
    references/
      REFERENCE.md
    scripts/
      run.py
    assets/
      template.txt
```

### Add Skill (root file or subfolder file)

1. Create either a legacy file or a skill directory with `SKILL.md`.
2. Add YAML frontmatter:

```md
---
name: reviewer
description: Read-only review role
triggers: ["review", "audit"]
---
Skill instructions...
```

Optional spec fields are also supported in frontmatter:

```md
---
name: pdf-processing
description: Extract text and forms from PDFs.
license: Apache-2.0
compatibility: Requires Python and local file access
metadata:
  author: example-team
allowed-tools: Bash(git:*) Read
---
```

3. Verify with `list_skills` and `read_skill("<name>")`.
4. If using directory format, verify resources with:
   - `list_skill_files("<name>")`
   - `read_skill_file("<name>", "references/REFERENCE.md")`

### Update Skill

1. Edit frontmatter and body.
2. Keep `name` unique across all skills.
3. Re-check with `list_skills`.

### Remove Skill

1. Delete the skill file.
2. Run `list_skills` to confirm removal.

### Skill Constraints

- Only markdown skill documents are loaded.
- Frontmatter requires `name` and `description`.
- `name` constraints:
  - max 64 chars
  - lowercase letters/digits/hyphen only
  - no consecutive `--`
- For directory-format skills, `name` must match the parent directory name.
- `read_skill` resolves by frontmatter `name`, not file path.

## Add / Update / Remove Rules

### What rules are

Rules are **persistent guardrails**: short “when X, do Y” commitments for you and the agent.

- **Compared to skills**: skills are playbooks and procedures (often long). Rules are **narrow triggers + solutions** you want honored whenever that situation comes up.
- **Compared to memory**: memory is **searchable notes** (many tags, retrieved by query). Rules are **explicitly listed** via `list_rules` and live as small, reviewable files.

### How they are stored

- **Many files, not one blob**: each rule is **exactly one** Markdown file with YAML frontmatter (`rules/active/*.md` for live rules, `rules/proposals/*.md` for drafts).
- **`list_rules`** reads only **`rules/active/`** — every `*.md` there is a separate rule, keyed by frontmatter `id`.
- If you edit **`rules/active/`** Markdown by hand while `agent-mcp serve` is running, **`list_rules` can stay stale** until you **restart** the MCP server (tool-driven changes such as **`promote_rule`** and **`rollback_rule`** reload the active index when they modify files).
- **Lifecycle**: create a proposal (tool or hand-written) → review under `rules/proposals/` → **`promote_rule(filename)`** moves that file into `rules/active/` (same basename). Changes are audited for **`rollback_rule`** via `rules/CHANGELOG.md` and `rules/machine_changelog.jsonl`.

Example active rule file `rules/active/no-secrets-in-logs.md`:

```markdown
---
id: no-secrets-in-logs
version: "2026-05-02"
trigger: Logging, traces, or debug output might include API keys, tokens, or passwords
solution: Redact secrets; log placeholders only; rely on env vars or secret managers.
---

Optional longer context (commands, naming, pointers to scanners).
```

### Add Rule

- Preferred path: `propose_rule(trigger, solution, source_session_id)` — writes a new Markdown file under `rules/proposals/` (or directly to `rules/active/` in auto mode, subject to daily cap). The server fills frontmatter: unique `id` (ULID), `created` (date), plus your `trigger` and `solution`.
- **Manual authoring**: create a `.md` file yourself with the same frontmatter keys (`id`, `created`, `trigger`, `solution`) and a human-readable `id` if you prefer; place it in `rules/proposals/` or `rules/active/` as appropriate.

### Update Rule

- Edit **proposal** files in `rules/proposals/` before promotion.
- For **active** rules, prefer a **new** proposal that supersedes old guidance (or fix via promotion workflow you choose); avoid silent edits without the changelog story if you care about rollback.

### Remove Rule

- Prefer **`rollback_rule(changelog_id)`** so removal/revert stays auditable.
- Deleting `rules/active/<file>.md` by hand removes the rule from `list_rules` but **bypasses** the changelog story; use when you knowingly accept that tradeoff.

## Configuration

Main file: `config.toml`.

### Core Blocks

- `[mode]`
- `[paths]`
- `[memory]`
- `[problems]`
- `[rules]`

### Memory Hybrid Defaults

```python
VECTOR_WEIGHT = 0.7
LEXICAL_WEIGHT = 0.3
```

Optional in `[memory]`:

```toml
vector_weight = 0.7
lexical_weight = 0.3
relevance_floor = 0.5
```

Normalization:

- neither set -> use defaults
- one set -> derive the other to sum to `1.0`
- both set -> normalize to `1.0`

## Safety Model

- File-facing parameters are basename/id oriented.
- Paths resolve under fixed roots.
- `memory_store` writes under `memory/`.
- Cluster bookkeeping writes under `state/`.
- Auto mode is bounded by daily cap.

## Common Commands

- `agent-mcp init [path]`
- `agent-mcp models pull`
- `agent-mcp serve`
- `agent-mcp memory prune`
- `agent-mcp doctor`

## Troubleshooting

- **Embedding/model errors**: run `agent-mcp models pull`.
- **Server not visible in harness**: verify MCP config command and args.
- **Missing skills/rules**: verify `config.toml` paths and local layout.
- **Rule regression**: inspect `rules/CHANGELOG.md` and rollback by id.

## Scope Notes

v0.1 intentionally excludes sub-agent orchestration, automatic session hooks, and LLM-authored rule generation inside the server.
