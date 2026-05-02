from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent_mcp.config import AgentConfig, load_config, resolve_path
from agent_mcp.paths import CONFIG_NAME


@dataclass
class AppContext:
    root: Path
    config: AgentConfig
    skills_dir: Path
    rules_active_dir: Path
    rules_proposals_dir: Path
    memory_dir: Path
    state_dir: Path
    changelog_path: Path
    clusters_path: Path
    metrics_path: Path


_APP: AppContext | None = None


def init_app(root: Path) -> AppContext:
    cfg = load_config(root)
    global _APP
    _APP = AppContext(
        root=root,
        config=cfg,
        skills_dir=resolve_path(root, cfg.paths.skills),
        rules_active_dir=resolve_path(root, cfg.paths.rules_active),
        rules_proposals_dir=resolve_path(root, cfg.paths.rules_proposals),
        memory_dir=resolve_path(root, cfg.paths.memory),
        state_dir=(root / "state").resolve(),
        changelog_path=(root / "rules" / "CHANGELOG.md").resolve(),
        clusters_path=(root / "state" / "clusters.json").resolve(),
        metrics_path=(root / "state" / "metrics.json").resolve(),
    )
    return _APP


def get_app() -> AppContext:
    if _APP is None:
        raise RuntimeError(f"Agent MCP not initialized. Missing {CONFIG_NAME} load?")
    return _APP


def reset_app() -> None:
    global _APP
    _APP = None
