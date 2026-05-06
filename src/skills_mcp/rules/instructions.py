from __future__ import annotations

import os

from skills_mcp.rules.loader import ActiveRuleIndex

_BASE = """**skills-mcp** — obey `rules/*.md` below; use `list_skills` → `read_skill` when a skill fits, `list_rules` → `read_rules` when you need one rule file by id (MCP `instructions` already seeds all rules when the host passes them through).

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


def render_mcp_seed_text(idx: ActiveRuleIndex, *, truncate_at: int | None = None) -> str:
    """Full MCP ``instructions`` string: preamble + concatenated rules."""
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
