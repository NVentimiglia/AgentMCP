from __future__ import annotations

import json
from pathlib import Path

from agent_mcp.config import load_config
from agent_mcp.paths import CONFIG_NAME, find_project_root


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
    if not cfg_path.is_file():
        fatal.append(f"missing {cfg_path}")
    else:
        try:
            load_config(root)
        except Exception as e:
            fatal.append(f"config.toml invalid: {e}")

    expected_dirs = [
        root / "skills",
        root / "rules" / "active",
        root / "rules" / "proposals",
        root / "memory",
        root / "state",
        root / "tests",
    ]
    for d in expected_dirs:
        if not d.exists():
            fatal.append(f"missing directory: {d}")

    changelog = root / "rules" / "CHANGELOG.md"
    if not changelog.is_file():
        warn.append(f"missing {changelog} (recommended)")

    clusters = root / "state" / "clusters.json"
    if not clusters.is_file():
        warn.append(f"missing {clusters} (will be created on first cluster write)")

    metrics = root / "state" / "metrics.json"
    if not metrics.is_file():
        warn.append(f"missing {metrics} (will be created on first MCP tool use)")

    models = Path.home() / ".agent-mcp" / "models"
    if not models.exists():
        warn.append(f"missing embedding cache directory: {models} (run `agent-mcp models pull`)")

    cursor_cfg = Path.home() / ".cursor" / "mcp.json"
    if cursor_cfg.is_file():
        try:
            raw = json.loads(cursor_cfg.read_text(encoding="utf-8"))
            servers = (raw.get("mcpServers") or {}) if isinstance(raw, dict) else {}
            if "agent-mcp" not in servers:
                warn.append("Cursor MCP config exists but missing `agent-mcp` server entry")
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
