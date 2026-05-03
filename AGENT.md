# AgentMCP / `agent-mcp` — agent reference (v0.1)

This document is the **maintainer contract** for the MCP tool surface.
Implementations must match [README.md](README.md).

## Global behavior

- **Transport**: stdio only (`agent-mcp serve`).
- **Project root**: `AGENT_MCP_ROOT` env, else first parent directory containing
  `config.toml`.
- **Secrets / PII**: structured session logs under `~/.agent-mcp/log/` **redact**
  `memory.text`-like fields.
- **Filesystem safety**: rule and skill file parameters are **basenames** only;
  paths and `..` are rejected.

## Machine-readable rules audit log

- Append-only JSON Lines: `rules/machine_changelog.jsonl` (alongside
  `rules/CHANGELOG.md`).
- `rollback_rule(changelog_id)` replays **inverse** of the selected entry’s
  `snapshot` (see implementation). It cannot target an entry with `op ==
  "ROLLBACK"`.

---

## `list_skills`

**Contract**: List skills under configured `paths.skills`.

**Inputs**: none.

**Outputs**: JSON array of `{ name, description, path }` (`path` is repo-
relative under `skills/`).

**Failures**: skills directory missing; loader scan error (invalid frontmatter,
duplicate `name`).

---

## `read_skill`

**Contract**: Return **full Markdown** for one skill (`---` YAML frontmatter +
body).

**Inputs**: `name` — skill identifier (must equal frontmatter `name`). No paths.

**Outputs**: Markdown string.

**Failures**: unknown name (`KeyError` surfaced to client); `name` containing
`/`, `\\`, or `..`.

---

## `memory_store`

**Contract**: Persist a memory row in Chroma + hybrid ranking fields.

**Inputs**:

- `text` (string, required)
- `tags` (string array, required) — each must be one of
  `problem | decision | pattern | preference | error | note`
- `source` (string, default `user`)

**Outputs**: JSON object: `id, text, tags, state, created_at, last_used_at, use_count, source`.

**Failures**: invalid/empty tags; embedding model unloadable (missing cache — run `agent-mcp models pull`).

---

## `memory_search`

**Contract**: Hybrid **vector + BM25** ranking over all memories; optional `relevance_floor` from config trims weak scores before truncation.

**Inputs**:

- `query` (string)
- `k` (integer, default 5)

**Outputs**: JSON array of hits: `{ score, id, text, tags, state, ... }`.

**Failures**: embedding errors; empty corpus returns `[]`.

**Notes**:

- Weight defaults: vector `0.7`, lexical `0.3`; optional config overrides normalized per README.
- If bulk embedding retrieval is unavailable, embeddings are recomputed from stored document text.

---

## `memory_reinforce`

**Contract**: Bump reinforcement metadata for ids.

**Inputs**: `ids` (string array of memory ids).

**Outputs**: `{ "ok": true, "ids": [...] }`.

**Failures**: unknown id.

**State**: `new` → `reinforced`; **`reinforced` entries are never auto-pruned.**

---

## `list_rules`

**Contract**: Snapshot of `rules/active/*.md` (loaded at startup / reload).

**Inputs**: none.

**Outputs**: JSON `[{ id, trigger }, ...]`.

**Failures**: malformed active rule files (parse errors on reload paths).

---

## `propose_rule`

**Contract**: Persist a proposed rule Markdown file under `rules/proposals/` or promote into `rules/active/` in **auto** mode.

**Inputs**:

- `trigger` (string)
- `solution` (string)
- `source_session_id` (string)

**Outputs** (representative):

- Proposal mode: `{ "mode": "proposal", "path": "rules/proposals/<file>.md", "changelog_id": "<id>" }`
- Auto mode: `{ "mode": "auto", "path": "rules/active/<file>.md", "changelog_id": "<id>" }`
- Daily cap spill (auto mode): `{ "mode": "proposal", ... , "reason": "daily_cap" }`

**Failures**: YAML/write errors.

---

## `promote_rule`

**Contract**: Move `rules/proposals/<basename>` → `rules/active/<basename>` and record changelog.

**Inputs**: `filename` — **basename**, must end with `.md`.

**Outputs**: `{ "changelog_id": "<id>" }`.

**Failures**: missing proposals file; path injection.

---

## `rollback_rule`

**Contract**: Restore filesystem state preceding a forward changelog entry.

**Inputs**: `changelog_id` — string id; must not contain path separators.

**Outputs**: `{ "rollback_id": "<new id>" }`.

**Failures**: unknown id; attempts to rollback a rollback entry.

---

## `flag_problem`

**Contract**:

1. Store `memory_store(..., tags=["problem"])`.
2. Rank prior `problem`-tag memories vs the composite query using hybrid similarity and `similarity_threshold` (exclusive of the new row id).
3. Merge/update recurrence clusters in `state/clusters.json`.
4. If `len(cluster.member_ids) >= recurrence_count` and the cluster **is not yet** `proposed`, call `propose_rule` logic automatically.

**Inputs**:

- `description` (string)
- `context` (string)
- `source_session_id` (string, default `anonymous`)

**Outputs**: JSON with `memory`, `cluster`, `recurrence_hit`, `proposal` (dict; may be empty).

**Failures**: propagate memory / rules failures.

---

## `get_metrics`

**Contract**: Return a JSON snapshot of aggregate usage counters persisted at `state/metrics.json`.

**Inputs**: none.

**Outputs**: JSON object with keys `version`, `updated_at`, `tools` (map of tool name → call count), `skills` (map of skill name → touch count for `read_skill` / `list_skill_files` / `read_skill_file` only), `memory` (`stores`, `searches`, `reinforces`, `context_chars_stored`), `rules` (`list`, `propose`, `promote`, `rollback`), `problems` (`flagged`). Invoking `get_metrics` increments both `tools.get_metrics` and the returned snapshot for that invocation.

**Failures**: none typical (state dir created on demand).

---

## CLI commands (non-MCP)

| Command | Purpose |
|---------|---------|
| `agent-mcp init [path]` | Lay out dirs + copy bundled starter files |
| `agent-mcp models pull` | Prime `fastembed` cache under `~/.agent-mcp/models` |
| `agent-mcp serve` | Start MCP stdio server |
| `agent-mcp memory prune` | CLI prune (30-day `new`-only policy) |
| `agent-mcp doctor` | Config/layout checks |

---

## Release checklist (v0.1.0)

1. `python -m pip install -e ".[dev]"` then `pytest -q`.
2. `agent-mcp models pull` once per machine embedding cache.
3. `git tag v0.1.0` when satisfied (manual).
