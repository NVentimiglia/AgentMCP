from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

METRICS_SCHEMA_VERSION = 1


def _utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_state() -> dict[str, Any]:
    return {
        "version": METRICS_SCHEMA_VERSION,
        "updated_at": _utc_now_iso(),
        "tools": {},
        "skills": {},
        "memory": {
            "stores": 0,
            "searches": 0,
            "reinforces": 0,
            "context_chars_stored": 0,
        },
        "rules": {
            "list": 0,
            "propose": 0,
            "promote": 0,
            "rollback": 0,
        },
        "problems": {"flagged": 0},
    }


class MetricsStore:
    """Persistent aggregate counters under state/metrics.json (stdlib only)."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._state = _default_state()
        self._load_merge()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._state))

    def record(
        self,
        *,
        tool: str,
        skill_name: str | None = None,
        memory_text_len: int | None = None,
    ) -> None:
        with self._lock:
            tools: dict[str, int] = self._state.setdefault("tools", {})
            tools[tool] = int(tools.get(tool, 0)) + 1

            if skill_name:
                skills: dict[str, int] = self._state.setdefault("skills", {})
                skills[skill_name] = int(skills.get(skill_name, 0)) + 1

            mem = self._state.setdefault("memory", {})
            rules = self._state.setdefault("rules", {})
            problems = self._state.setdefault("problems", {})

            if tool == "memory_store":
                mem["stores"] = int(mem.get("stores", 0)) + 1
                if memory_text_len is not None and memory_text_len > 0:
                    mem["context_chars_stored"] = int(mem.get("context_chars_stored", 0)) + int(
                        memory_text_len
                    )
            elif tool == "memory_search":
                mem["searches"] = int(mem.get("searches", 0)) + 1
            elif tool == "memory_reinforce":
                mem["reinforces"] = int(mem.get("reinforces", 0)) + 1
            elif tool == "list_rules":
                rules["list"] = int(rules.get("list", 0)) + 1
            elif tool == "propose_rule":
                rules["propose"] = int(rules.get("propose", 0)) + 1
            elif tool == "promote_rule":
                rules["promote"] = int(rules.get("promote", 0)) + 1
            elif tool == "rollback_rule":
                rules["rollback"] = int(rules.get("rollback", 0)) + 1
            elif tool == "flag_problem":
                problems["flagged"] = int(problems.get("flagged", 0)) + 1

            self._state["updated_at"] = _utc_now_iso()
            self._persist_unsafe()

    def _load_merge(self) -> None:
        if not self._path.is_file():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            from agent_mcp.session_logging import log_error
            log_error("metrics._load_merge", exc)
            return
        if not isinstance(raw, dict):
            return
        if int(raw.get("version", 0)) != METRICS_SCHEMA_VERSION:
            return
        st = _default_state()
        if isinstance(raw.get("updated_at"), str):
            st["updated_at"] = raw["updated_at"]
        if isinstance(raw.get("tools"), dict):
            st["tools"] = {
                str(k): int(v) for k, v in raw["tools"].items() if isinstance(v, (int, float))
            }
        if isinstance(raw.get("skills"), dict):
            st["skills"] = {
                str(k): int(v) for k, v in raw["skills"].items() if isinstance(v, (int, float))
            }
        if isinstance(raw.get("memory"), dict):
            rm = raw["memory"]
            for key in ("stores", "searches", "reinforces", "context_chars_stored"):
                if key in rm and isinstance(rm[key], (int, float)):
                    st["memory"][key] = int(rm[key])
        if isinstance(raw.get("rules"), dict):
            rr = raw["rules"]
            for key in ("list", "propose", "promote", "rollback"):
                if key in rr and isinstance(rr[key], (int, float)):
                    st["rules"][key] = int(rr[key])
        if isinstance(raw.get("problems"), dict) and isinstance(
            raw["problems"].get("flagged"), (int, float)
        ):
            st["problems"]["flagged"] = int(raw["problems"]["flagged"])
        self._state = st

    def _persist_unsafe(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".json.tmp")
        text = json.dumps(self._state, indent=2, sort_keys=False)
        tmp.write_text(text + ("\n" if not text.endswith("\n") else ""), encoding="utf-8")
        tmp.replace(self._path)
