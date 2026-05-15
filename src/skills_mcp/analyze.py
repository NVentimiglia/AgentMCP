"""Behavioral analysis via vendored gemini-docter (skills_mcp/dr/).

Reads session transcripts (Claude Code, Gemini, Cursor), detects behavioral
signals, and writes dr-*.md into the calling project's ``.memory/`` folder.

``.memory/`` is project-local.  AgentMCP's own ``rules/`` is never touched
by this module — that directory holds hand-authored global guardrails only.

Usage:
    skills-mcp analyze
"""

from __future__ import annotations

import re
import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import yaml

from skills_mcp.app_state import AppContext
from skills_mcp.lockfile import AnalyzeLock, DEFAULT_COOLDOWN_SECONDS

# Patchable in tests via monkeypatch.setattr("skills_mcp.analyze.ANALYZE_COOLDOWN_SECONDS", 0)
ANALYZE_COOLDOWN_SECONDS: int = DEFAULT_COOLDOWN_SECONDS

try:
    from skills_mcp.dr.analyzer import generate_report
    _DR_AVAILABLE = True
except ImportError:
    generate_report = None  # type: ignore[assignment]
    _DR_AVAILABLE = False

_SIGNAL_META: dict[str, dict[str, str]] = {
    "correction-heavy": {
        "trigger": "agent makes mistakes requiring frequent user correction (>20% of messages)",
        "solution": (
            "When the user corrects you, MUST stop and re-read their message. "
            "Quote back what they asked for and confirm understanding before proceeding."
        ),
    },
    "keep-going-loop": {
        "trigger": "agent stops work prematurely, requiring repeated 'keep going' prompts",
        "solution": (
            "Complete the FULL task before stopping. "
            "Do not pause mid-task to ask if you should continue."
        ),
    },
    "repeated-instructions": {
        "trigger": "user repeats similar instructions indicating agent did not understand",
        "solution": (
            "Re-read the user's last message carefully. "
            "If instructions seem similar to prior ones, ask for clarification before proceeding."
        ),
    },
    "negative-drift": {
        "trigger": "user messages become shorter and more corrective over a session",
        "solution": (
            "Every few turns, re-read the original request to avoid scope drift. "
            "If user messages are shrinking, stop and re-confirm the goal."
        ),
    },
    "rapid-corrections": {
        "trigger": "user sends immediate follow-up corrections within seconds of agent response",
        "solution": (
            "Double-check output against the request before presenting it. "
            "Rapid corrections mean the response did not match expectations."
        ),
    },
    "high-turn-ratio": {
        "trigger": "high ratio of user turns to assistant turns indicating constant redirection",
        "solution": (
            "Work more autonomously. "
            "Complete larger coherent units of work per turn rather than stopping frequently."
        ),
    },
    "error-loop": {
        "trigger": "3 or more consecutive tool failures detected in a session",
        "solution": (
            "After 2 consecutive tool failures, MUST stop and change strategy. "
            "Explain what failed and try a different approach rather than retrying the same action."
        ),
    },
    "edit-thrashing": {
        "trigger": "same file edited 5 or more times in a session",
        "solution": (
            "Read the full file before editing. Plan all changes, then make ONE complete edit. "
            "If you have edited a file 3+ times, re-read the original requirements first."
        ),
    },
    "negative-sentiment": {
        "trigger": "user messages show persistent negative sentiment or frustration",
        "solution": (
            "When the user expresses frustration, MUST acknowledge it and "
            "re-confirm the task goal before continuing."
        ),
    },
    "user-interrupts": {
        "trigger": "user interrupts agent mid-task to redirect",
        "solution": (
            "Break work into small, verifiable steps. "
            "Present a plan and wait for confirmation before executing long sequences."
        ),
    },
    "excessive-exploration": {
        "trigger": "agent reads too many files before acting",
        "solution": (
            "Act sooner. Do not read more than 3-5 files before making a change. "
            "If uncertain, ask rather than exploring."
        ),
    },
}

MEMORY_DIR_NAME = ".memory"


def memory_dir(project_root: Path) -> Path:
    """Return the ``.memory/`` path for a project root."""
    return project_root / MEMORY_DIR_NAME


def _read_existing_version(path: Path) -> int:
    if not path.is_file():
        return 0
    try:
        txt = path.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---", txt, re.DOTALL)
        if not m:
            return 0
        data = yaml.safe_load(m.group(1)) or {}
        return int(str(data.get("version", "0")))
    except Exception:
        return 0


