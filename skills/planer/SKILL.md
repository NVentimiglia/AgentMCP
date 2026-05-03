---
name: planer
description: Draft an implementation plan before coding. Use for plan,
  design, architecture, or "how to implement" tasks. Run researcher
  first if facts are still needed.
---

# Planer

Do not modify source code in this skill.
Wait for explicit user approval before coding.

- Do not run commands or edit files during planning.
- Link every proposed change to a research finding.
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
