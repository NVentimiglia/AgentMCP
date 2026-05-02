from __future__ import annotations

import json

from agent_mcp.server import configure_for_tests, flag_problem, list_skills


def test_list_skills_contains_session_start(project_home) -> None:
    configure_for_tests(project_home)
    skills = json.loads(list_skills())
    assert any(x.get("name") == "session-start" for x in skills)


def test_flag_problem_returns_json_blob(project_home) -> None:
    configure_for_tests(project_home)
    out = json.loads(flag_problem(description="one-off", context="", source_session_id="pytest"))
    assert "memory" in out and out["memory"]["id"]
