# SkillMCP

Serves project-specific skills and behavioral rules to AI agents via MCP.

Works with Claude Code, Gemini CLI, Cursor, and Antigravity.

Pairs well with [LearnSkill](https://github.com/NVentimiglia/LearnSkill) (behavioral auditing) and [claude-mem](https://github.com/thedotmack/claude-mem) (long-term memory).

---

## Quick Start

```bash
cd /path/to/project
skills-mcp init .    # scaffold .agents/ skills and rules
```

Restart your agent host to pick up the new skills.

---

## How it works

Injects knowledge into every agent session automatically via the MCP instruction block.

### AGENT.md — behavioral rules

Markdown files injected into the system prompt at session start. All sources are combined; none are dropped.

| Source | Location |
|---|---|
| Bundled (SkillMCP install) | `<skillmcp>/.agents/AGENT.md` |
| Configured agent folders | `AGENT.md` in each `agent_folders` entry |

### Skills — on-demand knowledge

Markdown skill files the agent fetches with `list_skills` / `read_skill` as needed. Later entries in `agent_folders` win on name collision.

| Source | Location |
|---|---|
| Bundled (SkillMCP install) | `<skillmcp>/.agents/skills/` |
| Configured agent folders | `skills/` subdir of each `agent_folders` entry |

---

## Setup

1. **Install**
   ```bash
   cd SkillMCP && uv sync
   ```

2. **Initialize**
   ```bash
   skills-mcp init .
   ```

3. **Configure**
   Edit `skillmcp.toml` to add agent folders. Last entry wins on collision.

   ```toml
   agent_folders = [
       "/path/to/shared/agents",
       ".agents/",
   ]
   ```

   Each agent folder can contain:
   - `AGENT.md` — behavioral rules injected into every session (all folders combined)
   - `skills/` — skill library scanned for `list_skills` / `read_skill`

---

## CLI Reference

| Command | Description |
|---|---|
| `init [path]` | Scaffold `.agents/`, `skillmcp.toml`, `AGENT.md`, register MCP |
| `doctor` | Verify directory layout and MCP registration |
| `mcp register` | Re-register with all agent hosts (Claude, Gemini, etc.) |

---

## Troubleshooting

- **Stale Paths**: If you move your project, run `skills-mcp mcp register` from the new location to update absolute paths in the MCP configs.
- **Missing Skills**: Run `skills-mcp doctor` to see exactly which `skillmcp.toml` is being discovered and how many skills were found.
