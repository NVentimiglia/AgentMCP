"""Tests for skills-mcp analyze (vendored gemini-docter integration)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from skills_mcp.analyze import _read_existing_version, _render_memory_rule, memory_dir, run_analyze
from skills_mcp.app_state import init_app
from skills_mcp.cli import cmd_init

_TEST_CONFIG = """\
[paths]
skills = "skills"
rules = "rules"
"""


def _make_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("SKILLS_MCP_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    cmd_init(tmp_path)
    (tmp_path / "config.toml").write_text(_TEST_CONFIG, encoding="utf-8")
    return tmp_path


def _fake_signal(name: str, severity: str = "high", examples: list[str] | None = None):
    sig = MagicMock()
    sig.signal_name = name
    sig.severity = severity
    sig.examples = examples or []
    return sig


def _fake_report(sessions: int = 3, signals=None):
    report = MagicMock()
    report.total_sessions = sessions
    report.top_signals = signals or []
    return report


# ---------------------------------------------------------------------------
# analyze writes to .memory/, never to rules/
# ---------------------------------------------------------------------------


def test_analyze_no_sessions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path, monkeypatch)
    app = init_app(root)

    with patch("skills_mcp.analyze.generate_report", return_value=_fake_report(sessions=0)):
        rc = run_analyze(app)

    assert rc == 0
    assert not memory_dir(root).exists() or list(memory_dir(root).glob("dr-*.md")) == []
    assert list((root / "rules").glob("dr-*.md")) == []


def test_analyze_no_signals(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path, monkeypatch)
    app = init_app(root)

    with patch("skills_mcp.analyze.generate_report", return_value=_fake_report(sessions=2, signals=[])):
        rc = run_analyze(app)

    assert rc == 0
    assert list((root / "rules").glob("dr-*.md")) == []


def test_analyze_writes_to_memory_not_rules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path, monkeypatch)
    app = init_app(root)

    signals = [
        _fake_signal("correction-heavy", "high", ["no that's wrong"]),
        _fake_signal("error-loop", "critical"),
    ]
    with (
        patch("skills_mcp.analyze.generate_report", return_value=_fake_report(sessions=5, signals=signals)),
        patch("skills_mcp.analyze.subprocess.run", return_value=MagicMock(stdout="", returncode=0)),
    ):
        rc = run_analyze(app)

    assert rc == 0
    mem = memory_dir(root)
    assert (mem / "dr-correction-heavy.md").is_file()
    assert (mem / "dr-error-loop.md").is_file()
    # must NOT appear in rules/
    assert not (root / "rules" / "dr-correction-heavy.md").exists()
    assert not (root / "rules" / "dr-error-loop.md").exists()


def test_analyze_memory_frontmatter_valid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path, monkeypatch)
    app = init_app(root)

    signals = [_fake_signal("edit-thrashing", "medium", ["wrote login.py 6 times"])]
    with (
        patch("skills_mcp.analyze.generate_report", return_value=_fake_report(sessions=1, signals=signals)),
        patch("skills_mcp.analyze.subprocess.run", return_value=MagicMock(stdout="", returncode=0)),
    ):
        run_analyze(app)

    from skills_mcp.rules.loader import parse_rule_md
    parsed = parse_rule_md(memory_dir(root) / "dr-edit-thrashing.md")
    assert parsed.fm.id == "dr-edit-thrashing"
    assert parsed.fm.version == "1"
    assert "edit" in parsed.fm.trigger.lower()
    assert parsed.fm.solution


def test_analyze_version_increments_on_rerun(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path, monkeypatch)
    app = init_app(root)
    monkeypatch.setattr("skills_mcp.analyze.ANALYZE_COOLDOWN_SECONDS", 0)

    signals = [_fake_signal("keep-going-loop", "medium")]
    with (
        patch("skills_mcp.analyze.generate_report", return_value=_fake_report(sessions=2, signals=signals)),
        patch("skills_mcp.analyze.subprocess.run", return_value=MagicMock(stdout="", returncode=0)),
    ):
        run_analyze(app)
        run_analyze(app)

    from skills_mcp.rules.loader import parse_rule_md
    parsed = parse_rule_md(memory_dir(root) / "dr-keep-going-loop.md")
    assert parsed.fm.version == "2"


def test_analyze_unknown_signal_gets_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path, monkeypatch)
    app = init_app(root)

    signals = [_fake_signal("some-future-signal", "low")]
    with (
        patch("skills_mcp.analyze.generate_report", return_value=_fake_report(sessions=1, signals=signals)),
        patch("skills_mcp.analyze.subprocess.run", return_value=MagicMock(stdout="", returncode=0)),
    ):
        run_analyze(app)

    from skills_mcp.rules.loader import parse_rule_md
    parsed = parse_rule_md(memory_dir(root) / "dr-some-future-signal.md")
    assert parsed.fm.id == "dr-some-future-signal"
    assert parsed.fm.solution


def test_analyze_git_diff_shown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    root = _make_project(tmp_path, monkeypatch)
    app = init_app(root)

    signals = [_fake_signal("correction-heavy", "high")]
    fake_diff = MagicMock(stdout="+++ b/.memory/dr-correction-heavy.md\n+new content", returncode=0)
    fake_status = MagicMock(stdout="", returncode=0)

    with (
        patch("skills_mcp.analyze.generate_report", return_value=_fake_report(sessions=3, signals=signals)),
        patch("skills_mcp.analyze.subprocess.run", side_effect=[fake_diff, fake_status]),
    ):
        run_analyze(app)

    captured = capsys.readouterr()
    assert ".memory/" in captured.out
    assert "dr-correction-heavy" in captured.out


def test_analyze_external_project_writes_to_its_memory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """analyze with project_root writes to that project's .memory/, not app.root."""
    server_root = tmp_path / "AgentMCP"
    server_root.mkdir()
    ext_root = tmp_path / "MyApp"
    ext_root.mkdir()

    monkeypatch.setenv("SKILLS_MCP_ROOT", str(server_root))
    monkeypatch.chdir(server_root)
    cmd_init(server_root)
    (server_root / "config.toml").write_text(_TEST_CONFIG, encoding="utf-8")
    app = init_app(server_root)

    signals = [_fake_signal("error-loop", "high")]
    with (
        patch("skills_mcp.analyze.generate_report", return_value=_fake_report(sessions=2, signals=signals)),
        patch("skills_mcp.analyze.subprocess.run", return_value=MagicMock(stdout="", returncode=0)),
    ):
        run_analyze(app, project_root=ext_root)

    assert (memory_dir(ext_root) / "dr-error-loop.md").is_file()
    assert not memory_dir(server_root).exists() or not (memory_dir(server_root) / "dr-error-loop.md").exists()


# ---------------------------------------------------------------------------
# Unit tests for helpers
# ---------------------------------------------------------------------------


def test_read_existing_version_missing(tmp_path: Path) -> None:
    assert _read_existing_version(tmp_path / "nope.md") == 0


def test_read_existing_version_from_file(tmp_path: Path) -> None:
    p = tmp_path / "rule.md"
    p.write_text('---\nid: x\nversion: "3"\ntrigger: t\nsolution: s\n---\n', encoding="utf-8")
    assert _read_existing_version(p) == 3


def test_render_memory_rule_parseable(tmp_path: Path) -> None:
    content = _render_memory_rule(
        rule_id="dr-correction-heavy",
        version=1,
        trigger="user corrects agent frequently",
        solution="Stop and re-read user message.",
        signal_name="correction-heavy",
        count=2,
        severities=["high"],
        examples=["no that's wrong"],
        sessions_analyzed=4,
        generated_at="2026-05-14T00:00:00Z",
    )
    p = tmp_path / "rule.md"
    p.write_text(content, encoding="utf-8")

    from skills_mcp.rules.loader import parse_rule_md
    parsed = parse_rule_md(p)
    assert parsed.fm.id == "dr-correction-heavy"
    assert parsed.fm.version == "1"
