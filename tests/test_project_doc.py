"""Tests for Project.md read/write tools and analyze separation.

Key scenario: the MCP server is rooted at ``server_root`` (AgentMCP) but the
agent is currently working in ``ext_root`` (MyApp).  All Project.md reads and
writes must go to the external project, not the server root.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from skills_mcp.server import (
    _impl_read_project_doc,
    _impl_write_project_doc,
    _resolve_project_doc_path,
    configure_for_tests,
)


# ---------------------------------------------------------------------------
# _resolve_project_doc_path
# ---------------------------------------------------------------------------


def test_resolve_defaults_to_app_root(project_home: Path) -> None:
    from skills_mcp.server import _APP

    configure_for_tests(project_home)
    from skills_mcp.server import _APP as app

    p = _resolve_project_doc_path("", app)
    assert p == app.root / "Project.md"


def test_resolve_uses_explicit_path(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    from skills_mcp.server import _APP as app

    ext = tmp_path / "MyApp"
    ext.mkdir()
    p = _resolve_project_doc_path(str(ext), app)
    assert p == ext / "Project.md"


def test_resolve_whitespace_falls_back_to_app_root(project_home: Path) -> None:
    configure_for_tests(project_home)
    from skills_mcp.server import _APP as app

    p = _resolve_project_doc_path("   ", app)
    assert p == app.root / "Project.md"


# ---------------------------------------------------------------------------
# read_project_doc
# ---------------------------------------------------------------------------


def test_read_returns_not_found_when_missing(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    # Use an external path with no Project.md
    ext = tmp_path / "EmptyProject"
    ext.mkdir()
    result = _impl_read_project_doc(str(ext))
    assert "No Project.md" in result


def test_read_from_server_root(project_home: Path) -> None:
    configure_for_tests(project_home)
    (project_home / "Project.md").write_text("# Server project\n", encoding="utf-8")
    result = _impl_read_project_doc("")
    assert "Server project" in result


def test_read_from_external_project(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    ext = tmp_path / "MyApp"
    ext.mkdir()
    (ext / "Project.md").write_text("# MyApp context\n", encoding="utf-8")

    result = _impl_read_project_doc(str(ext))
    assert "MyApp context" in result


def test_read_external_does_not_read_server_root(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    (project_home / "Project.md").write_text("# Server root\n", encoding="utf-8")
    ext = tmp_path / "OtherApp"
    ext.mkdir()
    (ext / "Project.md").write_text("# OtherApp\n", encoding="utf-8")

    result = _impl_read_project_doc(str(ext))
    assert "OtherApp" in result
    assert "Server root" not in result


# ---------------------------------------------------------------------------
# write_project_doc
# ---------------------------------------------------------------------------


def test_write_to_server_root(project_home: Path) -> None:
    configure_for_tests(project_home)
    _impl_write_project_doc("", "# Written\n")
    assert (project_home / "Project.md").read_text(encoding="utf-8") == "# Written\n"


def test_write_to_external_project(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    # ext must be outside project_home (they share the same tmp_path base via conftest)
    ext = tmp_path / "MyApp"
    ext.mkdir()

    _impl_write_project_doc(str(ext), "# MyApp memory\n")

    assert (ext / "Project.md").read_text(encoding="utf-8") == "# MyApp memory\n"
    # server root Project.md should be the scaffolded template, not the ext content
    server_doc = (project_home / "Project.md").read_text(encoding="utf-8")
    assert "MyApp memory" not in server_doc


def test_write_creates_parent_dirs(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    ext = tmp_path / "deep" / "nested" / "Project"
    # directory doesn't exist yet — write_project_doc should create it
    _impl_write_project_doc(str(ext), "# deep\n")
    assert (ext / "Project.md").read_text(encoding="utf-8") == "# deep\n"


# ---------------------------------------------------------------------------
# analyze session filtering — external project uses its own name
# ---------------------------------------------------------------------------


def test_analyze_filters_by_external_project_name(project_home: Path, tmp_path: Path) -> None:
    """_run_analyze_inner must filter sessions by the external project's name, not app.root."""
    from skills_mcp.analyze import _run_analyze_inner
    from skills_mcp.app_state import init_app

    app = init_app(project_home)
    ext = tmp_path / "ClientProject"
    ext.mkdir()

    mock_report = MagicMock()
    mock_report.total_sessions = 0  # just need to reach the filter call

    with patch("skills_mcp.analyze.generate_report", return_value=mock_report) as mock_gen:
        _run_analyze_inner(app, project_root=ext)

    mock_gen.assert_called_once()
    call_kwargs = mock_gen.call_args
    assert call_kwargs.kwargs.get("project_filter") == "ClientProject"


def test_analyze_without_project_root_uses_app_root_name(project_home: Path) -> None:
    from skills_mcp.analyze import _run_analyze_inner
    from skills_mcp.app_state import init_app

    app = init_app(project_home)
    expected_name = project_home.name

    mock_report = MagicMock()
    mock_report.total_sessions = 0

    with patch("skills_mcp.analyze.generate_report", return_value=mock_report) as mock_gen:
        _run_analyze_inner(app)

    call_kwargs = mock_gen.call_args
    assert call_kwargs.kwargs.get("project_filter") == expected_name


# ---------------------------------------------------------------------------
# MCP instructions do NOT contain Project.md (shared server limitation)
# ---------------------------------------------------------------------------


def test_instructions_do_not_contain_project_doc(project_home: Path) -> None:
    """Project.md must NOT be baked into MCP instructions — server is shared across projects."""
    from skills_mcp.server import mcp

    (project_home / "Project.md").write_text("SECRET_SERVER_CONTEXT", encoding="utf-8")
    configure_for_tests(project_home)

    instructions = mcp._mcp_server.instructions or ""
    assert "SECRET_SERVER_CONTEXT" not in instructions


def test_instructions_contain_read_project_doc_hint(project_home: Path) -> None:
    """Instructions should tell agents to call read_project_doc at session start."""
    from skills_mcp.server import mcp

    configure_for_tests(project_home)
    instructions = mcp._mcp_server.instructions or ""
    assert "read_project_doc" in instructions
