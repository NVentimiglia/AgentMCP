"""Shared fixtures for SkillMCP tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from skills_mcp.cli import cmd_init


@pytest.fixture(autouse=True)
def _reset_runtime_between_tests():
    yield
    from skills_mcp.server import reset_runtime

    reset_runtime()


_TEST_CONFIG = """\
skill_folders = [".agents/skills"]
"""


@pytest.fixture()
def project_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("SKILLS_MCP_ROOT", raising=False)
    monkeypatch.setenv("SKILLS_MCP_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    # Redirect all MCP registration writes to tmp_path so cmd_init never
    # touches the real user settings files (~/.claude/settings.json etc.).
    monkeypatch.setattr("skills_mcp.mcp_registration._CLAUDE_SETTINGS",
                        tmp_path / ".claude" / "settings.json")
    monkeypatch.setattr("skills_mcp.mcp_registration._CURSOR_SETTINGS",
                        tmp_path / ".cursor" / "mcp.json")
    monkeypatch.setattr("skills_mcp.mcp_registration._GEMINI_SETTINGS",
                        tmp_path / ".gemini" / "settings.json")
    monkeypatch.setattr("skills_mcp.mcp_registration._ANTIGRAVITY_SETTINGS",
                        tmp_path / ".antigravity" / "mcp.json")
    monkeypatch.setattr("skills_mcp.mcp_registration._ANTIGRAVITY_GEMINI_SETTINGS",
                        tmp_path / ".gemini" / "antigravity" / "mcp_config.json")

    cmd_init(tmp_path)

    (tmp_path / "skillmcp.toml").write_text(_TEST_CONFIG, encoding="utf-8")

    return tmp_path
