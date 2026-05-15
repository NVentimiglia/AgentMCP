from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from skills_mcp.app_state import AppContext, init_app, reset_app
from skills_mcp.paths import project_root_from_env_or_discover
from skills_mcp.rules.instructions import render_mcp_seed_text
from skills_mcp.rules.loader import ActiveRuleIndex
from skills_mcp.rules.service import RulesService
from skills_mcp.session_logging import init_project_error_logging
from skills_mcp.skills.loader import SkillIndex
from skills_mcp.usage_counters import counters_snapshot_json, increment_tool_counter
from skills_mcp.usage_logs import append_tool_log, format_exception, sanitize_path_segment

mcp = FastMCP("skills-mcp")

_SKILLS: SkillIndex | None = None
_RULE_INDEX: ActiveRuleIndex | None = None
_RULES: RulesService | None = None
_APP: AppContext | None = None


def configure_for_tests(root: Path) -> AppContext:
    """Initialize server globals (used by tests)."""
    return configure(root=root)


def configure(root: Path | None = None) -> AppContext:
    global _SKILLS, _RULE_INDEX, _RULES, _APP
    if root is None:
        root = project_root_from_env_or_discover()
    _APP = init_app(root)
    init_project_error_logging(_APP.state_dir / "logs")

    lib_roots: tuple[Path, ...] = ()
    if _APP.shared_skills_dir:
        lib_roots = (_APP.shared_skills_dir,)
    _SKILLS = SkillIndex(
        _APP.skills_dir,
        project_root=_APP.root,
        library_skill_dirs=lib_roots,
    )
    _SKILLS.scan()

    _RULE_INDEX = ActiveRuleIndex(_APP.rules_dir, library_rules_dir=_APP.shared_rules_dir)
    _RULE_INDEX.reload()
    _sync_mcp_session_instructions(_RULE_INDEX)

    _RULES = RulesService(_APP, active_index=_RULE_INDEX)
    return _APP


def _sync_mcp_session_instructions(idx: ActiveRuleIndex) -> None:
    """Push ``rules/*.md`` into MCP server ``instructions`` (host passes to each agent session)."""
    mcp._mcp_server.instructions = render_mcp_seed_text(idx)


def reset_runtime() -> None:
    global _SKILLS, _RULE_INDEX, _RULES, _APP
    _SKILLS = None
    _RULE_INDEX = None
    _RULES = None
    _APP = None
    reset_app()


def _require_runtime() -> tuple[SkillIndex, ActiveRuleIndex, RulesService, AppContext]:
    if _SKILLS is None or _RULE_INDEX is None or _RULES is None or _APP is None:
        configure()
    assert _SKILLS is not None
    assert _RULE_INDEX is not None
    assert _RULES is not None
    assert _APP is not None
    return _SKILLS, _RULE_INDEX, _RULES, _APP


def _run_traced(
    tool_name: str,
    log_bucket: tuple[str, ...],
    args_for_log: dict[str, object],
    session_note: str,
    fn: Callable[[], str],
) -> str:
    """Increment counters (before run), execute, append trace log in ``finally``."""
    *_rest, app = _require_runtime()
    increment_tool_counter(app.root, tool_name)
    response: str | None = None
    err_tb: str | None = None
    try:
        response = fn()
        return response
    except BaseException as exc:
        err_tb = format_exception(exc)
        raise
    finally:
        append_tool_log(
            app.root,
            bucket_parts=log_bucket,
            tool_name=tool_name,
            args=args_for_log,
            session_note=session_note,
            response=response,
            error=err_tb,
        )


def _impl_verify_setup() -> str:
    skills, idx, _, app = _require_runtime()

    issues: list[str] = []

    sd = app.skills_dir
    rd = app.rules_dir
    st = app.state_dir

    if not sd.is_dir():
        issues.append("skills_dir_missing")
    if not rd.is_dir():
        issues.append("rules_dir_missing")
    if not st.is_dir():
        issues.append("state_dir_missing")

    meta = skills.list_skills_meta()
    rules_tt = idx.list_ids_triggers()

    report = {
        "ok": len(issues) == 0,
        "checked_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project_root": str(app.root.resolve()),
        "paths": {
            "skills_dir": str(sd.resolve()),
            "shared_skills_dir": str(app.shared_skills_dir.resolve())
            if app.shared_skills_dir
            else None,
            "rules_dir": str(rd.resolve()),
            "state_dir": str(st.resolve()),
        },
        "issues": issues,
        "skills_count": len(meta),
        "rules_count": len(rules_tt),
    }
    return json.dumps(report, indent=2, ensure_ascii=False, sort_keys=False)


