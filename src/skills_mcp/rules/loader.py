from __future__ import annotations

import re
from pathlib import Path

import yaml

from skills_mcp.rules.schema import ParsedRule, RuleFrontmatter


def _split_frontmatter(text: str) -> tuple[str, str]:
    m = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError("missing YAML frontmatter")
    return m.group(1), m.group(2)


def parse_rule_md(path: Path) -> ParsedRule:
    txt = path.read_text(encoding="utf-8")
    fm_raw, body = _split_frontmatter(txt)
    data = yaml.safe_load(fm_raw) or {}
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a mapping")
    fm = RuleFrontmatter.model_validate(data)
    return ParsedRule(fm=fm, body=body)


class ActiveRuleIndex:
    """Loads top-level Markdown files under ``paths.rules`` (default ``rules/*.md``)."""

    def __init__(self, rules_dir: Path) -> None:
        self.rules_dir = rules_dir.resolve()
        self._parsed: dict[str, tuple[Path, ParsedRule]] = {}

    def reload(self) -> None:
        self._parsed.clear()
        if not self.rules_dir.is_dir():
            return
        for p in sorted(self.rules_dir.glob("*.md")):
            if not p.is_file():
                continue
            try:
                pr = parse_rule_md(p)
            except ValueError:
                continue
            self._parsed[pr.fm.id] = (p, pr)

    def list_ids_triggers(self) -> list[dict[str, str]]:
        out = []
        for rule_id in sorted(self._parsed.keys()):
            _, pr = self._parsed[rule_id]
            out.append({"id": pr.fm.id, "trigger": pr.fm.trigger})
        return out

    def list_catalog(self) -> list[dict[str, str]]:
        """Metadata for MCP ``list_rules`` (id, trigger, file basename)."""
        rows: list[dict[str, str]] = []
        for rule_id in sorted(self._parsed.keys()):
            path, pr = self._parsed[rule_id]
            rows.append(
                {
                    "id": pr.fm.id,
                    "trigger": pr.fm.trigger,
                    "file": path.name,
                }
            )
        return rows

    def read_full_markdown(self, rule_id: str) -> str:
        """Return on-disk Markdown for a rule ``id`` (including frontmatter)."""
        if "/" in rule_id or "\\" in rule_id or ".." in rule_id:
            raise ValueError("rule_id must not contain paths")
        if rule_id not in self._parsed:
            raise KeyError(f"unknown rule id: {rule_id}")
        path, _pr = self._parsed[rule_id]
        return path.read_text(encoding="utf-8")

    def iter_sorted(self) -> list[tuple[Path, ParsedRule]]:
        """Rules sorted by canonical ``id`` (stable order)."""
        return [self._parsed[rid] for rid in sorted(self._parsed.keys())]
