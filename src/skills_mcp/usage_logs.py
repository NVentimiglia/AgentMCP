from __future__ import annotations

import json
import os
import re
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Entire ``logs/`` tree budget (bytes).
MAX_LOG_DIR_BYTES = 20 * 1024 * 1024
# Max characters of tool response written into a single log file.
MAX_RESPONSE_LOG_CHARS = 8192

_SAFE_SEGMENT = re.compile(r"^[a-z0-9][a-z0-9._-]{0,119}$")


def logs_root(project_root: Path) -> Path:
    return (project_root / "state" / "logs").resolve()


def sanitize_path_segment(s: str, *, fallback: str = "unknown") -> str:
    """Map arbitrary string to a single safe directory/file segment."""
    t = s.strip().lower()
    t = re.sub(r"[^a-z0-9._-]+", "_", t)
    t = t.strip("._-") or fallback
    if len(t) > 120:
        t = t[:120]
    if not _SAFE_SEGMENT.match(t):
        return fallback
    if t in {".", ".."}:
        return fallback
    return t


def _ensure_under_logs(base: Path, candidate: Path) -> Path:
    base_s = str(base.resolve())
    cand_s = str(candidate.resolve())
    if not (cand_s == base_s or cand_s.startswith(base_s + os.sep)):
        raise ValueError("log path escapes logs directory")
    return candidate


def _truncate_response(text: str | None) -> tuple[str, int, bool]:
    if text is None:
        return "", 0, False
    n = len(text)
    if n <= MAX_RESPONSE_LOG_CHARS:
        return text, n, False
    half = MAX_RESPONSE_LOG_CHARS // 2
    head = text[:half]
    tail = text[-half:]
    truncated = f"{head}\n\n… [{n - MAX_RESPONSE_LOG_CHARS} chars omitted] …\n\n{tail}"
    return truncated, n, True


def _collect_files(log_base: Path) -> list[tuple[Path, int, float]]:
    if not log_base.is_dir():
        return []
    out: list[tuple[Path, int, float]] = []
    for p in log_base.rglob("*"):
        if p.is_file():
            try:
                st = p.stat()
            except OSError:
                continue
            out.append((p, st.st_size, st.st_mtime))
    return out


def enforce_logs_budget(project_root: Path, *, max_bytes: int = MAX_LOG_DIR_BYTES) -> None:
    """If ``logs/`` exceeds ``max_bytes``, delete oldest files (by mtime) until under budget."""
    log_base = logs_root(project_root)
    if not log_base.is_dir():
        return

    files = _collect_files(log_base)
    total = sum(sz for _p, sz, _m in files)
    if total <= max_bytes:
        return

    files.sort(key=lambda t: t[2])  # oldest mtime first
    for path, sz, _m in files:
        if total <= max_bytes:
            break
        try:
            path.unlink()
            total -= sz
        except OSError:
            continue

    # If still over (e.g. single huge file), try again — unlikely with truncation.
    if total > max_bytes:
        files = _collect_files(log_base)
        files.sort(key=lambda t: t[2])
        for path, sz, _m in files:
            if total <= max_bytes:
                break
            try:
                path.unlink()
                total -= sz
            except OSError:
                continue


def append_tool_log(
    project_root: Path,
    *,
    bucket_parts: tuple[str, ...],
    tool_name: str,
    args: dict[str, Any],
    session_note: str,
    response: str | None,
    error: str | None,
) -> Path | None:
    """
    Write one markdown blob under ``logs/<bucket_parts...>/blob-<UTC>.md``.
    Returns path written, or None if logging skipped due to error.
    """
    log_base = logs_root(project_root)
    safe_parts = tuple(sanitize_path_segment(p, fallback="x") for p in bucket_parts if p)
    if not safe_parts:
        safe_parts = ("_tools", "unknown")

    rel = Path(*safe_parts)
    target_dir = _ensure_under_logs(log_base, log_base / rel)
    target_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    fname = f"blob-{ts}-{sanitize_path_segment(tool_name, fallback='tool')}.md"
    out_path = _ensure_under_logs(log_base, target_dir / fname)

    body_resp, resp_len, resp_trunc = _truncate_response(response)
    lines = [
        f"# MCP tool `{tool_name}`",
        "",
        f"- **utc**: {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- **response_chars**: {resp_len}",
        f"- **response_truncated**: {resp_trunc}",
        "",
        "## Arguments",
        "",
        "```json",
        json.dumps(args, ensure_ascii=False, indent=2, default=str),
        "```",
        "",
    ]
    if session_note.strip():
        lines += ["## Session note (caller-supplied)", "", session_note.strip(), ""]
    if error:
        lines += ["## Error", "", f"```\n{error}\n```", ""]
    lines += ["## Response (possibly truncated)", "", "```", body_resp, "```", ""]

    try:
        out_path.write_text("\n".join(lines), encoding="utf-8")
    except OSError:
        return None

    enforce_logs_budget(project_root)
    return out_path


def format_exception(exc: BaseException) -> str:
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).strip()
