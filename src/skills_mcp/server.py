from __future__ import annotations

import json
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

    _RULE_INDEX = ActiveRuleIndex(_APP.rules_dir)
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


@mcp.tool()
def verify_setup() -> str:
    """One-call health snapshot: paths and skill/rule counts."""
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
def list_skills() -> str:
    """Return JSON list of skill metadata (name, description, path, …)."""
    skills, _, _, _app = _require_runtime()
    meta = list(skills.list_skills_meta())
    return json.dumps(meta, ensure_ascii=False)


@mcp.tool()
def read_skill(name: str, usage_reason: str = "") -> str:
    """Return the full Markdown for a skill by name (including frontmatter)."""
    skills, _, _, _app = _require_runtime()
    sk = skills.get_by_name(name)
    return sk.parsed.full_markdown()


@mcp.tool()
def list_rules() -> str:
    """Return JSON list of rule metadata (id, trigger, file) under ``paths.rules``."""
    _, idx, _, _app = _require_runtime()
    return json.dumps(idx.list_catalog(), ensure_ascii=False)


@mcp.tool()
def read_rules(rule_id: str) -> str:
    """Return the full Markdown for one rule by YAML ``id`` (including frontmatter)."""
    _, idx, _, _app = _require_runtime()
    return idx.read_full_markdown(rule_id)


def run_stdio_server() -> None:
    configure()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_stdio_server()
