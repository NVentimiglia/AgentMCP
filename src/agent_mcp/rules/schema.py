from __future__ import annotations

from pydantic import BaseModel, Field


class RuleFrontmatter(BaseModel):
    id: str = Field(..., min_length=1)
    created: str = Field(..., min_length=1)
    trigger: str = Field(..., min_length=1)
    solution: str = Field(..., min_length=1)


class ParsedRule(BaseModel):
    fm: RuleFrontmatter
    body: str
