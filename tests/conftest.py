"""Shared fixtures for SkillsMCP tests."""

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
[paths]
skills = "skills"
rules = "rules"
"""


@pytest.fixture()
def project_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("SKILLS_MCP_ROOT", raising=False)
    monkeypatch.setenv("SKILLS_MCP_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    cmd_init(tmp_path)

    (tmp_path / "config.toml").write_text(_TEST_CONFIG, encoding="utf-8")

    return tmp_path
