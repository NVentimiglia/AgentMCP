# SkillsMCP

One source of truth for agent skills, guardrail rules, and behavioral learning — served to every agent via MCP. Skills compound over time. Anti-patterns self-correct. Git is the audit layer.

---

## How It Works

```
skills/*.md ──┐
rules/*.md ───┼──► MCP server ──► Claude Code / Cursor / Gemini CLI / any MCP agent
instructions ─┘

sessions/*.md ──► learn pass (manual) ──► skills/*.md
agent turns   ──► analyze   (auto)    ──► rules/dr-*.md
```

**Skills** are reusable Markdown docs served to agents on demand.
**Rules** are guardrail instructions injected into every MCP session automatically.
**Sessions** are raw conversation logs distilled periodically into skills.
**Analyze** reads transcripts from Claude Code, Cursor, and Gemini CLI, detects behavioral anti-patterns, and writes them back as rules — no human required.

---

## Loops

### Loop 1 — Skill Learning (manual)

```
work with agents
  → save conversation to sessions/YYYY-MM-DD-topic.md
  → 3+ sessions ready?
      → run learn pass in Claude Code: "run the learn pass"
      → git diff skills/
      → commit keepers, revert noise
  → restart skills-mcp serve to pick up new skills
```

Cadence: whenever `sessions_pending` reaches 3+. Check with `get_usage_counters`.
The learn pass reads `skills/index.md`, updates existing skills, creates new ones, and promotes stubs from `skills/_candidates.md`.

### Loop 2 — Behavioral Analysis (automatic)

```
agent turn ends
  → hook fires: skills-mcp analyze
      → lock held or cooldown active? → skip silently
      → scan transcripts: Claude ~/.claude/projects/
                          Gemini ~/.gemini-docter/transcripts/
                          Cursor workspaceStorage/**/*.vscdb
      → detect signals (correction-heavy, error-loop, edit-thrashing, …)
      → write/update rules/dr-*.md (version increments each run)
      → git diff rules/
      → stamp + release lock
  → git add rules/ && git commit when diff looks right
```

Cadence: automatic after every agent turn. Protected by PID lock + 60-minute cooldown.

### Loop 3 — Serve (always on)

```
skills-mcp serve
  → agent connects via MCP
  → rules/*.md injected as session instructions
  → list_skills / read_skill served on demand
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

### End of a useful session

Save the raw conversation to:

```
sessions/2026-05-14-auth-refactor.md
```

No format required. The learn pass handles extraction.

### Weekly: run the learn pass

When `sessions_pending` hits 3+:

1. Open Claude Code → **"run the learn pass"** (or paste `LEARN.md`)
2. `git diff skills/` — review every change
3. Commit what's right, revert what isn't

Check status anytime:

```
get_usage_counters → learn_loop.sessions_pending: 4
                   → learn_loop.last_learn_pass:  2026-05-10T14:23:00Z
```

### Audit behavioral rules

Rules update in the background after each turn. Review when ready:

```bash
git diff rules/
git add rules/ && git commit -m "chore: update behavioral rules"
```

---

## Agent Integrations

`skills-mcp analyze` reads transcripts from all available providers on every run.

| Agent | Transcript source | Hook setup |
| --- | --- | --- |
| **Claude Code** | `~/.claude/projects/*.jsonl` (written automatically) | `skills-mcp hooks install` → Stop hook in `.claude/settings.local.json` |
| **Cursor** | `workspaceStorage/**/*.vscdb` (SQLite, read directly) | None — works automatically |
| **Gemini CLI** | `~/.gemini-docter/transcripts/*.jsonl` (captured by hook) | `skills-mcp hooks install --provider gemini` → `afterEachTurn` in `~/.gemini/settings.json` |
| Antigravity | — | Not yet supported |

All active providers are scanned on every analyze run. Missing or empty sources are silently skipped.

---

## Behavioral Signals

Signal detectors are vendored from [gemini-docter](https://github.com/NVentimiglia/gemini-docter). Each detected signal writes or updates a `rules/dr-<signal>.md` file.

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

Rule files include signal name, severity, occurrence count, examples, and sessions analyzed. Version increments on each run.

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
  "by_tool": { "list_skills": 12, "read_skill": 34, "verify_setup": 1, ... },
  "total": 47,
  "learn_loop": {
    "skills_count": 18,
    "sessions_total": 7,
    "sessions_pending": 3,
    "last_learn_pass": "2026-05-10T14:23:00Z"
  }
}
```

Call counts are also persisted to `usage_counters.json`. Each tool call writes a markdown blob to `logs/`. Both are gitignored.

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
| `skills-mcp analyze` | Scan transcripts, detect signals, write `rules/dr-*.md` |
| `skills-mcp hooks install` | Install Claude Code Stop hook |
| `skills-mcp hooks install --provider gemini` | Install Gemini CLI capture + trigger hooks |

## MCP Tools

| Tool | Returns |
| --- | --- |
| `verify_setup` | Paths, skill/rule counts, issues |
| `list_skills` | Skill metadata (name, description, path) |
| `read_skill(name)` | Full Markdown for one skill |
| `list_rules` | Rule metadata (id, trigger, file) |
| `read_rules(id)` | Full Markdown for one rule |
| `get_usage_counters` | Per-tool call counts + learn-loop status |

## Configuration (`config.toml`)

```toml
[paths]
skills  = "skills"
rules   = "rules"

# Shared content folder — a directory with skills/ and rules/ subdirectories.
# Both are merged with the project; project always wins on name/id collision.
# Supports absolute paths or paths relative to this config file.
# content = ".libraries"

# Legacy: shared skills only (use content = ... to share both skills and rules).
# shared_skills = ".libraries/skills"
```

### Shared content folder

Set `content` to any directory that contains `skills/` and/or `rules/` subdirectories:

```
.libraries/
  skills/
    my-shared-skill.md
  rules/
    my-shared-rule.md
```

```toml
[paths]
content = ".libraries"          # relative to config.toml
# content = "D:/SharedContent" # or absolute
```

- Both `skills/` and `rules/` subdirs are optional — missing ones are silently skipped.
- Project files always win: a project `rules/foo.md` with `id: foo` shadows `.libraries/rules/foo.md`.
- `shared_skills` still works for skills-only sharing; `content` is preferred when sharing both.
- `doctor` warns if `content` is set but the directory or its subdirs are missing.

## Key Files

| Path | Purpose |
| --- | --- |
| `CLAUDE.md` | Auto-loaded by Claude Code at session start |
| `AGENT.md` | Bootstrap for Gemini, Cursor, and other agents |
| `LEARN.md` | Learn pass prompt — paste into any agent to distill sessions |
| `config.toml` | Project paths |
| `skills/index.md` | Skill catalog; updated by learn pass |
| `skills/_candidates.md` | Emerging patterns awaiting promotion |
| `sessions/log.md` | Append-only learn pass history |
| `rules/dr-*.md` | Auto-generated behavioral guardrails |
| `usage_counters.json` | Per-tool MCP call counts (runtime, gitignored) |
| `logs/` | Per-call markdown blobs (runtime, gitignored) |
| `state/analyze.lock` | PID lock for running analyze (gitignored) |
| `state/analyze.stamp` | Timestamp of last analyze run (gitignored) |
| `.claude/settings.local.json` | Claude Code hook config (gitignored) |
| `~/.gemini/settings.json` | Gemini CLI hook config (global, managed by hooks install) |
| `src/skills_mcp/dr/` | Vendored gemini-docter signal detectors |
| `src/skills_mcp/dr_hooks/` | Gemini CLI transcript capture scripts |
