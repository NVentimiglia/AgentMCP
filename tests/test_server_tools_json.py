from __future__ import annotations

import json

from skills_mcp.server import (
    configure_for_tests,
    list_skills,
)


def test_list_skills_empty_after_minimal_init(project_home) -> None:
    configure_for_tests(project_home)
    skills = json.loads(list_skills())
    assert skills == []
