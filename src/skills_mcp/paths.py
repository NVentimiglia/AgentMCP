from __future__ import annotations

import os
from pathlib import Path

CONFIG_NAME = "skillmcp.toml"


def find_project_root(start: Path | None = None) -> Path:
    """Walk upward from `start` (default: cwd) until a skillmcp.toml is found."""
    cur = (start or Path.cwd()).resolve()
    for p in [cur, *cur.parents]:
        if (p / CONFIG_NAME).is_file():
            return p
    raise FileNotFoundError(
        f"Could not find {CONFIG_NAME} in '{cur}' or any parent directory. "
        "Run `skills-mcp init` to create a project, or set the SKILLS_MCP_ROOT "
        "environment variable to your project directory."
    )


def project_root_from_env_or_discover() -> Path:
    env_key = "SKILLS_MCP_ROOT"
    val = os.environ.get(env_key)

    if val:
        root = Path(val).expanduser().resolve()
        if root.is_dir() and (root / CONFIG_NAME).is_file():
            return root

    try:
        return find_project_root()
    except FileNotFoundError as e:
        if val:
            raise FileNotFoundError(
                f"Could not find SkillsMCP project. Environment variable {env_key} points to "
                f"invalid path '{val}', and auto-discovery from current directory failed: {e}"
            ) from e
        raise
