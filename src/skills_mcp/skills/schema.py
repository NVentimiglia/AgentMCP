from __future__ import annotations

import re
import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

class SkillFrontmatter(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    # Legacy v0.1 field; still supported.
    triggers: list[str] = Field(default_factory=list)
    # Agent Skills optional fields
    license: str | None = None
    compatibility: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    allowed_tools: str | None = Field(default=None, alias="allowed-tools")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if len(value) > 64:
            raise ValueError("name must be <= 64 characters")
        if "--" in value:
            raise ValueError("name must not contain consecutive hyphens")
        if not NAME_RE.fullmatch(value):
            raise ValueError(
                "name must contain only lowercase letters, digits, and single hyphens"
            )
        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        if len(value) > 1024:
            raise ValueError("description must be <= 1024 characters")
        return value

    @field_validator("compatibility")
    @classmethod
    def validate_compatibility(cls, value: str | None) -> str | None:
        if value is not None and not (1 <= len(value) <= 500):
            raise ValueError("compatibility must be 1-500 characters when provided")
        return value


class ParsedSkill(BaseModel):
    fm: SkillFrontmatter
    body: str

    def full_markdown(self) -> str:
        dump = yaml.safe_dump(self.fm.model_dump(), sort_keys=False, allow_unicode=True).strip()
        return f"---\n{dump}\n---\n{self.body.lstrip()}"
