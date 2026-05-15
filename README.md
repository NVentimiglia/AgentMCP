# SkillsMCP

One source of truth for agent skills, guardrail rules, and behavioral learning — served to every agent via MCP. Skills compound over time. Anti-patterns self-correct. Git is the audit layer.

---

## How It Works

```
AgentMCP/
  skills/*.md  ──► global packages — loaded on demand via list_skills / read_skill
  rules/*.md   ──► global personality — injected into every session automatically

MyApp/  (any project using this MCP server)
  .memory/*.md ──► project-local learnings — loaded on demand via list_memory / read_memory
                   written by analyze (dr-*.md) and by the agent (decisions, context, …)
```

**Skills** are global reusable patterns served on demand.
**Rules** are global guardrails injected automatically into every session.
**Memories** are project-local learnings: behavioral signals from analyze, decisions, open threads — loaded like skills but scoped to the project.

```
agent turns   ──► analyze (auto)    ──► MyApp/.memory/dr-*.md
.sessions/*.md ──► learn pass (manual) ──► skills/*.md  (or .memory/*.md)
```

---

## Three Tiers

| Tier | Location | Scope | Written by |
| --- | --- | --- | --- |
| **Rules** | `AgentMCP/rules/*.md` | Global — every session | Human (hand-authored guardrails) |
| **Skills** | `AgentMCP/skills/*.md` | Global — loaded on demand | Human + learn pass |
| **Memories** | `<project>/.memory/*.md` | Project-local — loaded on demand | Agent + analyze |

---

## Loops

### Loop 1 — Skill Learning (manual)

```
work with agents
  → save conversation to .sessions/YYYY-MM-DD-topic.md
  → 3+ sessions ready?
      → run learn pass: "run the learn pass"
      → git diff skills/
      → commit keepers, revert noise
  → restart skills-mcp serve to pick up new skills
```

Cadence: whenever `sessions_pending` reaches 3+. Check with `get_usage_counters`.

### Loop 2 — Behavioral Analysis (automatic)

```
agent turn ends
  → hook fires: skills-mcp analyze
      → lock held or cooldown active? → skip silently
      → detect CWD — is it a different project than AgentMCP?
      → scan transcripts: Claude ~/.claude/projects/
                          Gemini ~/.gemini-docter/transcripts/
                          Cursor workspaceStorage/**/*.vscdb
      → detect signals (correction-heavy, error-loop, edit-thrashing, …)
      → write/update <project>/.memory/dr-*.md
      → git diff .memory/
      → stamp + release lock
```

Cadence: automatic after every agent turn. Protected by PID lock + 60-minute cooldown.

### Loop 3 — Serve (always on)

```
skills-mcp serve
  → agent connects via MCP
  → rules/*.md injected as session instructions
  → instructions include session rituals (load memory, use skills, save at end)
  → list_skills / read_skill served on demand (global)
  → list_memory / read_memory / write_memory served on demand (project-local)
  → get_usage_counters reports metrics + learn-loop status
```

---

## Rituals

### First-time setup

```bash
pip install -e ".[dev,dr]"
skills-mcp init .
skills-mcp hooks install                        # Claude Code
skills-mcp hooks install --provider gemini      # Gemini CLI (optional)
# Cursor: no hook needed — reads SQLite DB automatically
skills-mcp doctor
skills-mcp serve
```

### Session start (agent does this automatically)

MCP `instructions` tell the agent to:

1. `list_memory(project_path=<cwd>)` — load project-local learnings
2. `list_skills` — check for applicable global skills
3. Apply active rules (already injected)

### Session end (agent prompts you)

At the end of a session with a notable pattern, correction, or decision:

1. Agent calls `write_memory(name, content, project_path)` — saves to `.memory/`
2. Save conversation → `.sessions/YYYY-MM-DD-topic.md` if worth a learn pass
3. If `sessions_pending` ≥ 3 → run the learn pass

### Learn pass (manual, when sessions_pending ≥ 3)

1. `skills-mcp sessions import` — pull JSONL transcripts into `.sessions/`
2. Open Claude Code → **"run the learn pass"** (or paste `LEARN.md`)
2. `git diff skills/` — review every change
3. Commit what's right, revert what isn't

```
get_usage_counters → learn_loop.sessions_pending: 4
                   → learn_loop.last_learn_pass:  2026-05-10T14:23:00Z
```

### Behavioral memory (automatic, review periodically)

Memory files update in the background after each turn. Review when ready:

```bash
git diff .memory/
git add .memory/ && git commit -m "chore: update project memory"
```

---

## Agent Integrations

| Agent | Transcript source | Hook setup |
| --- | --- | --- |
| **Claude Code** | `~/.claude/projects/*.jsonl` (written automatically) | `skills-mcp hooks install` → Stop hook in `.claude/settings.local.json` |
| **Cursor** | `workspaceStorage/**/*.vscdb` (SQLite, read directly) | None — works automatically |
| **Gemini CLI** | `~/.gemini-docter/transcripts/*.jsonl` (captured locally by hook) | `skills-mcp hooks install --provider gemini` → `afterEachTurn` in `~/.gemini/settings.json` |

All active providers are scanned on every analyze run. Missing or empty sources are silently skipped.

---

## Behavioral Signals

