"""Import Claude Code (and Gemini) session transcripts into sessions/*.md.

Bridges the gap between raw JSONL transcripts (used by analyze) and the
human-readable session files the learn pass expects.

Usage:
    skills-mcp sessions import [--project-path PATH]
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _claude_projects_dir() -> Path:
    return Path.home() / ".claude" / "projects"


def _project_folder_name(project_root: Path) -> str:
    """Convert an absolute path to the Claude Code project folder name.

    Claude lowercases the drive letter then replaces ``:`` and path separators
    with ``-``, so ``D:\\Projects\\AgentMCP`` becomes ``d--Projects-AgentMCP``.
    """
    resolved = str(project_root.resolve())
    # Lowercase only the drive letter (first char when followed by colon)
    if len(resolved) >= 2 and resolved[1] == ":":
        resolved = resolved[0].lower() + resolved[1:]
    # Replace : and path separators with -
    return resolved.replace(":", "-").replace("\\", "-").replace("/", "-")


def _find_project_jsonl(project_root: Path) -> list[Path]:
    folder_name = _project_folder_name(project_root)
    project_dir = _claude_projects_dir() / folder_name
    if not project_dir.is_dir():
        return []
    return sorted(project_dir.glob("*.jsonl"))


# ---------------------------------------------------------------------------
# JSONL → Markdown conversion
# ---------------------------------------------------------------------------

def _extract_text(content: object) -> str:
    """Pull plain text out of a message content field (str or list of blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                name = block.get("name", "tool")
                inp = block.get("input", {})
                parts.append(f"[tool: {name}({json.dumps(inp, ensure_ascii=False)[:120]})]")
        return "\n".join(parts)
    return ""


def _strip_system_tags(text: str) -> str:
    """Remove IDE/system injected tags that clutter session files."""
    text = re.sub(r"<ide_(?:opened|selection)_file>.*?</ide_(?:opened|selection)_file>", "", text, flags=re.DOTALL)
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.DOTALL)
    return text.strip()


def jsonl_to_markdown(jsonl_path: Path) -> str | None:
    """Convert one JSONL session file to a readable Markdown string.

    Returns ``None`` if the file contains no user/assistant turns.
    """
    lines_raw = jsonl_path.read_text(encoding="utf-8", errors="replace").splitlines()

    turns: list[tuple[str, str]] = []  # (role, text)
    session_date: str | None = None
    ai_title: str | None = None

    for raw in lines_raw:
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue

        t = obj.get("type")

        if t == "ai-title":
            ai_title = obj.get("aiTitle")

        if t in ("user", "assistant"):
            ts = obj.get("timestamp")
            if ts and session_date is None:
                try:
                    session_date = ts[:10]  # YYYY-MM-DD
                except Exception:
                    pass

            msg = obj.get("message", {})
            content = msg.get("content", "")
            text = _strip_system_tags(_extract_text(content))
            if text:
                turns.append((t, text))

    if not turns:
        return None

    date_str = session_date or datetime.now(UTC).strftime("%Y-%m-%d")
    title = ai_title or jsonl_path.stem[:40]

    lines: list[str] = [
        f"# Session: {title}",
        f"",
        f"**Date:** {date_str}  ",
        f"**Source:** {jsonl_path.name}",
        f"",
        "---",
        "",
    ]

    for role, text in turns:
        tag = "**User**" if role == "user" else "**Assistant**"
        lines.append(f"### {tag}\n")
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Import command
# ---------------------------------------------------------------------------

def _already_imported(sessions_dir: Path, jsonl_path: Path) -> bool:
    """Check if a session was already imported (marker in existing .md files)."""
    marker = jsonl_path.name
    for md in sessions_dir.glob("*.md"):
        if md.name in ("log.md", "README.md"):
            continue
        try:
            if marker in md.read_text(encoding="utf-8"):
                return True
        except OSError:
            pass
    return False


def import_sessions(project_root: Path, sessions_dir: Path) -> tuple[int, int]:
    """Import new JSONL transcripts into ``sessions_dir`` as Markdown files.

    Returns ``(imported, skipped)`` counts.
    """
    jsonl_files = _find_project_jsonl(project_root)
    if not jsonl_files:
        return 0, 0

    sessions_dir.mkdir(parents=True, exist_ok=True)
    imported = 0
    skipped = 0

    for jf in jsonl_files:
        if _already_imported(sessions_dir, jf):
            skipped += 1
            continue

        md = jsonl_to_markdown(jf)
        if md is None:
            skipped += 1
            continue

        # Extract date for filename
        date_match = re.search(r"\*\*Date:\*\* (\d{4}-\d{2}-\d{2})", md)
        date_str = date_match.group(1) if date_match else datetime.now(UTC).strftime("%Y-%m-%d")
        stem = jf.stem[:8]  # first 8 chars of session UUID
        out_path = sessions_dir / f"{date_str}-{stem}.md"

        # Avoid collisions
        suffix = 1
        while out_path.exists():
            out_path = sessions_dir / f"{date_str}-{stem}-{suffix}.md"
            suffix += 1

        out_path.write_text(md, encoding="utf-8")
        imported += 1

    return imported, skipped
