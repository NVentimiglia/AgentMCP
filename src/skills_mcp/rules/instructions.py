from __future__ import annotations

import os

_BASE = """**skills-mcp** is active. Follow these rituals every session.

## Session start
1. Call `list_skills` — check for applicable global and project-local skills.
2. Call `read_skill(name)` for any skill that applies to the current task.
3. AGENT.md rules below are already active.

## During the session
- Call `read_skill` before implementing patterns a skill covers.
- After 2 consecutive tool failures, change strategy — do not retry the same action.

---

"""


def render_mcp_seed_text(
    *,
    agent_md_content: str | None = None,
    truncate_at: int | None = None,
) -> str:
    """Full MCP ``instructions`` string: preamble + AGENT.md content.

    If ``agent_md_content`` is provided (from ``.agents/AGENT.md``), it is appended
    after the preamble.  Otherwise only the preamble is returned.
    """
    if agent_md_content is not None:
        seed = _BASE + "\n## Rules\n\n" + agent_md_content
    else:
        seed = _BASE
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
