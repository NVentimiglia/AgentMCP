from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from skills_mcp.app_state import AppContext, init_app, reset_app
from skills_mcp.config import load_config, resolve_path
from skills_mcp.paths import project_root_from_env_or_discover
from skills_mcp.rules.instructions import render_mcp_seed_text
from skills_mcp.skills.loader import SkillIndex

mcp = FastMCP("skills-mcp")

_SKILLS: SkillIndex | None = None
_APP: AppContext | None = None


def configure_for_tests(root: Path) -> AppContext:
    """Initialize server globals (used by tests)."""
    return configure(root=root)


def configure(root: Path | None = None) -> AppContext:
    global _SKILLS, _APP
    if root is None:
        try:
            root = project_root_from_env_or_discover()
        except FileNotFoundError as e:
            raise RuntimeError(f"Cannot initialize SkillsMCP: {e}") from e
    _APP = init_app(root)
    _SKILLS = SkillIndex(_APP.skill_dirs, project_root=_APP.root)
    _SKILLS.scan()
    agent_md = _load_agent_md(_APP.root)
    mcp._mcp_server.instructions = render_mcp_seed_text(agent_md_content=agent_md)
    return _APP


def _load_agent_md(root: Path) -> str | None:
    """Read .agents/AGENT.md if present; return its content, else None."""
    path = root / ".agents" / "AGENT.md"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return None


def reset_runtime() -> None:
    global _SKILLS, _APP
    _SKILLS = None
    _APP = None
    reset_app()


def _require_runtime() -> tuple[SkillIndex, AppContext]:
    if _SKILLS is None or _APP is None:
        configure()
    return _SKILLS, _APP


def _run_traced(
    tool_name: str,
    fn: Callable[[], str],
) -> str:
    """Execute tool function."""
    _skills, app = _require_runtime()
    return fn()


def _impl_verify_setup() -> str:
    skills, app = _require_runtime()

    issues: list[str] = []
    for d in app.skill_dirs:
        if not d.is_dir():
            issues.append(f"skill_dir_missing: {d}")
    if not app.skill_dirs:
        issues.append("no skill_folders configured")

    meta = skills.list_skills_meta()

    report = {
        "ok": len(issues) == 0,
        "checked_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project_root": str(app.root.resolve()),
        "skill_dirs": [str(d) for d in app.skill_dirs],
        "issues": issues,
        "skills_count": len(meta),
    }
    return json.dumps(report, indent=2, ensure_ascii=False, sort_keys=False)


@mcp.tool()
def verify_setup(session_note: str = "") -> str:
    """One-call health snapshot: paths and skill counts."""
    return _run_traced("verify_setup", _impl_verify_setup)


def _local_skill_index(project_path: str, app: AppContext) -> "SkillIndex | None":
    """Build a SkillIndex for a local project path if it differs from the global root."""
    if not project_path or not project_path.strip():
        return None
    local_root = Path(project_path.strip()).resolve()
    if local_root == app.root:
        return None
    # Load skill_folders from local skillmcp.toml if present, else default
    local_cfg_path = local_root / "skillmcp.toml"
    if local_cfg_path.is_file():
        local_cfg = load_config(local_root)
        dirs = [resolve_path(local_root, f) for f in local_cfg.skill_folders]
    else:
        default = local_root / ".agents" / "skills"
        if not default.is_dir():
            return None
        dirs = [default]
    dirs = [d for d in dirs if d.is_dir()]
    if not dirs:
        return None
    idx = SkillIndex(dirs, project_root=local_root)
    idx.scan()
    return idx


def _impl_list_skills(project_path: str) -> str:
    skills, app = _require_runtime()
    global_meta = list(skills.list_skills_meta())
    local_idx = _local_skill_index(project_path, app)
    if local_idx is None:
        return json.dumps(global_meta, ensure_ascii=False)
    local_meta = list(local_idx.list_skills_meta())
    local_names = {m["name"] for m in local_meta}
    merged = local_meta + [m for m in global_meta if m["name"] not in local_names]
    return json.dumps(merged, ensure_ascii=False)


@mcp.tool()
def list_skills(project_path: str = "", session_note: str = "") -> str:
    """Return JSON list of skill metadata — global skills merged with local project skills.

    Pass ``project_path`` (absolute path of the project you are working in) to
    include skills from that project's skill folders.  Local skills take
    precedence over global on name collision.
    """
    return _run_traced("list_skills", lambda: _impl_list_skills(project_path))


def _impl_read_skill(name: str, project_path: str, usage_reason: str) -> str:
    skills, app = _require_runtime()
    local_idx = _local_skill_index(project_path, app)
    if local_idx is not None:
        try:
            sk = local_idx.get_by_name(name)
            return sk.parsed.full_markdown()
        except (KeyError, ValueError):
            pass
    sk = skills.get_by_name(name)
    return sk.parsed.full_markdown()


@mcp.tool()
def read_skill(name: str, project_path: str = "", usage_reason: str = "", session_note: str = "") -> str:
    """Return the full Markdown for a skill by name.

    Checks the local project's skill folders first (if ``project_path`` given),
    then falls back to global skills.
    """
    return _run_traced("read_skill", lambda: _impl_read_skill(name, project_path, usage_reason))


def run_stdio_server(root: Path | None = None) -> None:
    configure(root=root)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_stdio_server()
