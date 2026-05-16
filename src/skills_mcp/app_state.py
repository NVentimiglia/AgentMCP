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
    #: Resolved skill directories in priority order (last = highest priority).
    skill_dirs: list[Path]
    state_dir: Path


_APP: AppContext | None = None


def init_app(root: Path) -> AppContext:
    cfg = load_config(root)
    resolved_root = root.resolve()

    skill_dirs = [resolve_path(resolved_root, f) for f in cfg.skill_folders]

    # Prepend the global skills library if provided (lowest priority — project skills win).
    library_env = os.environ.get("SKILLS_MCP_LIBRARY")
    if library_env:
        library_path = Path(library_env).resolve()
        if library_path.is_dir() and library_path not in skill_dirs:
            skill_dirs = [library_path] + skill_dirs

    global _APP
    _APP = AppContext(
        root=resolved_root,
        config=cfg,
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
