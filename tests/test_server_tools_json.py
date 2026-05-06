from __future__ import annotations

import json

import pytest

from skills_mcp.server import (
    configure_for_tests,
    list_rules,
    list_skills,
    read_rules,
    reset_runtime,
)


def test_list_skills_empty_after_minimal_init(project_home) -> None:
    configure_for_tests(project_home)
    skills = json.loads(list_skills())
    assert skills == []


def test_list_rules_and_read_rules_roundtrip(project_home) -> None:
    (project_home / "rules" / "r.md").write_text(
        "---\nid: rid\nversion: \"1\"\ntrigger: t\nsolution: s\n---\nbody\n",
        encoding="utf-8",
    )
    reset_runtime()
    configure_for_tests(project_home)

    rows = json.loads(list_rules())
    assert any(r["id"] == "rid" and r["file"] == "r.md" for r in rows)

    md = read_rules("rid")
    assert "body" in md
    assert "---" in md


def test_read_rules_unknown_raises(project_home) -> None:
    configure_for_tests(project_home)
    with pytest.raises(KeyError):
        read_rules("nope")