@mcp.tool()
def verify_setup(session_note: str = "") -> str:
    """One-call health snapshot: paths and skill/rule counts."""
    return _run_traced(
        "verify_setup",
        ("_tools", "verify_setup"),
        {"session_note": session_note},
        session_note,
        _impl_verify_setup,
    )


def _impl_list_skills() -> str:
    skills, _, _, _app = _require_runtime()
    meta = list(skills.list_skills_meta())
    return json.dumps(meta, ensure_ascii=False)


@mcp.tool()
def list_skills(session_note: str = "") -> str:
    """Return JSON list of skill metadata (name, description, path, …)."""
    return _run_traced(
        "list_skills",
        ("_tools", "list_skills"),
        {"session_note": session_note},
        session_note,
        _impl_list_skills,
    )


def _impl_read_skill(name: str, usage_reason: str) -> str:
    skills, _, _, _app = _require_runtime()
    sk = skills.get_by_name(name)
    return sk.parsed.full_markdown()


@mcp.tool()
def read_skill(name: str, usage_reason: str = "", session_note: str = "") -> str:
    """Return the full Markdown for a skill by name (including frontmatter)."""
    bucket = (sanitize_path_segment(name, fallback="invalid_skill"),)
    return _run_traced(
        "read_skill",
        bucket,
        {"name": name, "usage_reason": usage_reason, "session_note": session_note},
        session_note,
        lambda: _impl_read_skill(name, usage_reason),
    )


def _impl_list_rules() -> str:
    _, idx, _, _app = _require_runtime()
    return json.dumps(idx.list_catalog(), ensure_ascii=False)


@mcp.tool()
def list_rules(session_note: str = "") -> str:
    """Return JSON list of rule metadata (id, trigger, file) under ``paths.rules``."""
    return _run_traced(
        "list_rules",
        ("_tools", "list_rules"),
        {"session_note": session_note},
        session_note,
        _impl_list_rules,
    )


def _impl_read_rules(rule_id: str) -> str:
    _, idx, _, _app = _require_runtime()
    return idx.read_full_markdown(rule_id)


@mcp.tool()
def read_rules(rule_id: str, session_note: str = "") -> str:
    """Return the full Markdown for one rule by YAML ``id`` (including frontmatter)."""
    bucket = ("_rules", sanitize_path_segment(rule_id, fallback="unknown_rule"))
    return _run_traced(
        "read_rules",
        bucket,
        {"rule_id": rule_id, "session_note": session_note},
        session_note,
        lambda: _impl_read_rules(rule_id),
    )


_SESSION_SKIP = frozenset({"log.md", "readme.md", ".gitkeep"})


def _learn_loop_snapshot(app: AppContext, skills: SkillIndex) -> dict[str, object]:
    """Collect learning-loop file metrics: session counts, pending sessions, last learn pass."""
    sessions_dir = app.root / "sessions"
    log_md = sessions_dir / "log.md"

    session_files: list[Path] = []
    if sessions_dir.is_dir():
        session_files = [
            p for p in sessions_dir.glob("*.md")
            if p.name.lower() not in _SESSION_SKIP
        ]

    last_learn_pass: str | None = None
    log_mtime: float | None = None
    if log_md.is_file():
        try:
            log_mtime = log_md.stat().st_mtime
            last_learn_pass = datetime.fromtimestamp(log_mtime, tz=UTC).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        except OSError:
            pass

    pending = 0
    for sf in session_files:
        try:
            mt = sf.stat().st_mtime
        except OSError:
            continue
        if log_mtime is None or mt > log_mtime:
            pending += 1

    return {
        "skills_count": len(list(skills.list_skills_meta())),
        "sessions_total": len(session_files),
        "sessions_pending": pending,
        "last_learn_pass": last_learn_pass,
    }


def _impl_get_usage_counters() -> str:
    skills, _idx, _rules, app = _require_runtime()
    data: dict[str, object] = json.loads(
        counters_snapshot_json(app.root, project_root_str=str(app.root.resolve()))
    )
    data["learn_loop"] = _learn_loop_snapshot(app, skills)
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False)


@mcp.tool()
def get_usage_counters(session_note: str = "") -> str:
    """Return JSON usage counters (per-tool totals and ``usage_counters.json`` snapshot)."""
    return _run_traced(
        "get_usage_counters",
        ("_tools", "get_usage_counters"),
        {"session_note": session_note},
        session_note,
        _impl_get_usage_counters,
    )


def run_stdio_server() -> None:
    configure()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_stdio_server()
