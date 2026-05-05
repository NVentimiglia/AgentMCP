from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from agent_mcp.app_state import AppContext, init_app, reset_app
from agent_mcp.memory.store import MemoryStore, validate_tags
from agent_mcp.metrics import MetricsStore
from agent_mcp.paths import project_root_from_env_or_discover
from agent_mcp.problems import handle_flag_problem
from agent_mcp.rules.loader import ActiveRuleIndex
from agent_mcp.rules.service import RulesService
from agent_mcp.session_logging import init_session_logging, log_tool_event
from agent_mcp.skills.loader import SkillIndex

mcp = FastMCP("agent-mcp")

_MEMORY: MemoryStore | None = None
_SKILLS: SkillIndex | None = None
_RULE_INDEX: ActiveRuleIndex | None = None
_RULES: RulesService | None = None
_APP: AppContext | None = None
_METRICS: MetricsStore | None = None


def configure_for_tests(root: Path) -> AppContext:
    """Initialize server globals (used by tests)."""
    return configure(root=root)


def configure(root: Path | None = None) -> AppContext:
    global _MEMORY, _SKILLS, _RULE_INDEX, _RULES, _APP, _METRICS
    if root is None:
        root = project_root_from_env_or_discover()
    _APP = init_app(root)

    _SKILLS = SkillIndex(_APP.skills_dir)
    _SKILLS.scan()

    _RULE_INDEX = ActiveRuleIndex(_APP.rules_active_dir)
    _RULE_INDEX.reload()

    _RULES = RulesService(_APP, active_index=_RULE_INDEX)
    _MEMORY = MemoryStore.from_app(_APP)
    _METRICS = MetricsStore(_APP.metrics_path)
    return _APP


def reset_runtime() -> None:
    global _MEMORY, _SKILLS, _RULE_INDEX, _RULES, _APP, _METRICS
    _MEMORY = None
    _SKILLS = None
    _RULE_INDEX = None
    _RULES = None
    _APP = None
    _METRICS = None
    reset_app()


def _require_runtime() -> tuple[MemoryStore, SkillIndex, ActiveRuleIndex, RulesService, AppContext]:
    if _MEMORY is None or _SKILLS is None or _RULE_INDEX is None or _RULES is None or _APP is None or _METRICS is None:
        configure()
    assert _MEMORY is not None
    assert _SKILLS is not None
    assert _RULE_INDEX is not None
    assert _RULES is not None
    assert _APP is not None
    assert _METRICS is not None
    return _MEMORY, _SKILLS, _RULE_INDEX, _RULES, _APP


def _metrics_record(
    tool: str,
    *,
    skill_name: str | None = None,
    memory_text_len: int | None = None,
) -> None:
    global _METRICS
    if _METRICS is None:
        return
    _METRICS.record(tool=tool, skill_name=skill_name, memory_text_len=memory_text_len)


@mcp.tool()
def list_skills() -> str:
    """Return JSON list for all skills (name, description, path, format, resource dirs)."""
    log_tool_event("list_skills", {})
    _, skills, _, _, _ = _require_runtime()
    _metrics_record("list_skills")
    out = list(skills.list_skills_meta())
    return json.dumps(out)


@mcp.tool()
def read_skill(name: str) -> str:
    """Return the full Markdown for a skill (including frontmatter) by basename skill name."""
    log_tool_event("read_skill", {"name": name})
    _, skills, _, _, _ = _require_runtime()
    _metrics_record("read_skill", skill_name=name)
    sk = skills.get_by_name(name)
    text = sk.parsed.full_markdown()
    return text


@mcp.tool()
def list_skill_files(name: str, folder: str | None = None) -> str:
    """List files inside a skill root, optionally filtered to references/scripts/assets."""
    log_tool_event("list_skill_files", {"name": name, "folder": folder})
    _, skills, _, _, _ = _require_runtime()
    _metrics_record("list_skill_files", skill_name=name)
    files = skills.list_skill_files(name, folder)
    return json.dumps(files)


