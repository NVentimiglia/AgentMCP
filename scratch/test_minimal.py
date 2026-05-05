
import subprocess
import json
import time
import os

def test_minimal():
    env = os.environ.copy()
    process = subprocess.Popen(
        ["python", "d:/Projects/AgentMCP/scratch/minimal_mcp.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "list_tools",
        "params": {}
    }

    print("Sending list_tools request to minimal server...")
    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()

    start = time.time()
    while time.time() - start < 5:
        line = process.stdout.readline()
        if line:
            print(f"Received response: {line}")
            break
        
        err = process.stderr.readline()
        if err:
            print(f"Error output: {err.strip()}")
    else:
        print("Timeout waiting for response")

    process.terminate()

if __name__ == "__main__":
    test_minimal()
