"""Install and inspect agent hooks for skills-mcp analyze.

Supported providers
-------------------
claude  — Claude Code Stop hook in .claude/settings.local.json (project-level).
          Claude Code already writes JSONL transcripts automatically; the hook
          just triggers ``skills-mcp analyze`` after every turn.

gemini  — Gemini CLI afterEachTurn + sessionEnd hooks in ~/.gemini/settings.json.
          Requires two hook scripts (vendored in dr_hooks/) which capture
          conversation turns to ~/.gemini-docter/transcripts/.  After capture,
          a third entry triggers ``skills-mcp analyze``.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

HOOK_COMMAND = "skills-mcp analyze"

# Claude Code settings files (project-relative)
_CLAUDE_LOCAL = ".claude/settings.local.json"
_CLAUDE_SHARED = ".claude/settings.json"

# Gemini CLI global settings
_GEMINI_SETTINGS = Path.home() / ".gemini" / "settings.json"

# Where vendored Gemini hook scripts get installed
_GEMINI_HOOKS_DIR = Path.home() / ".skills-mcp" / "hooks"

# Vendored hook scripts inside this package
_DR_HOOKS_PKG = Path(__file__).resolve().parent / "dr_hooks"


# ---------------------------------------------------------------------------
# Generic JSON helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Claude Code
# ---------------------------------------------------------------------------


def _has_claude_stop_hook(data: dict) -> bool:
    for entry in data.get("hooks", {}).get("Stop", []):
        if isinstance(entry, dict) and entry.get("command") == HOOK_COMMAND:
            return True
    return False


def claude_hook_installed(project_root: Path) -> bool:
    for name in (_CLAUDE_LOCAL, _CLAUDE_SHARED):
        if _has_claude_stop_hook(_load_json(project_root / name)):
            return True
    return False


def install_claude_hook(project_root: Path) -> tuple[bool, str]:
    """Add Stop hook to ``.claude/settings.local.json``."""
    target = project_root / _CLAUDE_LOCAL

    for name in (_CLAUDE_LOCAL, _CLAUDE_SHARED):
        if _has_claude_stop_hook(_load_json(project_root / name)):
            return False, f"already installed ({project_root / name})"

    data = _load_json(target)
    data.setdefault("hooks", {}).setdefault("Stop", []).append(
        {"type": "command", "command": HOOK_COMMAND}
    )
    try:
        _save_json(target, data)
    except OSError as exc:
        return False, f"could not write {target}: {exc}"
    return True, str(target)


# ---------------------------------------------------------------------------
# Gemini CLI
# ---------------------------------------------------------------------------

_PYTHON = sys.executable  # same interpreter that runs skills-mcp


def _gemini_hook_command(script_name: str) -> str:
    script = _GEMINI_HOOKS_DIR / script_name
    return f'"{_PYTHON}" "{script}"'


def _has_gemini_hook(data: dict, command: str) -> bool:
    for section in ("afterEachTurn", "sessionEnd"):
        for entry in data.get("hooks", {}).get(section, []):
            if isinstance(entry, dict) and entry.get("command") == command:
                return True
    return False


def gemini_hook_installed() -> bool:
    data = _load_json(_GEMINI_SETTINGS)
    after_cmd = _gemini_hook_command("after_agent.py")
    analyze_cmd = HOOK_COMMAND
    return _has_gemini_hook(data, after_cmd) or _has_gemini_hook(data, analyze_cmd)


def install_gemini_hook() -> tuple[bool, str]:
    """Install Gemini CLI hooks:
    - afterEachTurn: after_agent.py  (capture transcript)
    - afterEachTurn: session_end.py  (finalize transcript)
    - afterEachTurn: skills-mcp analyze (trigger analysis)
    """
    if not _DR_HOOKS_PKG.is_dir():
        return False, f"dr_hooks package not found at {_DR_HOOKS_PKG}"

    # Install hook scripts to ~/.skills-mcp/hooks/
    _GEMINI_HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    for script in ("after_agent.py", "session_end.py"):
        src = _DR_HOOKS_PKG / script
        dst = _GEMINI_HOOKS_DIR / script
        if not src.is_file():
            return False, f"vendored hook script missing: {src}"
        shutil.copy2(src, dst)

    data = _load_json(_GEMINI_SETTINGS)
    hooks = data.setdefault("hooks", {})
    after_each = hooks.setdefault("afterEachTurn", [])

    added: list[str] = []
    for cmd in (
        _gemini_hook_command("after_agent.py"),
        _gemini_hook_command("session_end.py"),
        HOOK_COMMAND,
    ):
        if not any(isinstance(e, dict) and e.get("command") == cmd for e in after_each):
            after_each.append({"type": "command", "command": cmd})
            added.append(cmd)

    if not added:
        return False, f"already installed ({_GEMINI_SETTINGS})"

    try:
        _save_json(_GEMINI_SETTINGS, data)
    except OSError as exc:
        return False, f"could not write {_GEMINI_SETTINGS}: {exc}"

    return True, str(_GEMINI_SETTINGS)


# ---------------------------------------------------------------------------
# Unified API (used by CLI and doctor)
# ---------------------------------------------------------------------------


def hook_installed(project_root: Path) -> bool:
    """Return True if any supported provider hook is installed."""
    return claude_hook_installed(project_root) or gemini_hook_installed()


def install_hook(project_root: Path, provider: str = "claude") -> tuple[bool, str]:
    """Install hook for ``provider``. Returns ``(ok, message)``."""
    if provider == "claude":
        return install_claude_hook(project_root)
    if provider == "gemini":
        return install_gemini_hook()
    return False, f"unknown provider '{provider}' — supported: claude, gemini"
