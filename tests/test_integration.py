"""Integration tests for SkillMCP.

Run with: pytest tests/test_integration.py -m integration

These tests spin up a real MCP server and connect with an MCP client.
They require a full project installation (uv sync).
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.integration
def test_mcp_server_serves_list_skills(project_home: Path) -> None:
    """Real FastMCP server responds to list_skills."""
    pytest.importorskip("mcp")

    from skills_mcp.server import configure_for_tests, list_skills
    import json

    configure_for_tests(project_home)
    result = json.loads(list_skills())
    assert isinstance(result, list)


@pytest.mark.integration
def test_mcp_server_serves_read_skill(project_home: Path) -> None:
    """Real FastMCP server responds to read_skill for an existing skill."""
    pytest.importorskip("mcp")

    from skills_mcp.server import configure_for_tests, list_skills, read_skill
    import json

    configure_for_tests(project_home)
    skills = json.loads(list_skills())
    if not skills:
        pytest.skip("no skills in project_home")
    result = read_skill(skills[0]["name"])
    assert result
