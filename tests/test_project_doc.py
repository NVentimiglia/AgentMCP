"""Tests for .memory/ read/write/list tools and project separation.

The MCP server lives at ``server_root`` (AgentMCP) but the agent works in
``ext_root`` (MyApp).  All .memory/ reads and writes must go to the calling
project, not the server root.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from skills_mcp.server import (
    _impl_list_memory,
    _impl_read_memory,
    _impl_write_memory,
    _resolve_memory_dir,
    configure_for_tests,
)


# ---------------------------------------------------------------------------
# _resolve_memory_dir
# ---------------------------------------------------------------------------


def test_resolve_defaults_to_app_root(project_home: Path) -> None:
    configure_for_tests(project_home)
    from skills_mcp.server import _APP as app

    d = _resolve_memory_dir("", app)
    assert d == app.root / ".memory"


def test_resolve_uses_explicit_path(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    from skills_mcp.server import _APP as app

    ext = tmp_path / "MyApp"
    ext.mkdir()
    d = _resolve_memory_dir(str(ext), app)
    assert d == ext / ".memory"


def test_resolve_whitespace_falls_back_to_app_root(project_home: Path) -> None:
    configure_for_tests(project_home)
    from skills_mcp.server import _APP as app

    d = _resolve_memory_dir("   ", app)
    assert d == app.root / ".memory"


# ---------------------------------------------------------------------------
# list_memory
# ---------------------------------------------------------------------------


def test_list_memory_empty_when_no_dir(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    ext = tmp_path / "EmptyProject"
    ext.mkdir()
    result = _impl_list_memory(str(ext))
    assert result == "[]"


def test_list_memory_returns_md_files(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    ext = tmp_path / "MyApp"
    mem = ext / ".memory"
    mem.mkdir(parents=True)
    (mem / "decisions.md").write_text("# Decisions\n", encoding="utf-8")
    (mem / "dr-error-loop.md").write_text("# Error\n", encoding="utf-8")

    import json
    result = json.loads(_impl_list_memory(str(ext)))
    assert "decisions.md" in result
    assert "dr-error-loop.md" in result


# ---------------------------------------------------------------------------
# read_memory
# ---------------------------------------------------------------------------


def test_read_memory_not_found(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    ext = tmp_path / "EmptyProject"
    ext.mkdir()
    result = _impl_read_memory(str(ext), "decisions")
    assert "No memory file" in result


def test_read_memory_from_external_project(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    ext = tmp_path / "MyApp"
    mem = ext / ".memory"
    mem.mkdir(parents=True)
    (mem / "context.md").write_text("# MyApp context\n", encoding="utf-8")

    result = _impl_read_memory(str(ext), "context")
    assert "MyApp context" in result


def test_read_memory_auto_appends_md_extension(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    ext = tmp_path / "MyApp"
    mem = ext / ".memory"
    mem.mkdir(parents=True)
    (mem / "notes.md").write_text("hello\n", encoding="utf-8")

    assert "hello" in _impl_read_memory(str(ext), "notes")
    assert "hello" in _impl_read_memory(str(ext), "notes.md")


def test_read_memory_does_not_read_server_root(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    server_mem = project_home / ".memory"
    server_mem.mkdir(parents=True)
    (server_mem / "context.md").write_text("# Server root\n", encoding="utf-8")

    ext = tmp_path / "OtherApp"
    ext.mkdir()
    (ext / ".memory").mkdir()
    (ext / ".memory" / "context.md").write_text("# OtherApp\n", encoding="utf-8")

    result = _impl_read_memory(str(ext), "context")
    assert "OtherApp" in result
    assert "Server root" not in result


# ---------------------------------------------------------------------------
# write_memory
# ---------------------------------------------------------------------------


def test_write_memory_to_external_project(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    ext = tmp_path / "MyApp"
    ext.mkdir()

    _impl_write_memory(str(ext), "decisions", "# Decisions\nUse postgres.\n")

    assert (ext / ".memory" / "decisions.md").read_text(encoding="utf-8") == "# Decisions\nUse postgres.\n"


def test_write_memory_does_not_touch_server_root(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    ext = tmp_path / "MyApp"
    ext.mkdir()

    _impl_write_memory(str(ext), "notes", "ext content")

    assert not (project_home / ".memory" / "notes.md").exists()


def test_write_memory_creates_memory_dir(project_home: Path, tmp_path: Path) -> None:
    configure_for_tests(project_home)
    ext = tmp_path / "BrandNew"
    ext.mkdir()

    _impl_write_memory(str(ext), "context", "# Hello\n")

    assert (ext / ".memory" / "context.md").is_file()


# ---------------------------------------------------------------------------
# Analyze session filtering uses external project name
# ---------------------------------------------------------------------------


def test_analyze_filters_by_external_project_name(project_home: Path, tmp_path: Path) -> None:
    from skills_mcp.analyze import _run_analyze_inner
    from skills_mcp.app_state import init_app

    app = init_app(project_home)
    ext = tmp_path / "ClientProject"
    ext.mkdir()

    mock_report = MagicMock()
    mock_report.total_sessions = 0

    with patch("skills_mcp.analyze.generate_report", return_value=mock_report) as mock_gen:
        _run_analyze_inner(app, project_root=ext)

    assert mock_gen.call_args.kwargs.get("project_filter") == "ClientProject"


def test_analyze_without_project_root_uses_app_root_name(project_home: Path) -> None:
    from skills_mcp.analyze import _run_analyze_inner
    from skills_mcp.app_state import init_app

    app = init_app(project_home)
    mock_report = MagicMock()
    mock_report.total_sessions = 0

    with patch("skills_mcp.analyze.generate_report", return_value=mock_report) as mock_gen:
        _run_analyze_inner(app)

    assert mock_gen.call_args.kwargs.get("project_filter") == project_home.name


# ---------------------------------------------------------------------------
# MCP instructions contain memory ritual hint, not project-specific content
# ---------------------------------------------------------------------------


def test_instructions_contain_memory_hint(project_home: Path) -> None:
    from skills_mcp.server import mcp
    configure_for_tests(project_home)
    instructions = mcp._mcp_server.instructions or ""
    assert "list_memory" in instructions
    assert "write_memory" in instructions
