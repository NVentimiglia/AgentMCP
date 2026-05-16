# SkillsMCP Manual Smoke Test

Run this after `python tests/integration_runner.py` passes.
Purpose: confirm a **live agent session** loads and uses the MCP server correctly.

---

## Prerequisites

```bash
skills-mcp init <your-project-path>
skills-mcp doctor
```

Both should exit clean. If not, fix before proceeding.

---

## Step 1 — Confirm MCP server loaded

Open a new session in your agent (Claude Code, Cursor, Gemini, Copilot).

Ask:
> "What MCP servers do you have available? List their tools."

**Pass:** Agent lists `skills-mcp` and its tools: `verify_setup`, `list_skills`, `read_skill`.

**Fail:** Agent says no MCP servers, or the tool names are missing. Re-run `skills-mcp mcp register` and restart the agent host.

---

## Step 2 — AGENT.md is injected

Ask:
> "What instructions were you given at the start of this session?"

**Pass:** Agent mentions content from `.agents/AGENT.md` in the project (or the global one if the project has none). It does **not** have to quote it verbatim — any paraphrase of the headings is fine.

**Fail:** Agent says it has no special instructions, or the AGENT.md content is absent.

---

## Step 3 — list_skills

Ask:
> "Call `list_skills` for this project and tell me what skills are available."

**Pass:** Agent calls the tool and returns a list. Global skills always present. Local project skills appear if `.agents/skills/` has any.

**Fail:** Tool call errors, or returns empty when global skills are installed.

---

## Step 4 — read_skill

Pick any skill name from Step 3. Ask:
> "Read the skill named `<name>` and summarize it."

**Pass:** Agent calls `read_skill`, gets Markdown back, summarizes it.

**Fail:** Tool returns an error or empty content.

---

## Step 5 — Skill merge (local overrides global)

Only needed if you have a local skill with the same name as a global one.

Ask:
> "Call `list_skills` with `project_path=<your-project>`. Which version of `<skill-name>` do you get — local or global?"

**Pass:** Agent returns the local copy (local wins on collision).

---

## Done

All five steps passing confirms the live agent can discover and consume skills correctly.
