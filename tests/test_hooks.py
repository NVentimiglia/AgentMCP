"""Tests for agent hook install/detect (Claude Code and Gemini)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from skills_mcp.hooks import (
    HOOK_COMMAND,
    _CLAUDE_LOCAL,
    _CLAUDE_SHARED,
    claude_hook_installed,
    gemini_hook_installed,
    hook_installed,
    install_hook,
)


# ---------------------------------------------------------------------------
# Claude Code hooks
# ---------------------------------------------------------------------------


def test_claude_install_writes_stop_hook(tmp_path: Path) -> None:
    ok, msg = install_hook(tmp_path, provider="claude")
    assert ok
    target = tmp_path / _CLAUDE_LOCAL
    assert target.is_file()
    data = json.loads(target.read_text(encoding="utf-8"))
    assert any(e.get("command") == HOOK_COMMAND for e in data["hooks"]["Stop"])


def test_claude_install_idempotent(tmp_path: Path) -> None:
    install_hook(tmp_path, provider="claude")
    ok, msg = install_hook(tmp_path, provider="claude")
    assert not ok
    assert "already installed" in msg
    data = json.loads((tmp_path / _CLAUDE_LOCAL).read_text(encoding="utf-8"))
    assert sum(1 for e in data["hooks"]["Stop"] if e.get("command") == HOOK_COMMAND) == 1


def test_claude_install_merges_existing_settings(tmp_path: Path) -> None:
    target = tmp_path / _CLAUDE_LOCAL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"permissions": {"allow": ["Bash(ls)"]}}), encoding="utf-8")

    install_hook(tmp_path, provider="claude")
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["permissions"]["allow"] == ["Bash(ls)"]
    assert any(e.get("command") == HOOK_COMMAND for e in data["hooks"]["Stop"])


def test_claude_hook_installed_detects_local(tmp_path: Path) -> None:
    assert not claude_hook_installed(tmp_path)
    install_hook(tmp_path, provider="claude")
    assert claude_hook_installed(tmp_path)


def test_claude_hook_installed_detects_shared(tmp_path: Path) -> None:
    shared = tmp_path / _CLAUDE_SHARED
    shared.parent.mkdir(parents=True, exist_ok=True)
    shared.write_text(
        json.dumps({"hooks": {"Stop": [{"type": "command", "command": HOOK_COMMAND}]}}),
        encoding="utf-8",
    )
    assert claude_hook_installed(tmp_path)


# ---------------------------------------------------------------------------
# Gemini hooks
# ---------------------------------------------------------------------------


def test_gemini_install_writes_settings(tmp_path: Path) -> None:
    fake_settings = tmp_path / "gemini_settings.json"
    hooks_dir = tmp_path / "hooks"

    with (
        patch("skills_mcp.hooks._GEMINI_SETTINGS", fake_settings),
        patch("skills_mcp.hooks._GEMINI_HOOKS_DIR", hooks_dir),
    ):
        ok, msg = install_hook(tmp_path, provider="gemini")

    assert ok, msg
    assert fake_settings.is_file()
    data = json.loads(fake_settings.read_text(encoding="utf-8"))
    commands = [e.get("command", "") for e in data["hooks"]["afterEachTurn"]]
    assert any("after_agent.py" in c for c in commands)
    assert any("session_end.py" in c for c in commands)
    assert any(c == HOOK_COMMAND for c in commands)
    # Scripts copied to hooks dir
    assert (hooks_dir / "after_agent.py").is_file()
    assert (hooks_dir / "session_end.py").is_file()


def test_gemini_install_idempotent(tmp_path: Path) -> None:
    fake_settings = tmp_path / "gemini_settings.json"
    hooks_dir = tmp_path / "hooks"

    with (
        patch("skills_mcp.hooks._GEMINI_SETTINGS", fake_settings),
        patch("skills_mcp.hooks._GEMINI_HOOKS_DIR", hooks_dir),
    ):
        install_hook(tmp_path, provider="gemini")
        ok, msg = install_hook(tmp_path, provider="gemini")

    assert not ok
    assert "already installed" in msg


def test_gemini_hook_installed_detects(tmp_path: Path) -> None:
    fake_settings = tmp_path / "gemini_settings.json"
    hooks_dir = tmp_path / "hooks"

    with (
        patch("skills_mcp.hooks._GEMINI_SETTINGS", fake_settings),
        patch("skills_mcp.hooks._GEMINI_HOOKS_DIR", hooks_dir),
    ):
        assert not gemini_hook_installed()
        install_hook(tmp_path, provider="gemini")
        assert gemini_hook_installed()


# ---------------------------------------------------------------------------
# Unified hook_installed
# ---------------------------------------------------------------------------


def test_hook_installed_true_if_claude_present(tmp_path: Path) -> None:
    install_hook(tmp_path, provider="claude")
    assert hook_installed(tmp_path)


def test_hook_installed_unknown_provider(tmp_path: Path) -> None:
    ok, msg = install_hook(tmp_path, provider="cursor")
    assert not ok
    assert "unknown provider" in msg
