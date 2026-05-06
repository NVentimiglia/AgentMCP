from __future__ import annotations

from skills_mcp.paths import CONFIG_NAME


def test_init_layout_and_config(project_home) -> None:
    assert (project_home / CONFIG_NAME).is_file()
    assert (project_home / "skills").is_dir()
    assert (project_home / "rules").is_dir()
    assert (project_home / "state").is_dir()
