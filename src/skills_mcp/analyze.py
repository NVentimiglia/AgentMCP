"""Behavioral analysis via vendored gemini-docter (skills_mcp/dr/).

Reads Claude Code session transcripts (~/.claude/projects/), runs signal
detection, writes/updates rules/dr-*.md with SkillsMCP frontmatter,
then prints `git diff rules/` for audit. No human-in-the-loop.

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

# Attempt module-level import so tests can patch `skills_mcp.analyze.generate_report`.
# If vaderSentiment (required by the sentiment signal) is not installed, degrade gracefully.
try:
    from skills_mcp.dr.analyzer import generate_report
    _DR_AVAILABLE = True
except ImportError:
    generate_report = None  # type: ignore[assignment]
    _DR_AVAILABLE = False

# Maps gemini-docter signal names to SkillsMCP rule trigger/solution text.
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


def _read_existing_version(rule_path: Path) -> int:
    """Return the numeric version from an existing dr rule file, or 0 if absent/unparseable."""
    if not rule_path.is_file():
        return 0
    try:
        txt = rule_path.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---", txt, re.DOTALL)
        if not m:
            return 0
        data = yaml.safe_load(m.group(1)) or {}
        return int(str(data.get("version", "0")))
    except Exception:
        return 0


def _render_rule(
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


_PROJECT_DOC_BEGIN = "<!-- skills-mcp:begin -->"
_PROJECT_DOC_END = "<!-- skills-mcp:end -->"

_PROJECT_DOC_TEMPLATE = """\
# Project

<!-- Add project-specific context here. This file is injected into every MCP session. -->

