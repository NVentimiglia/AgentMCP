from __future__ import annotations

from pathlib import Path

from skills_mcp.skills.loader import SkillIndex


def test_skill_index_merges_shared_skills_under_unique_names(project_home: Path) -> None:
    central = project_home.parent / "central_skill_lib"
    sn = central / "orchid-skill"
    sn.mkdir(parents=True, exist_ok=True)
    (sn / "SKILL.md").write_text(
        "---\nname: orchid-skill\ndescription: From shared catalog\n---\nLIBRARY-BODY\n",
        encoding="utf-8",
    )

    ix = SkillIndex(
        project_home / ".agents" / "skills",
        project_root=project_home,
        library_skill_dirs=(central,),
    )
    ix.scan()

    orchid = ix.get_by_name("orchid-skill")
    assert "LIBRARY-BODY" in orchid.parsed.body
    assert orchid.catalog_origin == "library"


def test_project_skill_shadows_shared_catalog_on_name(project_home: Path) -> None:
    central = project_home.parent / "central_skill_lib2"
    sn = central / "twin-skill"
    sn.mkdir(parents=True, exist_ok=True)
    (sn / "SKILL.md").write_text(
        "---\nname: twin-skill\ndescription: Library\n---\nFROM-LIBRARY\n",
        encoding="utf-8",
    )

    proj = project_home / ".agents" / "skills" / "twin-skill"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "SKILL.md").write_text(
        "---\nname: twin-skill\ndescription: Project\n---\nFROM-PROJECT\n",
        encoding="utf-8",
    )

    ix = SkillIndex(
        project_home / ".agents" / "skills",
        project_root=project_home,
        library_skill_dirs=(central,),
    )
    ix.scan()

    twin = ix.get_by_name("twin-skill")
    assert "FROM-PROJECT" in twin.parsed.body
    assert twin.catalog_origin == "project"