def _render_memory_rule(
    *,
    rule_id: str,
    version: int,
    trigger: str,
    solution: str,
    signal_name: str,
    count: int,
    severities: list[str],
    examples: list[str],
    sessions_analyzed: int,
    generated_at: str,
) -> str:
    severity_str = ", ".join(sorted(set(severities))) if severities else "unknown"
    fm_lines = [
        "---",
        f"id: {rule_id}",
        f"version: \"{version}\"",
        f"trigger: \"{trigger}\"",
        "solution: >-",
        f"  {solution}",
        "---",
    ]
    body_lines = [
        "",
        f"_Auto-generated by `skills-mcp analyze`. Last updated: {generated_at}_",
        "",
        (
            f"**Signal:** `{signal_name}` | "
            f"**Occurrences:** {count} session(s) | "
            f"**Severity:** {severity_str} | "
            f"**Sessions analyzed:** {sessions_analyzed}"
        ),
        "",
    ]
    if examples:
        body_lines += ["## Examples", ""]
        for ex in examples[:5]:
            body_lines.append(f"- {ex.strip()}")
        body_lines.append("")
    return "\n".join(fm_lines + body_lines)


def _git_diff_memory(project_root: Path, mem_dir: Path) -> str:
    try:
        rel = mem_dir.relative_to(project_root)
    except ValueError:
        rel = mem_dir

    diff = subprocess.run(["git", "diff", str(rel)], cwd=project_root, capture_output=True, text=True)
    status = subprocess.run(["git", "status", "--short", str(rel)], cwd=project_root, capture_output=True, text=True)
    out = diff.stdout.strip()
    new_files = [line for line in status.stdout.splitlines() if line.startswith("??")]
    if new_files:
        if out:
            out += "\n"
        out += "\n".join(new_files) + "\n(new files — run `git add .memory/` to stage)"
    return out or "(no changes)"


def run_analyze(app: AppContext, *, project_root: Path | None = None) -> int:
    """Run behavioral analysis and write dr-*.md to ``<project>/.memory/``.

    ``project_root`` is the project the agent is working in (CWD when the
    hook fires).  Omit to use ``app.root``.
    """
    if not _DR_AVAILABLE:
        print("analyze: vaderSentiment not installed.\n  Run: pip install -e '.[dr]'")
        return 1

    lock = AnalyzeLock(app.state_dir, cooldown_seconds=ANALYZE_COOLDOWN_SECONDS)
    acquired, reason = lock.try_acquire()
    if not acquired:
        print(f"analyze: skipping — {reason}")
        return 0

    try:
        rc = _run_analyze_inner(app, project_root=project_root)
        if rc == 0:
            lock.stamp()
        return rc
    finally:
        lock.release()


def _run_analyze_inner(app: AppContext, *, project_root: Path | None = None) -> int:
    effective_root = project_root or app.root
    project_name = effective_root.name
    print(f"analyze: scanning sessions for '{project_name}' ...")

    try:
        report = generate_report(providers=["claude", "gemini", "cursor"], project_filter=project_name)
    except Exception as exc:
        print(f"analyze: error: {exc}")
        return 1

    if report.total_sessions == 0:
        print("analyze: no sessions found  (expected at ~/.claude/projects/)")
        return 0

    print(f"analyze: {report.total_sessions} session(s), {len(report.top_signals)} signal(s)")

    if not report.top_signals:
        print("analyze: no signals — .memory/ unchanged")
        return 0

    sig_counts: dict[str, int] = defaultdict(int)
    sig_severities: dict[str, list[str]] = defaultdict(list)
    sig_examples: dict[str, list[str]] = defaultdict(list)

    for sig in report.top_signals:
        sig_counts[sig.signal_name] += 1
        sig_severities[sig.signal_name].append(sig.severity)
        sig_examples[sig.signal_name].extend(sig.examples)

    mem = memory_dir(effective_root)
    mem.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    written: list[str] = []
    for signal_name, count in sorted(sig_counts.items()):
        rule_id = f"dr-{signal_name}"
        rule_path = mem / f"{rule_id}.md"
        meta = _SIGNAL_META.get(signal_name, {})
        version = _read_existing_version(rule_path) + 1
        content = _render_memory_rule(
            rule_id=rule_id,
            version=version,
            trigger=meta.get("trigger", f"{signal_name} pattern detected in session"),
            solution=meta.get("solution", f"Address the {signal_name} anti-pattern."),
            signal_name=signal_name,
            count=count,
            severities=sig_severities[signal_name],
            examples=sig_examples[signal_name],
            sessions_analyzed=report.total_sessions,
            generated_at=generated_at,
        )
        rule_path.write_text(content, encoding="utf-8")
        written.append(rule_path.name)

    print(f"analyze: wrote {len(written)} memory file(s): {', '.join(written)}")
    print(f"\n--- git diff {MEMORY_DIR_NAME}/ ---")
    print(_git_diff_memory(effective_root, mem))
    return 0
