from __future__ import annotations

import json
from pathlib import Path

from skills_mcp.config import load_config
from skills_mcp.config_paths import resolve_content_dir, resolve_shared_skills_dir
from skills_mcp.mcp_registration import registration_status
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

    if cfg is not None and cfg.paths.content:
        content = resolve_content_dir(root, cfg.paths.content)
        if content is None:
            warn.append(
                f"paths.content = '{cfg.paths.content}' is set but directory is missing "
                "(no shared skills or rules until it exists)"
            )
        else:
            if not (content / "skills").is_dir():
                warn.append(
                    f"paths.content '{content}' exists but has no skills/ subdirectory"
                )

    agents_dir = root / ".agents"
    if not agents_dir.is_dir():
        warn.append("missing .agents/ directory — run `skills-mcp init` to scaffold")
    else:
        if not (agents_dir / "skills").is_dir():
            warn.append("missing .agents/skills/ directory")
        if not (agents_dir / "AGENT.md").is_file():
            warn.append(
                "missing .agents/AGENT.md — add this file to define always-on behavioral rules"
            )

    # MCP server registration — must be registered for hosts to auto-start serve
    reg = registration_status()
    for host, registered in reg.items():
        if not registered:
            warn.append(
                f"{host}: skills-mcp server not registered — run `skills-mcp mcp register` "
                f"(serve will not start automatically without this)"
            )

    # Cursor: check for deprecated key
    cursor_cfg = Path.home() / ".cursor" / "mcp.json"
    if cursor_cfg.is_file():
        try:
            raw = json.loads(cursor_cfg.read_text(encoding="utf-8"))
            servers = (raw.get("mcpServers") or {}) if isinstance(raw, dict) else {}
            if "agent-mcp" in servers and "skills-mcp" not in servers:
                warn.append(
                    "Cursor MCP still uses deprecated `agent-mcp` key — rename to `skills-mcp` in ~/.cursor/mcp.json"
                )
        except Exception as e:
            warn.append(f"unable to parse ~/.cursor/mcp.json: {e}")

    _print(fatal, warn)
    return 1 if fatal else 0


def _print(fatal: list[str], warn: list[str]) -> None:
    if fatal:
        print("doctor: errors:\n- " + "\n- ".join(fatal))
    if warn:
        print("doctor: warnings:\n- " + "\n- ".join(warn))
    if not fatal and not warn:
        print("doctor: OK")
