from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path

from skills_mcp import __version__

BUNDLED = Path(__file__).resolve().parent / "bundled"


def cmd_init(target: Path) -> None:
    from skills_mcp.mcp_registration import register_all

    target = target.resolve()
    agents_dir = target / ".agents"
    (agents_dir / "skills").mkdir(parents=True, exist_ok=True)

    # AGENT.md is the primary rules source — plain markdown, no frontmatter needed.
    agent_md_dst = agents_dir / "AGENT.md"
    if not agent_md_dst.is_file():
        shutil.copy2(BUNDLED / "AGENT.md", agent_md_dst)

    cfg_dst = target / "config.toml"
    if not cfg_dst.is_file():
        shutil.copy2(BUNDLED / "config.toml", cfg_dst)

    # Register MCP server with all host agents (one-time, idempotent)
    _ok, msg = register_all(target)
    for line in msg.splitlines():
        print(f"  mcp: {line}")



def cmd_serve(root: Path | None = None) -> None:
    from skills_mcp.server import run_stdio_server

    run_stdio_server(root=root)


def cmd_doctor() -> int:
    from skills_mcp.doctor import run_doctor

    return run_doctor()


def cmd_mcp_register() -> int:
    from skills_mcp.mcp_registration import register_all
    from skills_mcp.paths import project_root_from_env_or_discover

    root = project_root_from_env_or_discover()
    _ok, msg = register_all(root)
    for line in msg.splitlines():
        print(f"mcp: {line}")
    print("mcp: restart your agent host to pick up the new server entry.")
    return 0


def main(argv: list[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(prog="skills-mcp", description="SkillsMCP MCP server CLI")
    parser.add_argument("--version", action="store_true", help="Print version")
    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init", help="Create skills/rules layout + config.toml + register MCP")
    p_init.add_argument("path", nargs="?", default=".", type=Path)

    p_serve = sub.add_parser("serve", help="Run MCP server (stdio)")
    p_serve.add_argument("--root", type=Path, help="Project root directory")

    sub.add_parser("doctor", help="Verify SkillMCP install and layout")

    p_mcp = sub.add_parser("mcp", help="Manage MCP server registration with host agents")
    p_mcp_sub = p_mcp.add_subparsers(dest="mcp_cmd")
    p_mcp_sub.add_parser(
        "register",
        help="Register skills-mcp in Claude Code, Gemini, Cursor, and Antigravity configs",
    )

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=os.environ.get("SKILLS_MCP_LOG_LEVEL")
        or os.environ.get("AGENT_MCP_LOG_LEVEL")
        or "INFO"
    )

    if args.version:
        print(__version__)
        return

    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    if args.cmd == "init":
        cmd_init(Path(args.path))
        return

    if args.cmd == "serve":
        cmd_serve(root=args.root)
        return

    if args.cmd == "doctor":
        sys.exit(cmd_doctor())

    if args.cmd == "mcp":
        if args.mcp_cmd == "register":
            sys.exit(cmd_mcp_register())
        p_mcp.print_help()
        sys.exit(1)

    parser.error(f"unknown command {args.cmd}")


if __name__ == "__main__":
    main()
