from __future__ import annotations

import json
from pathlib import Path

import pytest

from skills_mcp.server import (
    configure_for_tests,
    get_usage_counters,
    list_skills,
    reset_runtime,
    verify_setup,
)
from skills_mcp.usage_counters import KNOWN_TOOLS, counters_path
from skills_mcp.usage_logs import append_tool_log, enforce_logs_budget, logs_root


def test_counters_increment_and_persist(project_home: Path) -> None:
    configure_for_tests(project_home)
    list_skills()
    list_skills()
    verify_setup()
    raw = get_usage_counters()
    data = json.loads(raw)
    assert data["by_tool"]["list_skills"] == 2
    assert data["by_tool"]["verify_setup"] == 1
    assert data["by_tool"]["get_usage_counters"] == 1
    assert data["total"] == sum(data["by_tool"].values())

    cp = counters_path(project_home)
    assert cp.is_file()
    disk = json.loads(cp.read_text(encoding="utf-8"))
    assert disk["by_tool"]["list_skills"] == 2


def test_all_known_tools_in_counter_schema(project_home: Path) -> None:
    configure_for_tests(project_home)
    raw = get_usage_counters()
    data = json.loads(raw)
    for name in KNOWN_TOOLS:
        assert name in data["by_tool"]


def test_logs_created_under_project(project_home: Path) -> None:
    configure_for_tests(project_home)
    verify_setup()
    logs = project_home / "state" / "logs"
    assert logs.is_dir()
    tool_logs = list(logs.rglob("blob-*.md"))
    assert len(tool_logs) >= 1


def test_enforce_logs_budget_deletes_oldest(project_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("skills_mcp.usage_logs.MAX_LOG_DIR_BYTES", 800)
    log_root = project_home / "state" / "logs"
    log_root.mkdir(parents=True, exist_ok=True)
    # Two files; budget forces dropping oldest.
    a = log_root / "a.md"
    b = log_root / "b.md"
    a.write_text("x" * 500, encoding="utf-8")
    b.write_text("y" * 500, encoding="utf-8")
    enforce_logs_budget(project_home, max_bytes=800)
    sizes = sorted((p.name, p.stat().st_size) for p in log_root.iterdir() if p.is_file())
    total = sum(sz for _n, sz in sizes)
    assert total <= 800


def test_append_tool_log_respects_budget(project_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_for_tests(project_home)
    monkeypatch.setattr("skills_mcp.usage_logs.MAX_LOG_DIR_BYTES", 1200)
    for i in range(5):
        append_tool_log(
            project_home,
            bucket_parts=("_tools", "stress"),
            tool_name="t",
            args={"i": i},
            session_note="",
            response="z" * 400,
            error=None,
        )
    total = sum(p.stat().st_size for p in (project_home / "state" / "logs").rglob("*") if p.is_file())
    assert total <= 1200


def test_ensure_logs_path_rejects_escape(project_home: Path) -> None:
    from skills_mcp.usage_logs import _ensure_under_logs

    base = logs_root(project_home)
    base.mkdir(parents=True)
    with pytest.raises(ValueError, match="escapes"):
        _ensure_under_logs(base, base.parent / "outside.md")


def test_reset_runtime_new_session_same_disk_counters(project_home: Path) -> None:
    configure_for_tests(project_home)
    list_skills()
    reset_runtime()
    configure_for_tests(project_home)
    list_skills()
    data = json.loads(get_usage_counters())
    assert data["by_tool"]["list_skills"] == 2


# --- learn_loop snapshot ---


def test_learn_loop_no_sessions(project_home: Path) -> None:
    configure_for_tests(project_home)
    data = json.loads(get_usage_counters())
    ll = data["learn_loop"]
    assert ll["sessions_total"] == 0
    assert ll["sessions_pending"] == 0
    assert ll["last_learn_pass"] is None


def test_learn_loop_pending_sessions(project_home: Path) -> None:
    sessions_dir = project_home / ".sessions"
    sessions_dir.mkdir(exist_ok=True)
    (sessions_dir / "2026-05-01-foo.md").write_text("session A", encoding="utf-8")
    (sessions_dir / "2026-05-02-bar.md").write_text("session B", encoding="utf-8")

    configure_for_tests(project_home)
    data = json.loads(get_usage_counters())
    ll = data["learn_loop"]
    assert ll["sessions_total"] == 2
    assert ll["sessions_pending"] == 2
    assert ll["last_learn_pass"] is None


def test_learn_loop_after_learn_pass(project_home: Path) -> None:
    import time

    sessions_dir = project_home / ".sessions"
    sessions_dir.mkdir(exist_ok=True)
    old_session = sessions_dir / "2026-04-01-old.md"
    old_session.write_text("old", encoding="utf-8")

    log_md = sessions_dir / "log.md"
    time.sleep(0.05)  # ensure log is strictly newer than old_session
    log_md.write_text("## learn pass 1\n\ningested: old\n", encoding="utf-8")

    time.sleep(0.05)
    new_session = sessions_dir / "2026-05-14-new.md"
    new_session.write_text("new", encoding="utf-8")

    configure_for_tests(project_home)
    data = json.loads(get_usage_counters())
    ll = data["learn_loop"]
    assert ll["sessions_total"] == 2
    assert ll["sessions_pending"] == 1  # only new_session is after log_md
    assert ll["last_learn_pass"] is not None
