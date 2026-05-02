from __future__ import annotations

from agent_mcp.memory.store import MemoryStore
from agent_mcp.problems import handle_flag_problem
from agent_mcp.rules.loader import ActiveRuleIndex
from agent_mcp.rules.service import RulesService
from agent_mcp.server import configure_for_tests, reset_runtime


def _stack(project_home):
    configure_for_tests(project_home)
    from agent_mcp.app_state import get_app

    app = get_app()
    mem = MemoryStore.from_app()
    idx = ActiveRuleIndex(app.rules_active_dir)
    idx.reload()
    rules = RulesService(app, idx)
    return app, mem, rules


def test_recurring_problem_proposes_once(project_home) -> None:
    app, mem, rules = _stack(project_home)

    msg = "flaky oauth timeout in CI retry loop"
    for _ in range(2):
        r = handle_flag_problem(
            description=msg,
            context="",
            memory=mem,
            rules_svc=rules,
            source_session_id="s1",
        )
        assert not r["proposal"]

    r3 = handle_flag_problem(description=msg, context="", memory=mem, rules_svc=rules, source_session_id="s1")
    assert r3["recurrence_hit"]
    assert r3["proposal"] and r3["proposal"].get("path")

    r4 = handle_flag_problem(description=msg, context="", memory=mem, rules_svc=rules, source_session_id="s1")
    assert not r4["proposal"]


def test_unrelated_reports_no_proposal(project_home) -> None:
    _, mem, rules = _stack(project_home)
    for i in range(5):
        r = handle_flag_problem(
            description=f"totally different issue xyz{i}",
            context="ZZZ_UNIQUE_PREFIX",
            memory=mem,
            rules_svc=rules,
            source_session_id="s2",
        )
        assert not r["proposal"]


def test_cluster_persistence_across_restart(project_home) -> None:
    app, mem, rules = _stack(project_home)

    msg = "database migration fails on SQLite windows"
    for _ in range(2):
        handle_flag_problem(
            description=msg,
            context="",
            memory=mem,
            rules_svc=rules,
            source_session_id="s3",
        )

    reset_runtime()
    configure_for_tests(project_home)

    from agent_mcp.app_state import get_app

    app = get_app()
    mem = MemoryStore.from_app()
    idx = ActiveRuleIndex(app.rules_active_dir)
    idx.reload()
    rules = RulesService(app, idx)

    rfinal = handle_flag_problem(
        description=msg,
        context="",
        memory=mem,
        rules_svc=rules,
        source_session_id="s3",
    )
    assert rfinal["cluster"]["proposed"]
