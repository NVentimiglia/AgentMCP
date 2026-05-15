from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_COUNTERS_LOCK = threading.RLock()

COUNTERS_FILENAME = "usage_counters.json"
SCHEMA_VERSION = 1

# All MCP tools that participate in tracing (including get_usage_counters).
KNOWN_TOOLS: tuple[str, ...] = (
    "verify_setup",
    "list_skills",
    "read_skill",
    "list_rules",
    "read_rules",
    "list_memory",
    "read_memory",
    "write_memory",
    "get_usage_counters",
)


def _default_by_tool() -> dict[str, int]:
    return {name: 0 for name in KNOWN_TOOLS}


def counters_path(project_root: Path) -> Path:
    return (project_root / "state" / COUNTERS_FILENAME).resolve()


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
    tmp.write_text(payload + "\n", encoding="utf-8")
    tmp.replace(path)


def load_counters(project_root: Path) -> dict[str, Any]:
    path = counters_path(project_root)
    if not path.is_file():
        return {
            "version": SCHEMA_VERSION,
            "updated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "by_tool": _default_by_tool(),
            "total": 0,
        }
    raw = json.loads(path.read_text(encoding="utf-8"))
    by_tool = _default_by_tool()
    if isinstance(raw.get("by_tool"), dict):
        for k, v in raw["by_tool"].items():
            if k in by_tool and isinstance(v, int) and v >= 0:
                by_tool[k] = v
    total = raw.get("total")
    if not isinstance(total, int) or total < 0:
        total = sum(by_tool.values())
    return {
        "version": SCHEMA_VERSION,
        "updated_at": raw.get("updated_at", ""),
        "by_tool": by_tool,
        "total": total,
    }


def increment_tool_counter(project_root: Path, tool_name: str) -> None:
    if tool_name not in KNOWN_TOOLS:
        return
    with _COUNTERS_LOCK:
        data = load_counters(project_root)
        by_tool: dict[str, int] = data["by_tool"]
        by_tool[tool_name] = by_tool.get(tool_name, 0) + 1
        data["by_tool"] = by_tool
        data["total"] = sum(by_tool.values())
        data["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        _atomic_write_json(counters_path(project_root), data)


def counters_snapshot_json(project_root: Path, *, project_root_str: str | None = None) -> str:
    """Return formatted JSON for MCP ``get_usage_counters`` (read-only, no increment here)."""
    with _COUNTERS_LOCK:
        data = load_counters(project_root)
    out = dict(data)
    if project_root_str is not None:
        out["project_root"] = project_root_str
    return json.dumps(out, indent=2, ensure_ascii=False, sort_keys=False)
