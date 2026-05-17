from __future__ import annotations

import json
from pathlib import Path


def _load_telemetry(file_path: Path) -> dict:
    """Load telemetry JSON data from file or return default structure if not found/invalid."""
    if file_path.is_file():
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "TotalSessions": 0,
        "TotalSkillCalls": 0,
        "ToolCalls": {},
        "Skills": [],
    }


def _save_telemetry(file_path: Path, data: dict) -> None:
    """Save telemetry JSON data to file. Swallows OSErrors to avoid interrupting MCP server."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError:
        pass


def record_session(root: Path) -> None:
    """Increment the total session count when the server initializes."""
    file_path = root / "telemetry.json"
    data = _load_telemetry(file_path)
    data["TotalSessions"] = data.get("TotalSessions", 0) + 1
    _save_telemetry(file_path, data)


def record_tool_call(root: Path, tool_name: str) -> None:
    """Increment the invocation count for a specific MCP tool."""
    file_path = root / "telemetry.json"
    data = _load_telemetry(file_path)
    tool_calls = data.setdefault("ToolCalls", {})
    tool_calls[tool_name] = tool_calls.get(tool_name, 0) + 1
    _save_telemetry(file_path, data)


def record_skill_access(root: Path, skill_name: str) -> None:
    """Increment total skill access counter and update the individual skill leaderboards."""
    file_path = root / "telemetry.json"
    data = _load_telemetry(file_path)
    data["TotalSkillCalls"] = data.get("TotalSkillCalls", 0) + 1

    skills_list: list[dict[str, int]] = data.setdefault("Skills", [])

    # Convert the list of single-key dictionaries into a flat dictionary for processing
    local_skills: dict[str, int] = {}
    for item in skills_list:
        for k, v in item.items():
            local_skills[k] = local_skills.get(k, 0) + v

    local_skills[skill_name] = local_skills.get(skill_name, 0) + 1

    # Sort skills by count descending, then alphabetically on name for stability
    sorted_skills = sorted(local_skills.items(), key=lambda x: (-x[1], x[0]))

    data["Skills"] = [{k: v} for k, v in sorted_skills]
    _save_telemetry(file_path, data)
