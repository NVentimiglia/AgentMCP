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
    root_path = str(project_root.resolve())
    return {
        "command": sys.executable,
        "args": ["-m", "skills_mcp", "serve", "--root", root_path],
        "env": {"SKILLS_MCP_ROOT": root_path},
    }


def _register_host(settings_path: Path, project_root: Path) -> tuple[bool, str]:
    """Generic registration logic for any host."""
    data = _load_json(settings_path)
    servers = data.setdefault("mcpServers", {})
    entry = _server_entry(project_root)

    if _SERVER_KEY in servers:
        existing = servers[_SERVER_KEY]
        # If the registration is identical, skip to avoid unnecessary writes
        if (
            existing.get("command") == entry["command"]
            and existing.get("args") == entry["args"]
            and existing.get("env", {}).get("SKILLS_MCP_ROOT") == entry["env"]["SKILLS_MCP_ROOT"]
        ):
            return False, f"already registered ({settings_path})"

    servers[_SERVER_KEY] = entry
    try:
        _save_json(settings_path, data)
    except OSError as exc:
        return False, f"could not write {settings_path}: {exc}"
    return True, str(settings_path)


# ---------------------------------------------------------------------------
# Claude Code  (~/.claude/settings.json)
# ---------------------------------------------------------------------------

_CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"


def claude_registered() -> bool:
    data = _load_json(_CLAUDE_SETTINGS)
    return _SERVER_KEY in (data.get("mcpServers") or {})


def register_claude(project_root: Path) -> tuple[bool, str]:
    return _register_host(_CLAUDE_SETTINGS, project_root)


# ---------------------------------------------------------------------------
# Cursor  (~/.cursor/mcp.json)
# ---------------------------------------------------------------------------

_CURSOR_SETTINGS = Path.home() / ".cursor" / "mcp.json"


def cursor_registered() -> bool:
    data = _load_json(_CURSOR_SETTINGS)
    return _SERVER_KEY in (data.get("mcpServers") or {})


def register_cursor(project_root: Path) -> tuple[bool, str]:
    return _register_host(_CURSOR_SETTINGS, project_root)


# ---------------------------------------------------------------------------
# Gemini CLI  (~/.gemini/settings.json)
# ---------------------------------------------------------------------------

_GEMINI_SETTINGS = Path.home() / ".gemini" / "settings.json"


def gemini_registered() -> bool:
    data = _load_json(_GEMINI_SETTINGS)
    return _SERVER_KEY in (data.get("mcpServers") or {})


def register_gemini(project_root: Path) -> tuple[bool, str]:
    return _register_host(_GEMINI_SETTINGS, project_root)


# ---------------------------------------------------------------------------
# Antigravity  (~/.antigravity/mcp.json)  — Google IDE
# ---------------------------------------------------------------------------

_ANTIGRAVITY_SETTINGS = Path.home() / ".antigravity" / "mcp.json"

# Antigravity also reads from ~/.gemini/antigravity/mcp_config.json
_ANTIGRAVITY_GEMINI_SETTINGS = Path.home() / ".gemini" / "antigravity" / "mcp_config.json"


def antigravity_registered() -> bool:
    data = _load_json(_ANTIGRAVITY_SETTINGS)
    data2 = _load_json(_ANTIGRAVITY_GEMINI_SETTINGS)
    return _SERVER_KEY in (data.get("mcpServers") or {}) or _SERVER_KEY in (data2.get("mcpServers") or {})


def register_antigravity(project_root: Path) -> tuple[bool, str]:
    ok1, msg1 = _register_host(_ANTIGRAVITY_SETTINGS, project_root)
    ok2, msg2 = _register_host(_ANTIGRAVITY_GEMINI_SETTINGS, project_root)
    ok = ok1 or ok2
    msg = "; ".join(m for m in [msg1, msg2] if m)
    return ok, msg


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
