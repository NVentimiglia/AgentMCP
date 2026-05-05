
import time
import sys
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path("d:/Projects/AgentMCP/src")))

from agent_mcp.server import configure

start = time.time()
print("Starting configuration...")
try:
    configure(Path("d:/Projects/AgentMCP"))
    print(f"Configuration finished in {time.time() - start:.2f} seconds")
    
    from agent_mcp.server import memory_search
    print("Testing memory_search...")
    start_search = time.time()
    res = memory_search("test query")
    print(f"memory_search finished in {time.time() - start_search:.2f} seconds")
    print(f"Results: {len(res)} characters")
except Exception as e:
    print(f"Configuration failed: {e}")