"""


def _update_project_doc(
    app: AppContext,
    *,
    sessions_analyzed: int,
    signal_names: list[str],
    generated_at: str,
    project_root: Path | None = None,
) -> None:
    """Write/update the auto-managed status block inside ``Project.md``.

    ``project_root`` overrides ``app.root`` so the hook can target whichever
    project the agent is currently working in.  User content outside the
    ``<!-- skills-mcp:begin/end -->`` markers is preserved.
    """
    p = (project_root or app.root) / "Project.md"

    # Read existing content or seed from template.
    if p.is_file():
        existing = p.read_text(encoding="utf-8")
    else:
        existing = _PROJECT_DOC_TEMPLATE

    # Build the auto-managed block.
    skills_dir = app.skills_dir
    rules_dir = app.rules_dir
    skills_count = len(list(skills_dir.glob("*.md"))) if skills_dir.is_dir() else 0
    rules_count = len(list(rules_dir.glob("*.md"))) if rules_dir.is_dir() else 0

    signal_list = (
        "\n".join(f"  - `{s}`" for s in sorted(signal_names))
        if signal_names
        else "  _(none detected)_"
    )

    auto_block = (
        f"{_PROJECT_DOC_BEGIN}\n"
        f"## Status _(auto-updated by `skills-mcp analyze`)_\n\n"
        f"- **Last analyze:** {generated_at}\n"
        f"- **Sessions analyzed:** {sessions_analyzed}\n"
        f"- **Skills:** {skills_count}  |  **Rules:** {rules_count}\n"
        f"- **Active signals:**\n{signal_list}\n"
        f"{_PROJECT_DOC_END}\n"
    )

    # Replace existing managed block, or append if absent.
    begin_idx = existing.find(_PROJECT_DOC_BEGIN)
    end_idx = existing.find(_PROJECT_DOC_END)

    if begin_idx != -1 and end_idx != -1 and end_idx > begin_idx:
        new_text = existing[:begin_idx] + auto_block + existing[end_idx + len(_PROJECT_DOC_END):].lstrip("\n")
    else:
        new_text = existing.rstrip("\n") + "\n\n" + auto_block

    p.write_text(new_text, encoding="utf-8")


def _git_diff_rules(project_root: Path, rules_dir: Path) -> str:
    """Return combined `git diff` + `git status --short` output for rules/."""
    try:
        rel = rules_dir.relative_to(project_root)
    except ValueError:
        rel = rules_dir

    diff = subprocess.run(
        ["git", "diff", str(rel)],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    status = subprocess.run(
        ["git", "status", "--short", str(rel)],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    out = diff.stdout.strip()
    new_files = [line for line in status.stdout.splitlines() if line.startswith("??")]
    if new_files:
        if out:
            out += "\n"
        out += "\n".join(new_files) + "\n(new files — run `git add rules/` to stage)"
    return out or "(no changes)"


def run_analyze(app: AppContext, *, project_root: Path | None = None) -> int:
    """Run behavioral analysis and write/update rules/dr-*.md.

    ``project_root`` is the project the agent is currently working in.
    When set, ``Project.md`` is written there instead of ``app.root``.
    Returns 0 on success, 1 on error.
    """
    if not _DR_AVAILABLE:
        print(
            "analyze: vaderSentiment not installed.\n"
            "  Run: pip install -e '.[dr]'"
        )
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
    """Analyze body — called only when the lock is held."""
    effective_root = project_root or app.root
    project_name = effective_root.name
    print(f"analyze: scanning Claude Code sessions for '{project_name}' ...")

    try:
        report = generate_report(providers=["claude", "gemini", "cursor"], project_filter=project_name)
    except Exception as exc:
        print(f"analyze: error: {exc}")
        return 1

    if report.total_sessions == 0:
        print(
            "analyze: no Claude Code sessions found\n"
            "  (expected at ~/.claude/projects/)"
        )
        return 0

    print(
        f"analyze: {report.total_sessions} session(s) analyzed, "
        f"{len(report.top_signals)} signal(s) detected"
    )

    if not report.top_signals:
        print("analyze: no signals — rules unchanged")
        return 0

    # Aggregate by signal name across all sessions
    sig_counts: dict[str, int] = defaultdict(int)
    sig_severities: dict[str, list[str]] = defaultdict(list)
    sig_examples: dict[str, list[str]] = defaultdict(list)

    for sig in report.top_signals:
        sig_counts[sig.signal_name] += 1
        sig_severities[sig.signal_name].append(sig.severity)
        sig_examples[sig.signal_name].extend(sig.examples)

    # Write/update rules/dr-*.md — one file per signal
    rules_dir = app.rules_dir
    rules_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    written: list[str] = []
    for signal_name, count in sorted(sig_counts.items()):
        rule_id = f"dr-{signal_name}"
        rule_path = rules_dir / f"{rule_id}.md"

        meta = _SIGNAL_META.get(signal_name, {})
        trigger = meta.get("trigger", f"{signal_name} pattern detected in session")
        solution = meta.get("solution", f"Address the {signal_name} anti-pattern.")

        version = _read_existing_version(rule_path) + 1
        content = _render_rule(
            rule_id=rule_id,
            version=version,
            trigger=trigger,
            solution=solution,
            signal_name=signal_name,
            count=count,
            severities=sig_severities[signal_name],
            examples=sig_examples[signal_name],
            sessions_analyzed=report.total_sessions,
            generated_at=generated_at,
        )
        rule_path.write_text(content, encoding="utf-8")
        written.append(rule_path.name)

    print(f"analyze: wrote {len(written)} rule file(s): {', '.join(written)}")

    # Update Project.md status block if auto_update is enabled (default: true).
    if app.config.project_doc.auto_update:
        _update_project_doc(
            app,
            sessions_analyzed=report.total_sessions,
            signal_names=list(sig_counts.keys()),
            generated_at=generated_at,
            project_root=project_root,
        )
        print("analyze: Project.md status updated")

    # Git diff for audit — no prompts, just show what changed
    print("\n--- git diff rules/ ---")
    print(_git_diff_rules(effective_root, rules_dir))

    return 0
