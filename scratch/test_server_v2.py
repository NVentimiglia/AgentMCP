
import subprocess
import json
import time
import os
import sys

def test_server():
    env = os.environ.copy()
    env["AGENT_MCP_ROOT"] = "D:\\Projects\\AgentMCP"
    
    # We'll use a larger timeout and non-blocking reads if possible, 
    # but since we're on Windows, we'll use a simpler approach:
    # We'll write the request and then read from the pipe in a thread or just use a small timeout.
    
    print("Starting server...")
    process = subprocess.Popen(
        ["agent-mcp", "serve"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        bufsize=0 # Unbuffered
    )

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "list_skills",
            "arguments": {}
        }
    }

    print("Sending list_tools request...")
    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()

    print("Waiting for response...")
    # We'll try to read one character at a time to avoid blocking on a whole line
    # But stdout.read(1) still blocks.
    
    # Instead, we'll use process.communicate() with a timeout if possible (Python 3.3+)
    try:
        stdout, stderr = process.communicate(input=json.dumps(request) + "\n", timeout=10)
        print(f"Stdout: {stdout[:200]}")
        print(f"Stderr: {stderr[:200]}")
    except subprocess.TimeoutExpired:
        print("Timeout reached!")
        process.kill()
        stdout, stderr = process.communicate()
        print(f"Stdout so far: {stdout[:200]}")
        print(f"Stderr so far: {stderr[:200]}")

if __name__ == "__main__":
    test_server()
