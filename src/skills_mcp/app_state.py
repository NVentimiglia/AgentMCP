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
    shared_rules_dir: Path | None
    state_dir: Path


_APP: AppContext | None = None


def init_app(root: Path) -> AppContext:
    cfg = load_config(root)
    from skills_mcp.config_paths import resolve_content_dir, resolve_shared_skills_dir

    resolved_root = root.resolve()

    # Resolve content bundle (skills/ + rules/ subdirs).
    content_dir = resolve_content_dir(resolved_root, cfg.paths.content)

    # shared_skills: explicit config wins; fall back to content/skills/.
    if cfg.paths.shared_skills:
        ss = resolve_shared_skills_dir(resolved_root, cfg.paths.shared_skills)
    elif content_dir is not None:
        sub = content_dir / "skills"
        ss = sub if sub.is_dir() else None
    else:
        ss = None

    # shared_rules: always derived from content/rules/ (no separate config key yet).
    shared_rules: Path | None = None
    if content_dir is not None:
        sub = content_dir / "rules"
        shared_rules = sub if sub.is_dir() else None

    global _APP
    _APP = AppContext(
        root=resolved_root,
        config=cfg,
        skills_dir=resolve_path(resolved_root, cfg.paths.skills),
        shared_skills_dir=ss,
        rules_dir=resolve_path(resolved_root, cfg.paths.rules),
        shared_rules_dir=shared_rules,
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
