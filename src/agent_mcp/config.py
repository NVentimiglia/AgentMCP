from __future__ import annotations

from pathlib import Path
from typing import Literal

import tomli
from pydantic import BaseModel, Field, model_validator


class ModeConfig(BaseModel):
    rules: Literal["proposal", "auto"] = "proposal"


class PathsConfig(BaseModel):
    skills: str = "skills"
    rules_active: str = "rules/active"
    rules_proposals: str = "rules/proposals"
    memory: str = "memory"


class MemoryConfig(BaseModel):
    backend: str = "chromadb"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    inject_token_budget: int = 2000
    vector_weight: float | None = None
    lexical_weight: float | None = None
    relevance_floor: float | None = None

    @model_validator(mode="after")
    def normalize_weights(self) -> MemoryConfig:
        vw, lw = self.vector_weight, self.lexical_weight
        if vw is None and lw is None:
            return self
        if vw is None and lw is not None:
            lw = float(lw)
            if lw < 0 or lw > 1:
                raise ValueError("lexical_weight must be in [0, 1]")
            object.__setattr__(self, "lexical_weight", lw)
            object.__setattr__(self, "vector_weight", 1.0 - lw)
            return self
        if vw is not None and lw is None:
            vw = float(vw)
            if vw < 0 or vw > 1:
                raise ValueError("vector_weight must be in [0, 1]")
            object.__setattr__(self, "vector_weight", vw)
            object.__setattr__(self, "lexical_weight", 1.0 - vw)
            return self
        vw_f, lw_f = float(vw), float(lw)
        s = vw_f + lw_f
        if s <= 0:
            raise ValueError("vector_weight + lexical_weight must be positive")
        object.__setattr__(self, "vector_weight", vw_f / s)
        object.__setattr__(self, "lexical_weight", lw_f / s)
        return self

    def effective_vector_weight(self) -> float:
        return 0.7 if self.vector_weight is None else float(self.vector_weight)

    def effective_lexical_weight(self) -> float:
        return 0.3 if self.lexical_weight is None else float(self.lexical_weight)


class ProblemsConfig(BaseModel):
    similarity_threshold: float = 0.72
    recurrence_count: int = 3


class RulesPromotionConfig(BaseModel):
    max_auto_promotions_per_day: int = 5


class AgentConfig(BaseModel):
    mode: ModeConfig = Field(default_factory=ModeConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    problems: ProblemsConfig = Field(default_factory=ProblemsConfig)
    rules: RulesPromotionConfig = Field(default_factory=RulesPromotionConfig)


def load_config(root: Path) -> AgentConfig:
    path = root / "config.toml"
    if not path.is_file():
        raise FileNotFoundError(f"Missing config: {path}")
    data = tomli.loads(path.read_text(encoding="utf-8"))
    return AgentConfig.model_validate(
        {
            "mode": data.get("mode", {}),
            "paths": data.get("paths", {}),
            "memory": data.get("memory", {}),
            "problems": data.get("problems", {}),
            "rules": data.get("rules", {}),
        }
    )


def resolve_path(root: Path, rel: str) -> Path:
    return (root / rel).resolve()
