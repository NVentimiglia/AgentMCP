from __future__ import annotations

import os

from skills_mcp.rules.loader import ActiveRuleIndex

_BASE = """**skills-mcp** is active. Follow these rituals every session.

## Session start
1. Call `read_project_doc(project_path=<absolute path of the project you are working in>)` to load project memory and context.
2. Call `list_skills` to see available skills; call `read_skill(name)` for any that apply to the current task.
3. Rules below are already active — no need to re-read them unless directed.

## During the session
- Call `read_skill` before implementing patterns the skill covers.
- After 2 consecutive tool failures, change strategy — do not retry the same action.

## Session end
- If a notable pattern, correction, or new insight emerged, suggest the user save the session to `sessions/YYYY-MM-DD-topic.md`.
- Call `write_project_doc` to persist any decisions, context, or open threads that should survive into the next session.
- Check `get_usage_counters` — if `learn_loop.sessions_pending` ≥ 3, remind the user to run the learn pass.

---

"""


def render_active_rules_markdown(idx: ActiveRuleIndex) -> str:
    """Concatenate ``rules/*.md`` bodies with metadata headers for MCP session seeding."""
    sections: list[str] = []
    for _, pr in idx.iter_sorted():
        fm = pr.fm
        body = pr.body.strip()
        block = (
            f"### Rule `{fm.id}`\n\n"
            f"- **trigger:** {fm.trigger}\n"
            f"- **solution:** {fm.solution}\n\n"
            f"{body}\n"
        )
        sections.append(block)
    if not sections:
        return (
            "(No valid `rules/*.md` rule files yet — each file needs YAML frontmatter with "
            "``id``, ``trigger``, ``solution``.)\n"
        )
    return "\n---\n\n".join(sections)


def render_mcp_seed_text(
    idx: ActiveRuleIndex,
    *,
    truncate_at: int | None = None,
) -> str:
    """Full MCP ``instructions`` string: preamble + concatenated rules.

    Project.md is NOT injected here — the server is shared across projects and
    instructions are static per startup.  Agents load project context by calling
    ``read_project_doc(project_path=<cwd>)`` at session start.
    """
    rules_block = render_active_rules_markdown(idx)
    seed = _BASE + "\n## Rules\n\n" + rules_block
    limit = truncate_at if truncate_at is not None else _max_chars_env()
    if limit is None or limit <= 0:
        return seed
    if len(seed) <= limit:
        return seed

    suffix = "\n\n...(truncated; set SKILLS_MCP_RULES_INSTRUCTIONS_MAX_CHARS=0 for no cap).\n"
    budget = limit - len(suffix)
    if budget < 1:
        return seed[:limit]
    truncated = seed[:budget].rstrip()
    return truncated + suffix


def _max_chars_env() -> int | None:
    raw = os.environ.get("SKILLS_MCP_RULES_INSTRUCTIONS_MAX_CHARS")
    if raw is None:
        raw = os.environ.get("AGENT_MCP_RULES_INSTRUCTIONS_MAX_CHARS")
    if raw is None:
        return None
    stripped = raw.strip()
    if not stripped or stripped == "0":
        return None
    try:
        return int(stripped, 10)
    except ValueError:
        return None
