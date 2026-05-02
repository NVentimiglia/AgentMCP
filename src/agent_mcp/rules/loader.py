from __future__ import annotations

import re
from pathlib import Path

import yaml

from agent_mcp.rules.schema import ParsedRule, RuleFrontmatter


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
    def __init__(self, rules_active_dir: Path) -> None:
        self.rules_active_dir = rules_active_dir
        self._parsed: dict[str, tuple[Path, ParsedRule]] = {}

    def reload(self) -> None:
        self._parsed.clear()
        if not self.rules_active_dir.is_dir():
            return
        for p in sorted(self.rules_active_dir.glob("*.md")):
            pr = parse_rule_md(p)
            self._parsed[pr.fm.id] = (p, pr)

    def list_ids_triggers(self) -> list[dict[str, str]]:
        out = []
        for rule_id in sorted(self._parsed.keys()):
            _, pr = self._parsed[rule_id]
            out.append({"id": pr.fm.id, "trigger": pr.fm.trigger})
        return out

