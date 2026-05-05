
from mcp.server.fastmcp import FastMCP
import sys

mcp = FastMCP("test")

@mcp.tool()
def hello():
    return "world"

if __name__ == "__main__":
    print("Starting test server...", file=sys.stderr)
    mcp.run(transport="stdio")
