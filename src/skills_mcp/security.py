"""Security helpers — basename-only APIs."""

from __future__ import annotations

import re


def validate_basename(name: str, *, suffix: str | None = None) -> str:
    if name in {"", ".", ".."}:
        raise ValueError("invalid name")
    if "/" in name or "\\" in name:
        raise ValueError("paths are not allowed; use basename only")
    if ".." in name:
        raise ValueError("paths are not allowed")
    cleaned = name.strip()
    if suffix and not cleaned.endswith(suffix):
        raise ValueError(f"name must end with {suffix}")
    return cleaned


def slugify_trigger(text: str, max_len: int = 60) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-") or "rule"
    return s[:max_len].strip("-")
