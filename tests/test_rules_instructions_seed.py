from __future__ import annotations

import json
from pathlib import Path

import pytest

from skills_mcp.server import _require_runtime, _sync_mcp_session_instructions, configure_for_tests, mcp

_RULE_MD = """\
---
id: demo_seed
version: "1"
trigger: When testing.
solution: Expect this in MCP instructions.
---

# Seed body

Paragraph one.
"""


def test_configure_loads_rules_into_mcp_instructions(project_home: Path) -> None:
    (project_home / "rules" / "demo_seed.md").write_text(_RULE_MD, encoding="utf-8")

    configure_for_tests(project_home)

    ins = mcp.instructions or ""
    assert "demo_seed" in ins
    assert "Paragraph one." in ins


def test_instructions_truncation_env(project_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKILLS_MCP_RULES_INSTRUCTIONS_MAX_CHARS", "120")

    (project_home / "rules" / "demo_seed.md").write_text(_RULE_MD, encoding="utf-8")

    configure_for_tests(project_home)

    ins = mcp.instructions or ""
    assert len(ins) <= 120
    assert "truncated" in ins.lower()


def test_instructions_no_truncation_when_env_zero(project_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKILLS_MCP_RULES_INSTRUCTIONS_MAX_CHARS", "0")

    (project_home / "rules" / "demo_seed.md").write_text(_RULE_MD, encoding="utf-8")

    configure_for_tests(project_home)

    ins = mcp.instructions or ""
    assert len(ins) > 200


def test_empty_rules_placeholder(project_home: Path) -> None:
    configure_for_tests(project_home)

    ins = mcp.instructions or ""
    assert "No valid `rules/*.md`" in ins or "rules/*.md` rule files yet" in ins


def test_service_add_rule_refreshes_mcp_instructions(project_home: Path) -> None:
    configure_for_tests(project_home)

    assert "demo_seed" not in (mcp.instructions or "")

    _s, idx, rules, _app = _require_runtime()
    rules.propose_rule_md(
        trigger="fresh rule trigger text",
        solution="minimal solution line",
        source_session_id="pytest",
    )
    _sync_mcp_session_instructions(idx)

    ins = mcp.instructions or ""
    assert "fresh rule trigger text" in ins


def test_instructions_order_follows_rule_id_not_filename(project_home: Path) -> None:
    z_file = """\
---
id: z_rule
version: "1"
trigger: tz
solution: sz
---
Z body
"""
    a_file = """\
---
id: a_rule
version: "1"
trigger: ta
solution: sa
---
A body
"""
    (project_home / "rules" / "z_first_on_disk.md").write_text(z_file, encoding="utf-8")
    (project_home / "rules" / "a_second_on_disk.md").write_text(a_file, encoding="utf-8")

    configure_for_tests(project_home)

    ins = mcp.instructions or ""
    pos_a = ins.index("### Rule `a_rule`")
    pos_z = ins.index("### Rule `z_rule`")
    assert pos_a < pos_z


def test_invalid_max_chars_env_treated_as_no_cap(
    project_home: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SKILLS_MCP_RULES_INSTRUCTIONS_MAX_CHARS", "not-an-int")

    (project_home / "rules" / "demo_seed.md").write_text(_RULE_MD, encoding="utf-8")

    configure_for_tests(project_home)

    ins = mcp.instructions or ""
    assert "Paragraph one." in ins
    assert "truncated" not in ins.lower()
