# SkillMCP

Serves skills and behavioral rules (AGENT.md) to AI agents.

Works with Claude Code, Gemini CLI, Cursor, and Antigravity.

Prevents your project from looking like the [Cursed Repo](https://github.com/Hacksore/cursed-repo).

---

## What it does

Injects knowledge into every agent session via MCP:

| What | Source | How the agent gets it |
|---|---|---|
| **Behavioral rules** | `.agents/AGENT.md` | Auto-injected into MCP instructions every session |
| **Skills** | `.agents/skills/` (global + project-local) | Agent calls `list_skills` / `read_skill` on demand |

---

## Setup

```bash
# 1. Install (run once from the SkillMCP directory)
cd SkillMCP
uv sync

# 2. Initialise in your project (run once per project)
skills-mcp init .    # scaffold .agents/, register MCP with all hosts
skills-mcp doctor    # verify layout and registration
```

Restart your agent host once after `init` to pick up the MCP registration.

---

## MCP Tools

| Tool | Description |
|---|---|
| `verify_setup` | Health snapshot: paths, skill counts, issues |
| `list_skills([project_path])` | Global + local skill metadata |
| `read_skill(name[, project_path])` | Full Markdown for one skill; local wins over global |

### AGENT.md

`.agents/AGENT.md` is plain Markdown — no special syntax. Injected automatically into every session's MCP instructions. Edit it to define how agents should behave globally.

### Skills

Each skill is a folder under `.agents/skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`).

Project-local skills (in `<project>/.agents/skills/`) merge with global. Local wins on name collision.

---

## CLI

| Command | Description |
|---|---|
| `skills-mcp init [path]` | Scaffold `.agents/`, config.toml, register MCP with all hosts |
| `skills-mcp serve` | Run MCP server over stdio (started automatically by host agents) |
| `skills-mcp doctor` | Verify layout and MCP registration |
| `skills-mcp mcp register` | Re-register with Claude Code, Gemini, Cursor, Antigravity |

---

## Host Support

| Host | MCP registration |
|---|---|
| **Claude Code** | `~/.claude/settings.json` |
| **Gemini CLI** | `~/.gemini/settings.json` |
| **Cursor** | `~/.cursor/mcp.json` |
| **Antigravity** | `~/.antigravity/mcp.json` |

---

## Configuration (`config.toml`)

```toml
[paths]
skills = ".agents/skills"

# Optional: shared content folder with a skills/ subdirectory
# content = ".libraries"

# Optional: secondary skills repo (merged; project wins on collision)
# shared_skills = "path/to/shared"
```

---

## Key Files

| Path | Purpose |
|---|---|
| `.agents/AGENT.md` | Behavioral rules — injected every session |
| `.agents/skills/` | Global skill packages |
| `<project>/.agents/skills/` | Project-local skills |
| `config.toml` | Paths config |
| `CLAUDE.md` | Bootstrap instructions for Claude Code |
