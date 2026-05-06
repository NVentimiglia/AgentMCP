from __future__ import annotations

import json
from pathlib import Path

from skills_mcp.config import load_config
from skills_mcp.config_paths import resolve_shared_skills_dir
from skills_mcp.paths import CONFIG_NAME, find_project_root


def run_doctor() -> int:
    fatal: list[str] = []
    warn: list[str] = []

    try:
        root = find_project_root()
    except Exception as e:
        fatal.append(f"project root: {e}")
        _print(fatal, warn)
        return 1

    cfg_path = root / CONFIG_NAME
    cfg = None

    if not cfg_path.is_file():
        fatal.append(f"missing {cfg_path}")
    else:
        try:
            cfg = load_config(root)
        except Exception as e:
            fatal.append(f"config.toml invalid: {e}")

    if cfg is not None and cfg.paths.shared_skills:
        if resolve_shared_skills_dir(root, cfg.paths.shared_skills) is None:
            warn.append(
                "paths.shared_skills is set in config.toml but directory is missing "
                "(project skills-only until it exists)",
            )

    expected_dirs = [
        root / "skills",
        root / "rules",
        root / "state",
        root / "tests",
    ]
    for d in expected_dirs:
        if not d.exists():
            fatal.append(f"missing directory: {d}")

    cursor_cfg = Path.home() / ".cursor" / "mcp.json"
    if cursor_cfg.is_file():
        try:
            raw = json.loads(cursor_cfg.read_text(encoding="utf-8"))
            servers = (raw.get("mcpServers") or {}) if isinstance(raw, dict) else {}
            if "skills-mcp" not in servers:
                if "agent-mcp" in servers:
                    warn.append(
                        "Cursor MCP still uses deprecated `agent-mcp` key; rename to `skills-mcp` in mcp.json"
                    )
                else:
                    warn.append(
                        "Cursor MCP config exists but missing `skills-mcp` server entry"
                    )
        except Exception as e:
            warn.append(f"unable to parse Cursor MCP config ~/.cursor/mcp.json: {e}")
    else:
        warn.append("Cursor MCP config not found at ~/.cursor/mcp.json (optional)")

    _print(fatal, warn)
    return 1 if fatal else 0


def _print(fatal: list[str], warn: list[str]) -> None:
    if fatal:
        print("doctor: errors:\n- " + "\n- ".join(fatal))
    if warn:
        print("doctor: warnings:\n- " + "\n- ".join(warn))
    if not fatal and not warn:
        print("doctor: OK")
