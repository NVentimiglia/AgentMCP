from __future__ import annotations

from skills_mcp.paths import CONFIG_NAME


def test_init_layout_and_config(project_home) -> None:
    assert (project_home / CONFIG_NAME).is_file()
    assert (project_home / ".agents" / "skills").is_dir()
    assert (project_home / ".agents" / "AGENT.md").is_file()
    # .agents/rules/ is optional — only needed for structured MCP-queryable rules
    assert not (project_home / "rules").is_dir(), "rules/ should not be at project root"
    assert not (project_home / "skills").is_dir(), "skills/ should not be at project root"
    assert not (project_home / "state").is_dir(), "state/ should not be at project root"
    assert not (project_home / "tests").is_dir(), "tests/ should not be at project root"
