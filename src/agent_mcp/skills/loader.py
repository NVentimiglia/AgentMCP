from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from agent_mcp.skills.schema import ParsedSkill, SkillFrontmatter


@dataclass
class LoadedSkill:
    skill_root: Path
    main_file: Path
    rel_path: str
    format: str  # "directory" or "legacy_file"
    references_dir: str | None
    scripts_dir: str | None
    assets_dir: str | None
    parsed: ParsedSkill


def _split_frontmatter(text: str) -> tuple[str, str]:
    m = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError("missing YAML frontmatter (expected --- ... ---)")
    return m.group(1), m.group(2)


def parse_skill_file(
    path: Path, root: Path, *, skill_root: Path | None = None, fmt: str = "legacy_file"
) -> LoadedSkill:
    raw = path.read_text(encoding="utf-8")
    fm_raw, body = _split_frontmatter(raw)
    try:
        data = yaml.safe_load(fm_raw) or {}
        if not isinstance(data, dict):
            raise ValueError("frontmatter must be a YAML mapping")
        fm = SkillFrontmatter.model_validate(data)
    except Exception as e:
        raise ValueError(f"invalid skill frontmatter in {path}: {e}") from e
    sr = (skill_root or path.parent).resolve()
    rel = str(path.relative_to(root)).replace("\\", "/")
    parsed = ParsedSkill(fm=fm, body=body)

    refs = sr / "references"
    scripts = sr / "scripts"
    assets = sr / "assets"
    return LoadedSkill(
        skill_root=sr,
        main_file=path,
        rel_path=rel,
        format=fmt,
        references_dir=(str(refs.relative_to(root)).replace("\\", "/") if refs.is_dir() else None),
        scripts_dir=(str(scripts.relative_to(root)).replace("\\", "/") if scripts.is_dir() else None),
        assets_dir=(str(assets.relative_to(root)).replace("\\", "/") if assets.is_dir() else None),
        parsed=parsed,
    )


class SkillIndex:
    def __init__(self, skills_root: Path) -> None:
        self.skills_root = skills_root
        self._by_name: dict[str, LoadedSkill] = {}

    def scan(self) -> None:
        if not self.skills_root.is_dir():
            raise FileNotFoundError(f"skills directory missing: {self.skills_root}")

        # Spec-native skills: directory containing SKILL.md
        dir_skill_files = sorted(self.skills_root.rglob("SKILL.md"))
        loaded: list[LoadedSkill] = []
        dir_roots: list[Path] = []
        for sk in dir_skill_files:
            root = sk.parent.resolve()
            ls = parse_skill_file(sk, self.skills_root, skill_root=root, fmt="directory")
            # Agent Skills spec: name must match parent directory name.
            if ls.parsed.fm.name != root.name:
                raise ValueError(
                    f"skill name `{ls.parsed.fm.name}` must match parent directory `{root.name}` "
                    f"for {sk}"
                )
            loaded.append(ls)
            dir_roots.append(root)

        # Backward-compatible legacy single-file skills (*.md) not inside skill directories
        md_files = sorted(self.skills_root.rglob("*.md"))
        legacy_files = []
        for p in md_files:
            if p.name == "SKILL.md":
                continue
            rp = p.resolve()
            if any(root in rp.parents for root in dir_roots):
                continue
            legacy_files.append(p)

        paths_by_name: dict[str, list[LoadedSkill]] = {}
        for ls in loaded:
            n = ls.parsed.fm.name
            paths_by_name.setdefault(n, []).append(ls)
        for p in legacy_files:
            ls = parse_skill_file(p, self.skills_root, fmt="legacy_file")
            n = ls.parsed.fm.name
            paths_by_name.setdefault(n, []).append(ls)

        dups = {n: [x.rel_path for x in lst] for n, lst in paths_by_name.items() if len(lst) > 1}
        if dups:
            parts = [f"`{n}` -> {sorted(v)}" for n, v in sorted(dups.items())]
            raise ValueError("duplicate skill names: " + "; ".join(parts))

        self._by_name = {n: lst[0] for n, lst in paths_by_name.items()}

    def list_skills_meta(self) -> list[dict[str, str]]:
        return [
            {
                "name": s.parsed.fm.name,
                "description": s.parsed.fm.description,
                "path": s.rel_path,
                "format": s.format,
                "references_dir": s.references_dir or "",
                "scripts_dir": s.scripts_dir or "",
                "assets_dir": s.assets_dir or "",
            }
            for s in sorted(self._by_name.values(), key=lambda x: x.parsed.fm.name)
        ]

    def get_by_name(self, name: str) -> LoadedSkill:
        if "/" in name or "\\" in name or ".." in name:
            raise ValueError("skill name cannot contain paths")
        if name not in self._by_name:
            raise KeyError(f"unknown skill: {name}")
        return self._by_name[name]

    def list_skill_files(self, name: str, folder: str | None = None) -> list[str]:
        skill = self.get_by_name(name)
        root = skill.skill_root
        allowed = {"references", "scripts", "assets", None, ""}
        if folder not in allowed:
            raise ValueError("folder must be one of: references, scripts, assets")
        base = root if not folder else root / folder
        if not base.exists():
            return []
        if base.is_file():
            rel = str(base.relative_to(root)).replace("\\", "/")
            return [rel]
        out: list[str] = []
        for p in sorted(base.rglob("*")):
            if p.is_file():
                out.append(str(p.relative_to(root)).replace("\\", "/"))
        return out

    def read_skill_file(self, name: str, rel_path: str) -> str:
        skill = self.get_by_name(name)
        if rel_path in {"", ".", ".."} or "\\" in rel_path:
            raise ValueError("invalid relative path")
        if rel_path.startswith("/") or ".." in rel_path.split("/"):
            raise ValueError("path traversal rejected")
        tgt = (skill.skill_root / rel_path).resolve()
        if skill.skill_root not in tgt.parents and tgt != skill.skill_root:
            raise ValueError("path escapes skill root")
        if not tgt.is_file():
            raise FileNotFoundError(f"skill file not found: {rel_path}")
        return tgt.read_text(encoding="utf-8")
