from __future__ import annotations

from agent_mcp.paths import CONFIG_NAME


def test_init_includes_skill_files(project_home) -> None:
    assert (project_home / CONFIG_NAME).is_file()
    assert (project_home / "skills" / "session-start.md").is_file()
