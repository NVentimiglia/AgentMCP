
import time
import sys
from pathlib import Path

sys.path.append(str(Path("d:/Projects/AgentMCP/src")))

from agent_mcp.memory.store import MemoryStore
from agent_mcp.app_state import init_app

print("Initializing app...")
app = init_app(Path("d:/Projects/AgentMCP"))

print("Attempting to initialize MemoryStore (Chroma)...")
start = time.time()
try:
    store = MemoryStore.from_app(app)
    print(f"MemoryStore initialized in {time.time() - start:.2f} seconds")
except Exception as e:
    print(f"Failed: {e}")
