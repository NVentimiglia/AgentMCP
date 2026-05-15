"""Tests for skills-mcp analyze (vendored gemini-docter integration)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from skills_mcp.analyze import _read_existing_version, _render_rule, run_analyze
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
# Analysis with mocked generate_report
# ---------------------------------------------------------------------------


def test_analyze_no_sessions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path, monkeypatch)
    app = init_app(root)

    with patch("skills_mcp.analyze.generate_report", return_value=_fake_report(sessions=0)):
        rc = run_analyze(app)

    assert rc == 0
    assert list((root / "rules").glob("dr-*.md")) == []


def test_analyze_no_signals(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path, monkeypatch)
    app = init_app(root)

    with patch("skills_mcp.analyze.generate_report", return_value=_fake_report(sessions=2, signals=[])):
        rc = run_analyze(app)

    assert rc == 0
    assert list((root / "rules").glob("dr-*.md")) == []


def test_analyze_writes_rule_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
    rules_dir = root / "rules"
    assert (rules_dir / "dr-correction-heavy.md").is_file()
    assert (rules_dir / "dr-error-loop.md").is_file()


def test_analyze_rule_frontmatter_valid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path, monkeypatch)
    app = init_app(root)

    signals = [_fake_signal("edit-thrashing", "medium", ["wrote login.py 6 times"])]
    with (
        patch("skills_mcp.analyze.generate_report", return_value=_fake_report(sessions=1, signals=signals)),
        patch("skills_mcp.analyze.subprocess.run", return_value=MagicMock(stdout="", returncode=0)),
    ):
        run_analyze(app)

    from skills_mcp.rules.loader import parse_rule_md
    parsed = parse_rule_md(root / "rules" / "dr-edit-thrashing.md")
    assert parsed.fm.id == "dr-edit-thrashing"
    assert parsed.fm.version == "1"
    assert "edit" in parsed.fm.trigger.lower()
    assert parsed.fm.solution


def test_analyze_version_increments_on_rerun(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path, monkeypatch)
    app = init_app(root)
    # Disable cooldown so two back-to-back runs are both allowed.
    monkeypatch.setattr("skills_mcp.analyze.ANALYZE_COOLDOWN_SECONDS", 0)

    signals = [_fake_signal("keep-going-loop", "medium")]
    with (
        patch("skills_mcp.analyze.generate_report", return_value=_fake_report(sessions=2, signals=signals)),
        patch("skills_mcp.analyze.subprocess.run", return_value=MagicMock(stdout="", returncode=0)),
    ):
        run_analyze(app)
        run_analyze(app)

    from skills_mcp.rules.loader import parse_rule_md
    parsed = parse_rule_md(root / "rules" / "dr-keep-going-loop.md")
    assert parsed.fm.version == "2"


def test_analyze_unknown_signal_gets_fallback_rule(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _make_project(tmp_path, monkeypatch)
    app = init_app(root)

    signals = [_fake_signal("some-future-signal", "low")]
    with (
        patch("skills_mcp.analyze.generate_report", return_value=_fake_report(sessions=1, signals=signals)),
        patch("skills_mcp.analyze.subprocess.run", return_value=MagicMock(stdout="", returncode=0)),
    ):
        run_analyze(app)

    from skills_mcp.rules.loader import parse_rule_md
    parsed = parse_rule_md(root / "rules" / "dr-some-future-signal.md")
    assert parsed.fm.id == "dr-some-future-signal"
    assert parsed.fm.solution  # fallback text present


def test_analyze_git_diff_shown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    root = _make_project(tmp_path, monkeypatch)
    app = init_app(root)

    signals = [_fake_signal("correction-heavy", "high")]
    fake_diff = MagicMock(stdout="+++ b/rules/dr-correction-heavy.md\n+new content", returncode=0)
    fake_status = MagicMock(stdout="", returncode=0)

    with (
        patch("skills_mcp.analyze.generate_report", return_value=_fake_report(sessions=3, signals=signals)),
        patch("skills_mcp.analyze.subprocess.run", side_effect=[fake_diff, fake_status]),
    ):
        run_analyze(app)

    captured = capsys.readouterr()
    assert "git diff rules/" in captured.out
    assert "dr-correction-heavy" in captured.out


# ---------------------------------------------------------------------------
# Unit tests for helpers
# ---------------------------------------------------------------------------


def test_read_existing_version_missing(tmp_path: Path) -> None:
    assert _read_existing_version(tmp_path / "nope.md") == 0


def test_read_existing_version_from_file(tmp_path: Path) -> None:
    p = tmp_path / "rule.md"
    p.write_text('---\nid: x\nversion: "3"\ntrigger: t\nsolution: s\n---\n', encoding="utf-8")
    assert _read_existing_version(p) == 3


def test_render_rule_parseable(tmp_path: Path) -> None:
    content = _render_rule(
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
