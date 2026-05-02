from __future__ import annotations

import json

from agent_mcp.server import (
    configure_for_tests,
    get_metrics,
    list_skills,
    memory_search,
    memory_store,
    read_skill,
    reset_runtime,
)


def test_metrics_skill_and_tool_counters(project_home) -> None:
    configure_for_tests(project_home)
    list_skills()
    read_skill("session-start")
    read_skill("session-start")
    m = json.loads(get_metrics())

    assert m["tools"]["list_skills"] == 1
    assert m["tools"]["read_skill"] == 2
    assert m["skills"]["session-start"] == 2
    assert m["tools"]["get_metrics"] == 1


def test_metrics_memory_chars_and_reload(project_home) -> None:
    configure_for_tests(project_home)
    memory_store("hello", tags=["note"], source="pytest")
    memory_search("hello", k=3)
    m1 = json.loads(get_metrics())
    assert m1["memory"]["stores"] == 1
    assert m1["memory"]["context_chars_stored"] == 5
    assert m1["memory"]["searches"] == 1

    reset_runtime()
    configure_for_tests(project_home)
    m2 = json.loads(get_metrics())
    assert m2["memory"]["stores"] == 1
    assert m2["memory"]["context_chars_stored"] == 5
    assert m2["memory"]["searches"] == 1
