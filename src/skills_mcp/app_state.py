from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from skills_mcp.config import AgentConfig, load_config, resolve_path
from skills_mcp.paths import CONFIG_NAME


@dataclass
class AppContext:
    """Resolved filesystem layout for one project."""

    root: Path
    config: AgentConfig
    #: Resolved agent folders in priority order (last = highest priority).
    agent_dirs: list[Path]
    #: Resolved skill directories (agent_dir/skills/) in same priority order.
    skill_dirs: list[Path]
    state_dir: Path


_APP: AppContext | None = None


def init_app(root: Path) -> AppContext:
    cfg = load_config(root)
    resolved_root = root.resolve()

    agent_dirs = [resolve_path(resolved_root, f) for f in cfg.agent_folders]
    skill_dirs = [d / "skills" for d in agent_dirs]

    # Prepend the global agent library if provided (lowest priority — project agents win).
    # SKILLS_MCP_LIBRARY points to an agent folder; its skills/ subdir and AGENT.md
    # are included alongside the configured agent_folders.
    library_env = os.environ.get("SKILLS_MCP_LIBRARY")
    if library_env:
        library_path = Path(library_env).resolve()
        library_skills = library_path / "skills"
        if library_path.is_dir() and library_path not in agent_dirs:
            agent_dirs = [library_path] + agent_dirs
            skill_dirs = [library_skills] + skill_dirs

    global _APP
    _APP = AppContext(
        root=resolved_root,
        config=cfg,
        agent_dirs=agent_dirs,
        skill_dirs=skill_dirs,
        state_dir=(resolved_root / "state").resolve(),
    )
    return _APP


def get_app() -> AppContext:
    if _APP is None:
        raise RuntimeError(f"SkillsMCP not initialized. Missing {CONFIG_NAME} load?")
    return _APP


def reset_app() -> None:
    global _APP
    _APP = None
