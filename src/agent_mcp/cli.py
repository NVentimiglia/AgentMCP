from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path

from agent_mcp import __version__

BUNDLED = Path(__file__).resolve().parent / "bundled"


def _sync_tree(src_dir: Path, dst_dir: Path) -> None:
    if not src_dir.is_dir():
        return
    for p in src_dir.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(src_dir)
        out = dst_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if not out.is_file():
            shutil.copy2(p, out)


def cmd_init(target: Path) -> None:
    target = target.resolve()
    dirs = [
        target / "skills" / "roles",
        target / "rules" / "active",
        target / "rules" / "proposals",
        target / "memory",
        target / "state",
        target / "tests",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    cfg_dst = target / "config.toml"
    if not cfg_dst.is_file():
        shutil.copy2(BUNDLED / "config.toml", cfg_dst)

    bundled_skills = BUNDLED / "skills"
    _sync_tree(bundled_skills, target / "skills")

    changelog_dst = target / "rules" / "CHANGELOG.md"
    if not changelog_dst.is_file():
        shutil.copy2(BUNDLED / "rules" / "CHANGELOG.md", changelog_dst)

    clusters_dst = target / "state" / "clusters.json"
    if not clusters_dst.is_file():
        shutil.copy2(BUNDLED / "state" / "clusters.json", clusters_dst)


def cmd_models_pull(model: str | None) -> None:
    cache_dir = Path.home() / ".agent-mcp" / "models"
    cache_dir.mkdir(parents=True, exist_ok=True)
    embedding_model = model
    if embedding_model is None:
        try:
            from agent_mcp.config import load_config
            from agent_mcp.paths import find_project_root

            root = find_project_root()
            embedding_model = load_config(root).memory.embedding_model
        except FileNotFoundError:
            embedding_model = "BAAI/bge-small-en-v1.5"
    try:
        from fastembed import TextEmbedding
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("fastembed is required for models pull") from e
    logging.info("Pulling embedding model %s into %s", embedding_model, cache_dir)
    TextEmbedding(model_name=embedding_model, cache_dir=str(cache_dir))


def cmd_serve() -> None:
    from agent_mcp.server import run_stdio_server

    run_stdio_server()


def cmd_memory_prune() -> None:
    from agent_mcp.paths import project_root_from_env_or_discover
    from agent_mcp.app_state import init_app
    from agent_mcp.memory.store import MemoryStore

    root = project_root_from_env_or_discover()
    init_app(root)
    store = MemoryStore.from_app()
    n = store.prune()
    print(f"Pruned {n} memory entries")


def cmd_doctor() -> int:
    from agent_mcp.doctor import run_doctor

    return run_doctor()


def main(argv: list[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(prog="agent-mcp", description="AgentBridge MCP server CLI")
    parser.add_argument("--version", action="store_true", help="Print version")
    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init", help="Create AgentBridge folder layout")
    p_init.add_argument("path", nargs="?", default=".", type=Path)

    p_pull = sub.add_parser("models", help="Embedding model utilities")
    p_pull_sub = p_pull.add_subparsers(dest="models_cmd")
    p_pull_pull = p_pull_sub.add_parser("pull", help="Download fastembed model cache")
    p_pull_pull.add_argument("--model", type=str, default=None)

    sub.add_parser("serve", help="Run MCP server (stdio)")
    p_prune = sub.add_parser(
        "memory",
        help="Memory maintenance",
    )
    p_prune_sub = p_prune.add_subparsers(dest="memory_cmd")
    p_prune_sub.add_parser("prune", help="Drop stale new memories")

    sub.add_parser("doctor", help="Verify install, layout, caches")

    args = parser.parse_args(argv)
    logging.basicConfig(level=os.environ.get("AGENT_MCP_LOG_LEVEL", "INFO"))

    if args.version:
        print(__version__)
        return

    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    if args.cmd == "init":
        cmd_init(Path(args.path))
        return

    if args.cmd == "models":
        if args.models_cmd != "pull":
            p_pull.print_help()
            sys.exit(1)
        cmd_models_pull(args.model)
        return

    if args.cmd == "serve":
        cmd_serve()
        return

    if args.cmd == "memory":
        if args.memory_cmd != "prune":
            p_prune.print_help()
            sys.exit(1)
        cmd_memory_prune()
        return

    if args.cmd == "doctor":
        sys.exit(cmd_doctor())

    parser.error(f"unknown command {args.cmd}")


if __name__ == "__main__":
    main()
