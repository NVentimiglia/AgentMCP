"""Tests for agent_folders — multiple agent directories merging."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skills_mcp.app_state import init_app
from skills_mcp.cli import cmd_init
from skills_mcp.server import configure_for_tests, list_skills, reset_runtime


def _make_project(tmp_path: Path, config: str, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("SKILLS_MCP_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    cmd_init(tmp_path)
    (tmp_path / "skillmcp.toml").write_text(config, encoding="utf-8")
    return tmp_path


def _write_skill(directory: Path, name: str, description: str = "A skill") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{name}.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\nBody.\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# AppContext resolution
# ---------------------------------------------------------------------------


def test_skill_dirs_populated_from_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shared = tmp_path / "shared_agents"
    shared.mkdir()

    cfg = f'agent_folders = ["{shared.as_posix()}", ".agents/"]\n'
    root = _make_project(tmp_path, cfg, monkeypatch)
    app = init_app(root)

    assert len(app.skill_dirs) == 2
    assert app.skill_dirs[0] == (shared / "skills").resolve()
    assert app.skill_dirs[1] == (root / ".agents" / "skills").resolve()


def test_missing_skill_dir_excluded_from_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    nonexistent = tmp_path / "ghost_agents"
    cfg = f'agent_folders = ["{nonexistent.as_posix()}", ".agents/"]\n'
    root = _make_project(tmp_path, cfg, monkeypatch)
    app = init_app(root)
    # ghost dir not on disk — SkillIndex silently skips it
    configure_for_tests(root)
    skills = json.loads(list_skills())
    assert isinstance(skills, list)


def test_single_folder_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = 'agent_folders = [".agents/"]\n'
    root = _make_project(tmp_path, cfg, monkeypatch)
    app = init_app(root)
    assert len(app.skill_dirs) == 1


# ---------------------------------------------------------------------------
# Skills merging via MCP list_skills
# ---------------------------------------------------------------------------


def test_shared_skills_visible_via_mcp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shared = tmp_path / "shared_agents"
    _write_skill(shared / "skills", "shared-widget", "A shared widget skill")

    cfg = f'agent_folders = ["{shared.as_posix()}", ".agents/"]\n'
    root = _make_project(tmp_path, cfg, monkeypatch)
    configure_for_tests(root)

    skills = json.loads(list_skills())
    names = [s["name"] for s in skills]
    assert "shared-widget" in names


def test_last_folder_wins_on_collision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shared = tmp_path / "shared_agents"
    _write_skill(shared / "skills", "my-skill", "Shared version")

    cfg = f'agent_folders = ["{shared.as_posix()}", ".agents/"]\n'
    root = _make_project(tmp_path, cfg, monkeypatch)
    _write_skill(root / ".agents" / "skills", "my-skill", "Project version")
    configure_for_tests(root)

    skills = json.loads(list_skills())
    match = next(s for s in skills if s["name"] == "my-skill")
    assert "Project version" in match["description"]


def test_no_extra_folders_works_normally(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = 'agent_folders = [".agents/"]\n'
    root = _make_project(tmp_path, cfg, monkeypatch)
    app = init_app(root)
    assert len(app.skill_dirs) == 1
