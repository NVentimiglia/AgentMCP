---
name: session-start
description: Start-of-session checklist. Run memory_search on your current task, then proceed.
triggers: ["start", "session", "begin"]
---

At the start of a working session: (1) Summarize the task in one line. (2) Call `memory_search` with that line and `k=5`. (3) Apply any returned decisions, patterns, or preferences before editing code. (4) If nothing relevant is returned, continue and store useful findings with `memory_store` before you finish.