@mcp.tool()
def read_skill_file(name: str, relative_path: str) -> str:
    """Read a text file from within a skill root (path traversal is rejected)."""
    log_tool_event("read_skill_file", {"name": name, "relative_path": relative_path})
    _, skills, _, _, _ = _require_runtime()
    _metrics_record("read_skill_file", skill_name=name)
    return skills.read_skill_file(name, relative_path)


@mcp.tool()
def memory_store(text: str, tags: list[str], source: str = "user") -> str:
    """Persist a memory entry (validated tags)."""
    log_tool_event("memory_store", {"text": text, "tags": tags, "source": source})
    mem, _, _, _, _ = _require_runtime()
    _metrics_record("memory_store", memory_text_len=len(text))
    tags = validate_tags(tags)
    row = mem.add_entry(text=text, tags=tags, source=source)
    return json.dumps(row)


@mcp.tool()
def memory_search(query: str, k: int = 5) -> str:
    """Hybrid lexical+vector memory search."""
    log_tool_event("memory_search", {"query": query, "k": k})
    mem, _, _, _, _ = _require_runtime()
    _metrics_record("memory_search")
    ranked = mem.hybrid_search(query, int(k))
    out = [{"score": float(sc), **row} for sc, row in ranked]
    return json.dumps(out)


@mcp.tool()
def memory_reinforce(ids: list[str]) -> str:
    """Reinforce one or more memory ids."""
    log_tool_event("memory_reinforce", {"ids": ids})
    mem, _, _, _, _ = _require_runtime()
    _metrics_record("memory_reinforce")
    mem.reinforce(list(ids))
    return json.dumps({"ok": True, "ids": ids})


@mcp.tool()
def list_rules() -> str:
    """JSON list[{id, trigger}] for rules/active."""
    log_tool_event("list_rules", {})
    _, _, idx, _, _ = _require_runtime()
    _metrics_record("list_rules")
    return json.dumps(idx.list_ids_triggers())


@mcp.tool()
def propose_rule(trigger: str, solution: str, source_session_id: str) -> str:
    """Create a proposal (default) or auto-add with changelog (auto mode)."""
    log_tool_event("propose_rule", {"trigger": trigger, "solution": solution, "source_session_id": source_session_id})
    _, _, _, rules, _ = _require_runtime()
    _metrics_record("propose_rule")
    out = rules.propose_rule_md(trigger=trigger, solution=solution, source_session_id=source_session_id)
    return json.dumps(out)


@mcp.tool()
def promote_rule(filename: str) -> str:
    """Promote rules/proposals/<filename> → rules/active/<filename>."""
    log_tool_event("promote_rule", {"filename": filename})
    _, _, _, rules, _ = _require_runtime()
    _metrics_record("promote_rule")
    out = rules.promote_rule(filename=filename)
    return json.dumps(out)


@mcp.tool()
def rollback_rule(changelog_id: str) -> str:
    """Rollback an append-only changelog entry id (stored in rules/machine_changelog.jsonl)."""
    log_tool_event("rollback_rule", {"changelog_id": changelog_id})
    _, _, _, rules, _ = _require_runtime()
    _metrics_record("rollback_rule")
    if "/" in changelog_id or "\\" in changelog_id:
        raise ValueError("changelog_id must not contain paths")
    out = rules.rollback_rule(changelog_id=str(changelog_id).strip())
    return json.dumps(out)


@mcp.tool()
def flag_problem(description: str, context: str, source_session_id: str = "anonymous") -> str:
    """Store a structured problem note and possibly auto-propose recurring rules."""
    log_tool_event("flag_problem", {"description": description, "context": context, "source_session_id": source_session_id})
    mem, _, _, rules, _ = _require_runtime()
    _metrics_record("flag_problem")
    out = handle_flag_problem(
        description=description,
        context=context,
        memory=mem,
        rules_svc=rules,
        source_session_id=source_session_id,
    )
    return json.dumps(out, default=str)


@mcp.tool()
def get_metrics() -> str:
    """Return JSON aggregate usage: per-tool calls, per-skill touches, memory/rule/problem buckets."""
    log_tool_event("get_metrics", {})
    _require_runtime()
    _metrics_record("get_metrics")
    return json.dumps(_METRICS.snapshot())


def run_stdio_server() -> None:
    init_session_logging()
    configure()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_stdio_server()
