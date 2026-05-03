---
id: session_start
version: "2026-05-02"
trigger: Session start, new conversation, or when context is needed.
solution: Summarize the task, read MEMORY.md for relevant context, apply findings before editing code.
---

# Session Start

At the start of a working session:

1. Summarize the task in one line.
2. Read `MEMORY.md` from the project memory directory and scan for entries relevant to the task.
3. Apply any returned decisions, patterns, or preferences before editing code.
4. If no relevant memory exists, proceed normally. Save useful findings to a new memory file before finishing.
