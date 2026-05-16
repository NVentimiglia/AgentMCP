from __future__ import annotations

import json

from skills_mcp.config import load_config
from skills_mcp.mcp_registration import registration_status
from skills_mcp.paths import CONFIG_NAME, project_root_from_env_or_discover


def run_doctor() -> int:
    fatal: list[str] = []
    warn: list[str] = []

    try:
        root = project_root_from_env_or_discover()
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
            fatal.append(f"{CONFIG_NAME} invalid: {e}")

    if cfg is not None:
        from skills_mcp.config import resolve_path
        for folder in cfg.skill_folders:
            d = resolve_path(root, folder)
            if not d.is_dir():
                warn.append(
                    f"skill_folder '{folder}' does not exist yet "
                    "(create it or remove from skill_folders)"
                )

    # MCP server registration
    reg = registration_status()
    for host, registered in reg.items():
        if not registered:
            warn.append(
                f"{host}: skills-mcp server not registered — run `skills-mcp mcp register` "
                f"(serve will not start automatically without this)"
            )

    _print(fatal, warn)
    return 1 if fatal else 0


def _print(fatal: list[str], warn: list[str]) -> None:
    if fatal:
        print("doctor: errors:\n- " + "\n- ".join(fatal))
    if warn:
        print("doctor: warnings:\n- " + "\n- ".join(warn))
    if not fatal and not warn:
        print("doctor: OK")
