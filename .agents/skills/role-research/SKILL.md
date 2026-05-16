---
name: role-research
description: >-
  [Role · agent workflow] Fact-finding and investigation before coding: read the
  repo, compare approaches, cite sources. Use before `role-plan`. Triggers —
  research, investigate, reproduction, unknown root cause.
metadata:
  skill_class: role
  taxonomy: workflow
  discovers_with: research,investigate,why,code-reading,spelunking,comparison,before-planning
  pairs_with: role-plan
triggers:
  - research
  - investigate
  - why does this fail
  - gather facts before planning
---

# Researcher (`role-research`)

Gather facts. Do not propose solutions.

- Start with specific questions, not broad exploration.
- Separate observations (what the code does) from hypotheses (why).
- Consult **`paths.rules`** (**`rules/*.md`** defaults), notebooks, and prior **`read_skill`** payloads before inventing norms.
- List findings as bullets with citations: file paths, line numbers, URLs.

Finish by stating whether enough information exists to move to
`planning`, or whether further research is needed.

When the next step is structured implementation planning, invoke skill **`role-plan`**.

## Subagent Strategy (Diverge → Converge)

For questions with multiple viable answers or competing approaches,
spawn independent subagents to research each angle in parallel.
Each subagent works without seeing the others' findings to avoid
anchoring bias. After all complete, compare results and surface
contradictions, gaps, and consensus.

Use when:
- The right approach is genuinely unclear.
- Two or more implementations exist and need comparison.
- You want independent validation of a finding.
