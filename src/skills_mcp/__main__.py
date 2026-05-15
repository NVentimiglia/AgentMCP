"""Allow ``python -m skills_mcp serve`` (avoids stale ``agent-mcp.exe`` on PATH)."""

from __future__ import annotations

from skills_mcp.cli import main

if __name__ == "__main__":
    main()
