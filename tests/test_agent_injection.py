"""Tests that AGENT.md and skills from both the library agent folder
(SKILLS_MCP_LIBRARY) and the configured project agent_folders are included.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skills_mcp.app_state import init_app
from skills_mcp.server import configure_for_tests, list_skills, mcp


def _write_agent_md(agent_dir: Path, content: str) -> None:
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "AGENT.md").write_text(content, encoding="utf-8")


def _write_skill(skills_dir: Path, name: str, description: str) -> None:
    skill_dir = skills_dir / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\nBody.\n",
        encoding="utf-8",
    )


@pytest.fixture()
def dual_agent_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """
    Returns (library_agent_dir, project_root).

    library agent folder:
        AGENT.md  — "LIBRARY-RULE"
        skills/lib-skill/SKILL.md

    project root:
        skillmcp.toml  — agent_folders = [".agents/"]
        .agents/AGENT.md  — "PROJECT-RULE"
        .agents/skills/proj-skill/SKILL.md
    """
    # Library agent folder (simulates <pkg>/.agents)
    lib_agent = tmp_path / "lib_agent"
    _write_agent_md(lib_agent, "LIBRARY-RULE")
    _write_skill(lib_agent / "skills", "lib-skill", "From library")

    # Project
    project = tmp_path / "my_project"
    project.mkdir()
    _write_agent_md(project / ".agents", "PROJECT-RULE")
    _write_skill(project / ".agents" / "skills", "proj-skill", "From project")
    (project / "skillmcp.toml").write_text(
        'agent_folders = [".agents/"]\n', encoding="utf-8"
    )

    monkeypatch.setenv("SKILLS_MCP_ROOT", str(project))
    monkeypatch.setenv("SKILLS_MCP_LIBRARY", str(lib_agent))

    return lib_agent, project


# ---------------------------------------------------------------------------
# AppContext: agent_dirs and skill_dirs both populated from library + config
# ---------------------------------------------------------------------------


def test_agent_dirs_include_library_and_project(
    dual_agent_setup: tuple[Path, Path],
) -> None:
    lib_agent, project = dual_agent_setup
    app = init_app(project)

    assert lib_agent.resolve() in app.agent_dirs
    assert (project / ".agents").resolve() in app.agent_dirs


def test_skill_dirs_include_library_and_project(
    dual_agent_setup: tuple[Path, Path],
) -> None:
    lib_agent, project = dual_agent_setup
    app = init_app(project)

    assert (lib_agent / "skills").resolve() in app.skill_dirs
    assert (project / ".agents" / "skills").resolve() in app.skill_dirs


# ---------------------------------------------------------------------------
# Instructions: both AGENT.mds are injected into the MCP seed text
# ---------------------------------------------------------------------------


def test_instructions_include_both_agent_mds(
    dual_agent_setup: tuple[Path, Path],
) -> None:
    """Both AGENT.mds are combined — neither is dropped on 'collision'."""
    _, project = dual_agent_setup
    configure_for_tests(project)

    instructions = mcp._mcp_server.instructions or ""
    assert "LIBRARY-RULE" in instructions, (
        "Library AGENT.md content should be injected into MCP instructions"
    )
    assert "PROJECT-RULE" in instructions, (
        "Project AGENT.md content should be injected into MCP instructions"
    )


# ---------------------------------------------------------------------------
# Skills: both library and project skills are visible via list_skills
# ---------------------------------------------------------------------------


def test_list_skills_includes_library_skill(
    dual_agent_setup: tuple[Path, Path],
) -> None:
    _, project = dual_agent_setup
    configure_for_tests(project)

    names = [s["name"] for s in json.loads(list_skills())]
    assert "lib-skill" in names, "Library skill should appear in list_skills"


def test_list_skills_includes_project_skill(
    dual_agent_setup: tuple[Path, Path],
) -> None:
    _, project = dual_agent_setup
    configure_for_tests(project)

    names = [s["name"] for s in json.loads(list_skills())]
    assert "proj-skill" in names, "Project skill should appear in list_skills"


# ---------------------------------------------------------------------------
# Priority: project skill beats library skill on name collision
# ---------------------------------------------------------------------------


def test_project_skill_overrides_library_on_collision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lib_agent = tmp_path / "lib_agent"
    _write_skill(lib_agent / "skills", "shared-skill", "Library version")

    project = tmp_path / "project"
    project.mkdir()
    _write_skill(project / ".agents" / "skills", "shared-skill", "Project version")
    (project / "skillmcp.toml").write_text(
        'agent_folders = [".agents/"]\n', encoding="utf-8"
    )

    monkeypatch.setenv("SKILLS_MCP_ROOT", str(project))
    monkeypatch.setenv("SKILLS_MCP_LIBRARY", str(lib_agent))

    configure_for_tests(project)

    skills = json.loads(list_skills())
    match = next(s for s in skills if s["name"] == "shared-skill")
    assert "Project version" in match["description"]
