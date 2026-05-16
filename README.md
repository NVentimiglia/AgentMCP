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

Restart your agent host to pick up the new skills and rules.

---

## How it works

Injects knowledge into every agent session automatically via the MCP instruction block.

| Feature | Source | Interaction |
|---|---|---|
| **Behavioral Rules** | `.agents/AGENT.md` | Injected into the system prompt automatically |
| **Skill Library** | `.agents/skills/` | Agent calls `list_skills` / `read_skill` as needed |
| **Project Overrides** | `skillmcp.toml` | Local skills override global on name collision |

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
   Edit `skillmcp.toml` to add external skill folders. Last entry wins on collision.

   ```toml
   skill_folders = [
       "/path/to/shared/skills", 
       ".agents/skills",
   ]
   ```

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
