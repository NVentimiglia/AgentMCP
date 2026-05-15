"""Path helpers for resolving optional shared content directories."""

from __future__ import annotations

from pathlib import Path


def _resolve_dir(project_root: Path, configured: str | None) -> Path | None:
    """Return a resolved directory Path or None if unset or not found on disk."""
    if configured is None or not str(configured).strip():
        return None
    raw = configured.strip()
    p = Path(raw).expanduser()
    resolved = p.resolve() if p.is_absolute() else (project_root / raw).expanduser().resolve()
    return resolved if resolved.is_dir() else None


def resolve_shared_skills_dir(project_root: Path, configured: str | None) -> Path | None:
    """Resolve ``paths.shared_skills`` → directory or None."""
    return _resolve_dir(project_root, configured)


def resolve_content_dir(project_root: Path, configured: str | None) -> Path | None:
    """Resolve ``paths.content`` → directory or None."""
    return _resolve_dir(project_root, configured)
