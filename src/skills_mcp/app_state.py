from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from skills_mcp.config import AgentConfig, load_config, resolve_path
from skills_mcp.paths import CONFIG_NAME


@dataclass
class AppContext:
    """Resolved filesystem layout for one project."""

    root: Path
    config: AgentConfig
    skills_dir: Path
    shared_skills_dir: Path | None
    rules_dir: Path
    state_dir: Path


_APP: AppContext | None = None


def init_app(root: Path) -> AppContext:
    cfg = load_config(root)
    from skills_mcp.config_paths import resolve_shared_skills_dir

    resolved_root = root.resolve()
    ss = resolve_shared_skills_dir(resolved_root, cfg.paths.shared_skills)

    global _APP
    _APP = AppContext(
        root=resolved_root,
        config=cfg,
        skills_dir=resolve_path(resolved_root, cfg.paths.skills),
        shared_skills_dir=ss,
        rules_dir=resolve_path(resolved_root, cfg.paths.rules),
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
