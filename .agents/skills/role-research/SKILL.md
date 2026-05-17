---
name: role-research
description: >-
  [Role · agent workflow] Fact-finding and ideation before planning: map
  unknowns, assign risk/reward, run parallel subagent probes, converge on
  ranked options. Use before `role-plan`. Triggers — research, investigate,
  unknown root cause, approach comparison.
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
  - unknown approach
  - compare options
---
# Researcher (`role-research`)

Gather facts and map unknowns. Do not propose solutions — surface
options and assign directional guidance.

---

## Phase 0 · Frame the Problem

Before any exploration:

1. State the question in one sentence.
2. List what is already known (observations only — no hypotheses).
3. List explicit unknowns — gaps that block a decision.

For each unknown assign:

- **Risk** — consequence if wrong (Low / Medium / High)
- **Reward** — value if resolved (Low / Medium / High)
- **Direction** — best guess on where to look (file, doc, test, external)

Stop and surface this list to the user before proceeding if the
problem statement is ambiguous.

---

## Phase 1 · Diverge (Parallel Subagents)

Trigger when: the right approach is genuinely unclear, two or more
implementations need comparison, or independent validation is needed.

Spawn one subagent per candidate angle. Each subagent:

- Receives only the question and its assigned angle — no other
  subagent's findings.
- Returns a structured report:
  - **Findings** — bullets with citations (file path + line, URL, doc section)
  - **Pros** — concrete benefits
  - **Cons** — concrete drawbacks or risks
  - **Confidence** — Low / Medium / High with one-line rationale

Subagents work in parallel and must not share intermediate results.

---

## Phase 2 · Converge (Synthesis)

After all subagents complete:

1. Identify contradictions — flag where findings conflict.
2. Identify gaps — unknowns not resolved by any subagent.
3. Identify consensus — findings agreed across agents.
4. Weight each option against the risk/reward table from Phase 0.

Produce a **findings table**:

| Option | Pros | Cons | Risk | Reward | Confidence | Recommended |
|--------|------|------|------|--------|------------|-------------|
| A      | ...  | ...  | H/M/L | H/M/L | H/M/L    | Yes / No    |

Mark at most one option `Recommended`. If none qualifies, state
`No clear winner — further research needed` and list blocking gaps.

---

## Phase 3 · Exit Criteria

State one of:

- **Ready for planning** — enough information exists; invoke `role-plan`.
- **Further research needed** — list remaining unknowns and suggested angles.
- **Escalate** — ambiguity requires a human decision before proceeding.
