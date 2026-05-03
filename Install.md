Perform a complete installation of the AgentMCP server from the current
directory.

## Bootstrapping note

`CLAUDE.md` is loaded by Claude Code at startup with no server required.
It contains the session-start ritual and prompt-rewriting behavior. This
is the only reliable hook — rules in `rules/active/` are served via the
MCP server's `list_rules` tool and are unavailable if the server is not
running. Always ensure `CLAUDE.md` is present before relying on any
server-side rules.

## Steps

1. Server setup: install the package in editable mode (`pip install -e .`),
   initialize the server (`agent-mcp init .`), and pull the necessary
   embedding models (`agent-mcp models pull`).

2. MCP integration: add the agent-mcp server to Claude Desktop, Antigravity,
   and Cursor.
   - Locate their MCP configuration files (typically in `%APPDATA%` or
     `~/.cursor`).
   - Add an entry with `command: agent-mcp` and `args: ["serve"]`.
   - Set the `AGENT_MCP_ROOT` environment variable to point to this directory.

3. Bootstrap hook: confirm `CLAUDE.md` exists in the project root. It is
   the native Claude Code bootstrap and fires before any MCP server starts.
   Do not put session-start logic only in `rules/active/` — those rules
   require the server to be running.

4. Permissions: you have permission to access the system's application data
   and home directory to locate and modify configuration files.

Report back with a summary of files modified and confirm the server is
healthy via `agent-mcp doctor`.
