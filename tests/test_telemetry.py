from __future__ import annotations

import json
from pathlib import Path

from skills_mcp.server import (
    configure_for_tests,
    list_skills,
    read_skill,
    skill_health,
    verify_setup,
)
from skills_mcp.telemetry import (
    _load_telemetry,
    record_session,
    record_skill_access,
    record_tool_call,
)


def test_telemetry_unit_operations(tmp_path: Path) -> None:
    telemetry_file = tmp_path / "telemetry.json"

    # 1. Test record_session
    record_session(tmp_path)
    data = _load_telemetry(telemetry_file)
    assert data["TotalSessions"] == 1
    assert data["TotalSkillCalls"] == 0
    assert data["ToolCalls"] == {}
    assert data["Skills"] == []

    # 2. Test record_tool_call
    record_tool_call(tmp_path, "verify_setup")
    record_tool_call(tmp_path, "verify_setup")
    data = _load_telemetry(telemetry_file)
    assert data["ToolCalls"]["verify_setup"] == 2

    # 3. Test record_skill_access (and sorting leaderboard)
    record_skill_access(tmp_path, "role-research")
    record_skill_access(tmp_path, "role-plan")
    record_skill_access(tmp_path, "role-plan")

    data = _load_telemetry(telemetry_file)
    assert data["TotalSkillCalls"] == 3
    # Check that "role-plan" is first (count=2), and "role-research" is second (count=1)
    assert data["Skills"] == [{"role-plan": 2}, {"role-research": 1}]


def test_telemetry_via_server_tools(project_home: Path) -> None:
    # Create a mock skill in the project BEFORE configuring the server so it is scanned
    skills_dir = project_home / ".agents" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    (skills_dir / "test-skill.md").write_text(
        "---\nname: test-skill\ndescription: Smoke telemetry\ntriggers: []\n---\nTest Skill MD Content\n",
        encoding="utf-8"
    )

    # configure_for_tests initializes the server, which also triggers record_session.
    app = configure_for_tests(project_home)
    telemetry_file = app.root / "telemetry.json"

    # Verify session count is initialized
    data = _load_telemetry(telemetry_file)
    assert data["TotalSessions"] == 1
    assert data["ToolCalls"] == {}

    # Call verify_setup (should record a tool call)
    verify_setup()
    data = _load_telemetry(telemetry_file)
    assert data["ToolCalls"]["verify_setup"] == 1

    # Call list_skills (should record a tool call)
    list_skills()
    data = _load_telemetry(telemetry_file)
    assert data["ToolCalls"]["list_skills"] == 1

    # Read the skill (should record tool call AND skill access)
    read_skill("test-skill")
    data = _load_telemetry(telemetry_file)
    assert data["ToolCalls"]["read_skill"] == 1
    assert data["TotalSkillCalls"] == 1
    assert data["Skills"] == [{"test-skill": 1}]

    # Call skill_health and verify
    raw_health = skill_health()
    health_data = json.loads(raw_health)

    assert health_data["status"] == "healthy"
    assert health_data["call_number"] == 1
    assert health_data["total_sessions"] == 1
    assert health_data["total_skill_calls"] == 1

    # Call skill_health again and verify call sequence increment
    raw_health_2 = skill_health()
    health_data_2 = json.loads(raw_health_2)
    assert health_data_2["call_number"] == 2
