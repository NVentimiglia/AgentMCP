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


def cmd_analyze() -> int:
    from skills_mcp.analyze import run_analyze
    from skills_mcp.app_state import init_app
    from skills_mcp.paths import project_root_from_env_or_discover

    app = init_app(project_root_from_env_or_discover())

    # If the hook fires while the agent is in a different project, CWD won't match
    # app.root.  Pass CWD as the project_root so Project.md lands in the right place.
    cwd = Path.cwd().resolve()
    project_root = cwd if cwd != app.root else None

    return run_analyze(app, project_root=project_root)


def cmd_sessions_import(project_path: str | None) -> int:
    from skills_mcp.app_state import init_app
    from skills_mcp.paths import project_root_from_env_or_discover
    from skills_mcp.sessions import import_sessions

    app = init_app(project_root_from_env_or_discover())
    project_root = Path(project_path).resolve() if project_path else (Path.cwd().resolve())
    sessions_dir = app.root / ".sessions"

    print(f"sessions: importing from '{project_root.name}' -> {sessions_dir}")
    imported, skipped = import_sessions(project_root, sessions_dir)
    print(f"sessions: {imported} imported, {skipped} skipped (already imported or empty)")
    if imported:
        print(f"  -> run the learn pass to distill into skills")
    return 0


def cmd_hooks_install(provider: str) -> int:
    from skills_mcp.hooks import install_hook
    from skills_mcp.paths import project_root_from_env_or_discover

    root = project_root_from_env_or_discover()
    ok, msg = install_hook(root, provider=provider)
    if ok:
        print(f"hooks: {provider} hook installed -> {msg}")
        print(f"  analyze will now run automatically after each {provider} turn.")
    else:
        print(f"hooks: {msg}")
    return 0  # idempotent — never a fatal error


def main(argv: list[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(prog="skills-mcp", description="SkillsMCP MCP server CLI")
    parser.add_argument("--version", action="store_true", help="Print version")
    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init", help="Create skills/rules layout + config.toml")
    p_init.add_argument("path", nargs="?", default=".", type=Path)

    sub.add_parser("serve", help="Run MCP server (stdio)")

    sub.add_parser("doctor", help="Verify install and layout")

    sub.add_parser(
        "analyze",
        help="Run behavioral analysis and write <project>/.memory/dr-*.md",
    )

    p_sessions = sub.add_parser("sessions", help="Manage session files for the learn pass")
    p_sessions_sub = p_sessions.add_subparsers(dest="sessions_cmd")
    p_sess_import = p_sessions_sub.add_parser(
        "import", help="Import JSONL transcripts from ~/.claude/projects/ into sessions/"
    )
    p_sess_import.add_argument(
        "--project-path",
        default=None,
        help="Project to import from (default: CWD)",
    )

    p_hooks = sub.add_parser("hooks", help="Manage agent hooks for auto-analyze")
    p_hooks_sub = p_hooks.add_subparsers(dest="hooks_cmd")
    p_install = p_hooks_sub.add_parser("install", help="Install auto-analyze hook")
    p_install.add_argument(
        "--provider",
        choices=["claude", "gemini"],
        default="claude",
        help="Agent to install hook for (default: claude)",
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
        cmd_serve()
        return

    if args.cmd == "doctor":
        sys.exit(cmd_doctor())

    if args.cmd == "analyze":
        sys.exit(cmd_analyze())

    if args.cmd == "sessions":
        if args.sessions_cmd == "import":
            sys.exit(cmd_sessions_import(args.project_path))
        p_sessions.print_help()
        sys.exit(1)

    if args.cmd == "hooks":
        if args.hooks_cmd == "install":
            sys.exit(cmd_hooks_install(args.provider))
        p_hooks.print_help()
        sys.exit(1)

    parser.error(f"unknown command {args.cmd}")


if __name__ == "__main__":
    main()
