---
name: role-plan
description: >-
  [Role · agent workflow] Produce an execution-ready plan before writing code —
  architecture, phased tasks, verification. Run `role-research` first when facts
  are unclear. Use for plan, design, ADR drafts, refactor strategy.
metadata:
  skill_class: role
  taxonomy: workflow
  discovers_with: plan,design,architecture,implementation,tasks,verification,ADR,hardening-phases
  pairs_with: role-research
triggers:
  - plan
  - design doc
  - how should we implement
  - phased rollout
---

# Planner (`role-plan`)

Do not modify source code in this skill.
Wait for explicit user approval before coding.

When requirements or root causes are ambiguous, invoke **`role-research`** before planning.

- Do not run commands or edit files during planning.
- Link every proposed change to a research finding (or cite direct code evidence).
- A plan without a verification section is incomplete.

## Agent Design Doc (modeled on Design.md)

Agent-facing. Terse. Structured for execution.

- One-line executive summary.
- Goals — short bullet list of what this solves.
- Non-goals — what is explicitly deferred or out of scope.
- Architecture — named pattern (MVVM, MVC, layered, event-driven,
  etc.) with an ASCII diagram if structure is non-trivial.
- Considerations — weighted trade-offs for key decisions:
  - State the options.
  - Pro/con for each.
  - Recommendation with rationale.
- Schemas — data shapes, interfaces, or contracts relevant to the
  implementation.
- Phases with numbered tasks (T0.1, T1.1, …) grouped by phase.
  Each task is one atomic, verifiable unit of work.
- Stop conditions — when to halt and prompt the user.
- Verification plan — tests and manual steps to confirm success.

## User Guide (modeled on README.md)

Human-facing. Readable. No implementation detail.

- One-paragraph overview of what was built and why.
- Architecture diagram if helpful.
- Install or setup steps if applicable.
- Feature list or capability summary.
- Usage examples or user journeys.
- Troubleshooting section if failure modes are non-obvious.
