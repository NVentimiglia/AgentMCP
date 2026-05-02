from __future__ import annotations

import json
import logging
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ulid import ULID

_SESSION_FILE: Path | None = None
_ERROR_FILE: Path | None = None


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if "text" in payload and isinstance(payload.get("text"), str):
        payload = {**payload, "text": "[REDACTED]"}
    return payload


def init_session_logging() -> Path:
    global _SESSION_FILE, _ERROR_FILE
    log_root = Path.home() / ".agent-mcp" / "log"
    log_root.mkdir(parents=True, exist_ok=True)

    # Per-session tool event log
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    _SESSION_FILE = log_root / f"session-{stamp}-{ULID()}.jsonl"

    fh = logging.FileHandler(_SESSION_FILE, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(message)s"))

    lg = logging.getLogger("agent_mcp.session")
    for h in lg.handlers:
        h.close()
    lg.handlers.clear()
    lg.addHandler(fh)
    lg.setLevel(logging.INFO)
    lg.propagate = False

    # Persistent error log (appended across sessions)
    _ERROR_FILE = log_root / "errors.log"
    efh = logging.FileHandler(_ERROR_FILE, mode="a", encoding="utf-8")
    efh.setLevel(logging.ERROR)
    efh.setFormatter(logging.Formatter("%(asctime)s ERROR %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ"))

    err_lg = logging.getLogger("agent_mcp.errors")
    for h in err_lg.handlers:
        h.close()
    err_lg.handlers.clear()
    err_lg.addHandler(efh)
    err_lg.setLevel(logging.ERROR)
    err_lg.propagate = False

    return _SESSION_FILE


def log_error(context: str, exc: BaseException) -> None:
    """Append one entry to errors.log. Call from any except block."""
    lg = logging.getLogger("agent_mcp.errors")
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).strip()
    lg.error("[%s] %s: %s\n%s", context, type(exc).__name__, exc, tb)


def log_tool_event(tool: str, arguments: dict[str, Any]) -> None:
    lg = logging.getLogger("agent_mcp.session")
    if not lg.handlers:
        return

    safe_args = dict(arguments)
    if "text" in safe_args:
        safe_args = _redact_payload(safe_args)
    if "memory" in safe_args and isinstance(safe_args["memory"], dict):
        inner = dict(safe_args["memory"])
        if isinstance(inner.get("text"), str):
            inner["text"] = "[REDACTED]"
        safe_args["memory"] = inner

    record = {"tool": tool, "args": safe_args, "ts": datetime.now(UTC).isoformat()}
    lg.info(json.dumps(record, separators=(",", ":"), sort_keys=False))
