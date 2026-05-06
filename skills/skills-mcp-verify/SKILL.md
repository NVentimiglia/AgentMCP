---
name: skills-mcp-verify
description: >-
  [Ops] Smoke checklist for SkillsMCP — verify_setup, list_skills, list_rules.
  Run after install or MCP config changes.
metadata:
  skill_class: ops
  taxonomy: qa
  discovers_with: verify SkillsMCP, smoke test MCP, list_rules,read_rules
---

# SkillsMCP smoke checklist

## Quick ping

Call MCP **`verify_setup`** — **`paths`**, **`skills_count`**, **`rules_count`**, **`issues`**.

## Rules & skills

**`list_rules`** then **`read_rules(<id>)`**; **`list_skills`** / **`read_skill`** for playbooks.

## Sample sequence

```
list_rules()
read_rules("<id-from-list>")
verify_setup()
```
