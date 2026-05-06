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
    target = target.resolve()
    dirs = [
        target / "skills",
        target / "rules",
        target / "state",
        target / "tests",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    cfg_dst = target / "config.toml"
    if not cfg_dst.is_file():
        shutil.copy2(BUNDLED / "config.toml", cfg_dst)


def cmd_serve() -> None:
    from skills_mcp.server import run_stdio_server

    run_stdio_server()


def cmd_doctor() -> int:
    from skills_mcp.doctor import run_doctor

    return run_doctor()


def main(argv: list[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(prog="skills-mcp", description="SkillsMCP MCP server CLI")
    parser.add_argument("--version", action="store_true", help="Print version")
    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init", help="Create skills/rules layout + config.toml")
    p_init.add_argument("path", nargs="?", default=".", type=Path)

    sub.add_parser("serve", help="Run MCP server (stdio)")

    sub.add_parser("doctor", help="Verify install and layout")

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
        cmd_serve()
        return

    if args.cmd == "doctor":
        sys.exit(cmd_doctor())

    parser.error(f"unknown command {args.cmd}")


if __name__ == "__main__":
    main()