Signal detectors are vendored from [gemini-docter](https://github.com/NVentimiglia/gemini-docter). Each detected signal writes or updates a `.memory/dr-<signal>.md` file in the calling project.

| Signal | Fires when |
| --- | --- |
| `correction-heavy` | >20% of user messages are corrections |
| `keep-going-loop` | "keep going" prompts appear 2+ times |
| `repeated-instructions` | Similar instructions repeated (Jaccard ≥60%) |
| `negative-drift` | Messages shrink and grow more corrective over time |
| `rapid-corrections` | User follows up within 10 seconds of a response |
| `high-turn-ratio` | User/assistant turn ratio >1.5 |
| `error-loop` | 3+ consecutive tool failures |
| `edit-thrashing` | Same file edited 5+ times |
| `negative-sentiment` | Persistent negative sentiment (VADER) |

Memory files include signal name, severity, occurrence count, examples, and sessions analyzed. Version increments on each run.

---

## Lock and Cooldown

The Stop hook fires on every agent turn. The lock prevents pile-up:

| Condition | Behavior |
| --- | --- |
| Another analyze process is running | Skip — PID lockfile held |
| Last run < 60 minutes ago | Skip — cooldown stamp |
| Lockfile exists but process is dead | Take over and run |
| Otherwise | Acquire, run, stamp, release |

State files live in `state/` (gitignored).

---

## Metrics

`get_usage_counters` (MCP tool) returns per-tool call counts and learn-loop status:

```json
{
  "by_tool": { "list_skills": 12, "read_skill": 34, "list_memory": 8, "read_memory": 5, "write_memory": 3, ... },
  "total": 54,
  "learn_loop": {
    "skills_count": 18,
    "sessions_total": 7,
    "sessions_pending": 3,
    "last_learn_pass": "2026-05-10T14:23:00Z"
  }
}
```

---

## Install

```bash
pip install -e ".[dev,dr]"
# dev  = pytest
# dr   = vaderSentiment (required for negative-sentiment signal)

skills-mcp init .
skills-mcp hooks install
skills-mcp doctor
skills-mcp serve
```

## CLI

| Command | Description |
| --- | --- |
| `skills-mcp init [path]` | Scaffold `skills/`, `rules/`, `state/`, `config.toml` |
| `skills-mcp serve` | Run MCP server over stdio |
| `skills-mcp doctor` | Verify layout, config, Cursor MCP entry, and hooks |
| `skills-mcp analyze` | Scan transcripts, detect signals, write `<project>/.memory/dr-*.md` |
| `skills-mcp hooks install` | Install Claude Code Stop hook |
| `skills-mcp hooks install --provider gemini` | Install Gemini CLI capture + trigger hooks |
| `skills-mcp sessions import [--project-path PATH]` | Import JSONL transcripts from `~/.claude/projects/` into `.sessions/` |

## MCP Tools

| Tool | Returns |
| --- | --- |
| `verify_setup` | Paths, skill/rule counts, issues |
| `list_skills` | Global skill metadata (name, description, path) |
| `read_skill(name)` | Full Markdown for one global skill |
| `list_rules` | Global rule metadata (id, trigger, file) |
| `read_rules(id)` | Full Markdown for one global rule |
| `list_memory(project_path)` | Memory file names in `<project>/.memory/` |
| `read_memory(name, project_path)` | Contents of one memory file |
| `write_memory(name, content, project_path)` | Write a memory file to `<project>/.memory/` |
| `get_usage_counters` | Per-tool call counts + learn-loop status |

---

## Configuration (`config.toml`)

```toml
[paths]
skills  = "skills"
rules   = "rules"

# Shared content folder — a directory with skills/ and rules/ subdirectories.
# Both are merged with the project; project always wins on name/id collision.
# content = ".libraries"

# Legacy: shared skills only.
# shared_skills = ".libraries/skills"
```

### Shared content folder

Set `content` to any directory containing `skills/` and/or `rules/` subdirectories:

```toml
[paths]
content = ".libraries"
```

- Project files always win on name/id collision.
- `doctor` warns if `content` is set but the directory or its subdirs are missing.

## Key Files

| Path | Purpose |
| --- | --- |
| `AGENT.md` | Bootstrap instructions auto-loaded by Cursor, Gemini, and other agents |
| `CLAUDE.md` | Bootstrap instructions auto-loaded by Claude Code |
| `LEARN.md` | Learn pass prompt — paste into any agent to distill sessions into skills |
| `config.toml` | Project paths |
| `skills/index.md` | Skill catalog; updated by learn pass |
| `skills/_candidates.md` | Emerging patterns awaiting promotion |
| `.sessions/log.md` | Append-only learn pass history |
| `<project>/.memory/dr-*.md` | Auto-generated behavioral memory (per project) |
| `<project>/.memory/*.md` | Agent-written decisions, context, open threads (per project) |
| `state/usage_counters.json` | Per-tool MCP call counts (runtime, gitignored) |
| `state/logs/` | Per-call markdown blobs (runtime, gitignored) |
| `state/analyze.lock` | PID lock for running analyze (gitignored) |
| `state/analyze.stamp` | Timestamp of last analyze run (gitignored) |
| `.claude/settings.local.json` | Claude Code hook config (gitignored) |
| `~/.gemini/settings.json` | Gemini CLI hook config (global, managed by hooks install) |
| `src/skills_mcp/dr/` | Vendored gemini-docter signal detectors |
| `src/skills_mcp/dr_hooks/` | Gemini CLI transcript capture scripts |
