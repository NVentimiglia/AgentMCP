"""Tests for paths.content — shared skills content folder."""

from __future__ import annotations

from pathlib import Path

import pytest

from skills_mcp.cli import cmd_init
from skills_mcp.app_state import init_app
from skills_mcp.server import configure_for_tests, list_skills, reset_runtime

import json

_CONFIG_WITH_CONTENT = """\
[paths]
skills  = ".agents/skills"
content = "{content}"
"""

_CONFIG_NO_CONTENT = """\
[paths]
skills = ".agents/skills"
"""


def _make_project(tmp_path: Path, config: str, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("SKILLS_MCP_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    cmd_init(tmp_path)
    (tmp_path / "config.toml").write_text(config, encoding="utf-8")
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


def test_content_dir_populates_shared_skills(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = tmp_path / "shared"
    (content / "skills").mkdir(parents=True)

    cfg = _CONFIG_WITH_CONTENT.format(content=content.as_posix())
    root = _make_project(tmp_path, cfg, monkeypatch)
    app = init_app(root)

    assert app.shared_skills_dir == content / "skills"


def test_content_dir_missing_subdir_gives_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = tmp_path / "shared"
    content.mkdir()
    # No skills/ subdirectory

    cfg = _CONFIG_WITH_CONTENT.format(content=content.as_posix())
    root = _make_project(tmp_path, cfg, monkeypatch)
    app = init_app(root)

    assert app.shared_skills_dir is None


def test_shared_skills_explicit_wins_over_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = tmp_path / "shared"
    (content / "skills").mkdir(parents=True)
    explicit_skills = tmp_path / "other_skills"
    explicit_skills.mkdir()

    cfg = (
        f'[paths]\nskills = ".agents/skills"\n'
        f'shared_skills = "{explicit_skills.as_posix()}"\n'
        f'content = "{content.as_posix()}"\n'
    )
    root = _make_project(tmp_path, cfg, monkeypatch)
    app = init_app(root)

    assert app.shared_skills_dir == explicit_skills


# ---------------------------------------------------------------------------
# Skills merging via MCP list_skills
# ---------------------------------------------------------------------------


def test_content_skills_visible_via_mcp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = tmp_path / "shared"
    _write_skill(content / "skills", "shared-widget", "A shared widget skill")

    cfg = _CONFIG_WITH_CONTENT.format(content=content.as_posix())
    root = _make_project(tmp_path, cfg, monkeypatch)
    configure_for_tests(root)

    skills = json.loads(list_skills())
    names = [s["name"] for s in skills]
    assert "shared-widget" in names


def test_project_skill_wins_over_content_skill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = tmp_path / "shared"
    _write_skill(content / "skills", "my-skill", "Shared version")

    cfg = _CONFIG_WITH_CONTENT.format(content=content.as_posix())
    root = _make_project(tmp_path, cfg, monkeypatch)
    _write_skill(root / ".agents" / "skills", "my-skill", "Project version")
    configure_for_tests(root)

    skills = json.loads(list_skills())
    match = next(s for s in skills if s["name"] == "my-skill")
    assert "Project version" in match["description"]


def test_no_content_dir_works_normally(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _make_project(tmp_path, _CONFIG_NO_CONTENT, monkeypatch)
    app = init_app(root)
    assert app.shared_skills_dir is None
