from __future__ import annotations

from pathlib import Path

from skills_mcp.app_state import get_app
from skills_mcp.rules.loader import ActiveRuleIndex
from skills_mcp.rules.service import RulesService
from skills_mcp.server import configure_for_tests


def _services(project_home: Path):
    configure_for_tests(project_home)
    app = get_app()
    idx = ActiveRuleIndex(app.rules_dir)
    idx.reload()
    svc = RulesService(app, idx)
    return app, svc, idx


def test_propose_rule_writes_flat_rules_dir(project_home) -> None:
    _, svc, _ = _services(project_home)

    out = svc.propose_rule_md(
        trigger="always run pytest short",
        solution="pytest --tb=short",
        source_session_id="test",
    )
    path_norm = str(out["path"]).replace("\\", "/")
    assert path_norm.startswith("rules/")
    app = get_app()
    assert (app.rules_dir / Path(path_norm).name).is_file()


def test_propose_reload_makes_rule_visible(project_home) -> None:
    app, svc, idx = _services(project_home)

    svc.propose_rule_md(
        trigger="lint before commit",
        solution="run ruff",
        source_session_id="test",
    )
    md_files = sorted(app.rules_dir.glob("*.md"))
    assert md_files
    idx.reload()
    ids = idx.list_ids_triggers()
    assert ids


def test_propose_duplicate_slug_overwrites(project_home) -> None:
    app, svc, _ = _services(project_home)
    trig = "unique trigger slug xyz"
    svc.propose_rule_md(trigger=trig, solution="a", source_session_id="t")
    n1 = len(list(app.rules_dir.glob("*.md")))
    svc.propose_rule_md(trigger=trig, solution="b", source_session_id="t")
    n2 = len(list(app.rules_dir.glob("*.md")))
    assert n1 == n2
