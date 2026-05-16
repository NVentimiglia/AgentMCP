"""Register skills-mcp as an MCP server in host agent configs.

Once registered, the host spawns ``skills-mcp serve`` automatically at session
start — the user never runs it manually.

Supported hosts
---------------
claude      — ~/.claude/settings.json           mcpServers entry
cursor      — ~/.cursor/mcp.json                mcpServers entry
gemini      — ~/.gemini/settings.json           mcpServers entry
antigravity — ~/.antigravity/mcp.json           mcpServers entry  (Google IDE)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SERVER_KEY = "skills-mcp"


def _load_json(path: Path) -> dict:
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _server_entry(project_root: Path) -> dict:
    """Build the mcpServers entry for this installation."""
    return {
        "command": sys.executable,
        "args": ["-m", "skills_mcp", "serve"],
        "env": {"SKILLS_MCP_ROOT": str(project_root.resolve())},
    }


# ---------------------------------------------------------------------------
# Claude Code  (~/.claude/settings.json)
# ---------------------------------------------------------------------------

_CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"


def claude_registered() -> bool:
    data = _load_json(_CLAUDE_SETTINGS)
    return _SERVER_KEY in (data.get("mcpServers") or {})


def register_claude(project_root: Path) -> tuple[bool, str]:
    if claude_registered():
        return False, f"already registered ({_CLAUDE_SETTINGS})"
    data = _load_json(_CLAUDE_SETTINGS)
    data.setdefault("mcpServers", {})[_SERVER_KEY] = _server_entry(project_root)
    try:
        _save_json(_CLAUDE_SETTINGS, data)
    except OSError as exc:
        return False, f"could not write {_CLAUDE_SETTINGS}: {exc}"
    return True, str(_CLAUDE_SETTINGS)


# ---------------------------------------------------------------------------
# Cursor  (~/.cursor/mcp.json)
# ---------------------------------------------------------------------------

_CURSOR_SETTINGS = Path.home() / ".cursor" / "mcp.json"


def cursor_registered() -> bool:
    data = _load_json(_CURSOR_SETTINGS)
    return _SERVER_KEY in (data.get("mcpServers") or {})


def register_cursor(project_root: Path) -> tuple[bool, str]:
    if cursor_registered():
        return False, f"already registered ({_CURSOR_SETTINGS})"
    data = _load_json(_CURSOR_SETTINGS)
    data.setdefault("mcpServers", {})[_SERVER_KEY] = _server_entry(project_root)
    try:
        _save_json(_CURSOR_SETTINGS, data)
    except OSError as exc:
        return False, f"could not write {_CURSOR_SETTINGS}: {exc}"
    return True, str(_CURSOR_SETTINGS)


# ---------------------------------------------------------------------------
# Gemini CLI  (~/.gemini/settings.json)
# ---------------------------------------------------------------------------

_GEMINI_SETTINGS = Path.home() / ".gemini" / "settings.json"


def gemini_registered() -> bool:
    data = _load_json(_GEMINI_SETTINGS)
    return _SERVER_KEY in (data.get("mcpServers") or {})


def register_gemini(project_root: Path) -> tuple[bool, str]:
    if gemini_registered():
        return False, f"already registered ({_GEMINI_SETTINGS})"
    data = _load_json(_GEMINI_SETTINGS)
    data.setdefault("mcpServers", {})[_SERVER_KEY] = _server_entry(project_root)
    try:
        _save_json(_GEMINI_SETTINGS, data)
    except OSError as exc:
        return False, f"could not write {_GEMINI_SETTINGS}: {exc}"
    return True, str(_GEMINI_SETTINGS)


# ---------------------------------------------------------------------------
# Antigravity  (~/.antigravity/mcp.json)  — Google IDE
# ---------------------------------------------------------------------------

_ANTIGRAVITY_SETTINGS = Path.home() / ".antigravity" / "mcp.json"


def antigravity_registered() -> bool:
    data = _load_json(_ANTIGRAVITY_SETTINGS)
    return _SERVER_KEY in (data.get("mcpServers") or {})


def register_antigravity(project_root: Path) -> tuple[bool, str]:
    if antigravity_registered():
        return False, f"already registered ({_ANTIGRAVITY_SETTINGS})"
    data = _load_json(_ANTIGRAVITY_SETTINGS)
    data.setdefault("mcpServers", {})[_SERVER_KEY] = _server_entry(project_root)
    try:
        _save_json(_ANTIGRAVITY_SETTINGS, data)
    except OSError as exc:
        return False, f"could not write {_ANTIGRAVITY_SETTINGS}: {exc}"
    return True, str(_ANTIGRAVITY_SETTINGS)


# ---------------------------------------------------------------------------
# Unified API
# ---------------------------------------------------------------------------

def registration_status() -> dict[str, bool]:
    """Return per-host registration status."""
    return {
        "claude": claude_registered(),
        "cursor": cursor_registered(),
        "gemini": gemini_registered(),
        "antigravity": antigravity_registered(),
    }


def register_all(project_root: Path) -> tuple[bool, str]:
    """Register with all supported hosts. Returns (ok, message)."""
    results: list[str] = []
    ok = True
    for host, fn in (
        ("claude", register_claude),
        ("cursor", register_cursor),
        ("gemini", register_gemini),
        ("antigravity", register_antigravity),
    ):
        installed, msg = fn(project_root)
        results.append(f"{host}: {'registered' if installed else msg}")
        if not installed and "already" not in msg:
            ok = False
    return ok, "\n".join(results)
