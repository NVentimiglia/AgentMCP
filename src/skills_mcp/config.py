from __future__ import annotations

from pathlib import Path
from typing import Any

import tomli
from pydantic import BaseModel, ConfigDict, Field


class PathsConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    skills: str = "skills"
    rules: str = "rules"
    #: Optional secondary skills repository (merged; project wins on name clash).
    shared_skills: str | None = None
    #: Optional shared content folder containing skills/ and rules/ subdirectories.
    #: Provides both shared skills and shared rules; project always wins on collision.
    content: str | None = None


class ProjectDocConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    #: Auto-update Project.md on every analyze run (default: true).
    auto_update: bool = True


class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    paths: PathsConfig = Field(default_factory=PathsConfig)
    project_doc: ProjectDocConfig = Field(default_factory=ProjectDocConfig)


def load_config(root: Path) -> AgentConfig:
    path = root / "config.toml"
    if not path.is_file():
        raise FileNotFoundError(f"Missing config: {path}")
    data = tomli.loads(path.read_text(encoding="utf-8"))
    return AgentConfig.model_validate({
        "paths": data.get("paths", {}),
        "project_doc": data.get("project_doc", {}),
    })


def resolve_path(root: Path, rel: str) -> Path:
    return (root / rel).resolve()
