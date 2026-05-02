from __future__ import annotations

from pathlib import Path

import pytest

from agent_mcp.app_state import get_app
from agent_mcp.paths import CONFIG_NAME
from agent_mcp.rules.loader import ActiveRuleIndex
from agent_mcp.rules.service import RulesService
from agent_mcp.server import configure_for_tests


def _services(project_home: Path):
    configure_for_tests(project_home)
    app = get_app()
    idx = ActiveRuleIndex(app.rules_active_dir)
    idx.reload()
    svc = RulesService(app, idx)
    return app, svc, idx


def test_proposal_mode_writes_proposals_not_active(project_home) -> None:
    app, svc, _ = _services(project_home)
    assert app.config.mode.rules == "proposal"

    out = svc.propose_rule_md(
        trigger="always run pytest short",
        solution="pytest --tb=short",
        source_session_id="test",
    )
    assert out["mode"] == "proposal"
    rel = Path(out["path"].replace("\\", "/"))
    assert rel.parts[1] == "proposals"


def test_promote_moves_into_active(project_home) -> None:
    app, svc, idx = _services(project_home)

    svc.propose_rule_md(
        trigger="lint before commit",
        solution="run ruff",
        source_session_id="test",
    )
    md_files = sorted((app.rules_proposals_dir).glob("*.md"))
    assert md_files

    changelog = svc.promote_rule(filename=md_files[0].name)["changelog_id"]
    assert changelog
    assert (app.rules_active_dir / md_files[0].name).exists()
    assert not (app.rules_proposals_dir / md_files[0].name).exists()
    idx.reload()
    ids = idx.list_ids_triggers()
    assert ids


def test_rollback_promote_restore(project_home) -> None:
    app, svc, idx = _services(project_home)

    svc.propose_rule_md(
        trigger="rollback-demo",
        solution="nothing",
        source_session_id="test",
    )
    md_files = sorted((app.rules_proposals_dir).glob("*.md"))
    content_before = md_files[0].read_bytes()
    changelog_id = svc.promote_rule(filename=md_files[0].name)["changelog_id"]

    svc.rollback_rule(changelog_id=changelog_id)

    restored = sorted((app.rules_proposals_dir).glob("*.md"))
    assert restored
    rt = restored[0].read_text(encoding="utf-8").replace("\r\n", "\n")
    cb = content_before.decode("utf-8").replace("\r\n", "\n")
    assert "rollback-demo" in rt and "---" in rt
    assert "rollback-demo" in cb


def test_auto_daily_cap_fallback_to_proposals(project_home) -> None:
    txt = Path(project_home / CONFIG_NAME).read_text(encoding="utf-8")
    txt = txt.replace('rules = "proposal"', 'rules = "auto"')
    txt = txt.replace("max_auto_promotions_per_day = 5", "max_auto_promotions_per_day = 1")
    Path(project_home / CONFIG_NAME).write_text(txt, encoding="utf-8")

    configure_for_tests(project_home)
    app = get_app()
    idx = ActiveRuleIndex(app.rules_active_dir)
    idx.reload()
    svc = RulesService(app, idx)

    first = svc.propose_rule_md(trigger="cap-a", solution="sa", source_session_id="t")
    assert first["mode"] == "auto"

    second = svc.propose_rule_md(trigger="cap-b", solution="sb", source_session_id="t")
    assert second["mode"] == "proposal"
