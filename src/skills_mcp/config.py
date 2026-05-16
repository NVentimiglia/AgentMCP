from __future__ import annotations

from pathlib import Path

import tomli
from pydantic import BaseModel, ConfigDict, Field


class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    #: Ordered list of agent folders. Each folder's skills/ subdir is scanned for skills;
    #: each folder's AGENT.md is injected into the session. Later entries take priority
    #: on name collision. Supports absolute paths or paths relative to the config file.
    agent_folders: list[str] = Field(default_factory=lambda: [".agents/"])


def load_config(root: Path) -> AgentConfig:
    path = root / "skillmcp.toml"
    if not path.is_file():
        return AgentConfig()
    data = tomli.loads(path.read_text(encoding="utf-8"))
    return AgentConfig.model_validate(data)


def resolve_path(root: Path, rel: str) -> Path:
    p = Path(rel).expanduser()
    return p.resolve() if p.is_absolute() else (root / rel).resolve()
