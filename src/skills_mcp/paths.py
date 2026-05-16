from __future__ import annotations

import os
from pathlib import Path

CONFIG_NAME = "config.toml"


def _looks_like_agent_project(root: Path) -> bool:
    """Return True if the directory looks like a skills-mcp project."""
    # New convention: .agents/ folder
    if (root / ".agents").is_dir():
        return True
    # Legacy: skills/ + rules/ at root level
    return (root / "skills").is_dir() and (root / "rules").is_dir()


def find_project_root(start: Path | None = None) -> Path:
    """Walk upward from `start` (default: cwd) until a skills-mcp project's config.toml is found."""
    cur = (start or Path.cwd()).resolve()
    for p in [cur, *cur.parents]:
        if (p / CONFIG_NAME).is_file() and _looks_like_agent_project(p):
            return p
    raise FileNotFoundError(
        f"Could not find {CONFIG_NAME} in {cur} or any parent directory. "
        "Run `skills-mcp init` or set SKILLS_MCP_ROOT (or legacy AGENT_MCP_ROOT) to a project directory."
    )


def project_root_from_env_or_discover() -> Path:
    env = os.environ.get("SKILLS_MCP_ROOT") or os.environ.get("AGENT_MCP_ROOT")
    if env:
        root = Path(env).expanduser().resolve()
        if not (root / CONFIG_NAME).is_file():
            raise FileNotFoundError(
                f"SKILLS_MCP_ROOT/AGENT_MCP_ROOT={root} has no {CONFIG_NAME}"
            )
        return root
    return find_project_root()
