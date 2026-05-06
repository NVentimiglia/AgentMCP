"""Path helpers for resolving optional skill library directories."""

from __future__ import annotations

from pathlib import Path


def resolve_shared_skills_dir(project_root: Path, configured: str | None) -> Path | None:
    """Return normalized directory Path or ``None`` if unset or missing."""
    if configured is None or not str(configured).strip():
        return None
    raw = configured.strip()
    p = Path(raw).expanduser()
    resolved = p.resolve() if p.is_absolute() else (project_root / raw).expanduser().resolve()
    return resolved if resolved.is_dir() else None
