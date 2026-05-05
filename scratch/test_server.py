
import subprocess
import json
import time

def test_server():
    import os
    env = os.environ.copy()
    env["AGENT_MCP_ROOT"] = "D:\\Projects\\AgentMCP"
    process = subprocess.Popen(
        ["agent-mcp", "serve"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )

    # MCP JSON-RPC request for list_tools
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "list_tools",
        "params": {}
    }

    print("Sending list_tools request...")
    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()

    start = time.time()
    print("Waiting for response (timeout 30s)...")
    while time.time() - start < 30:
        line = process.stdout.readline()
        if line:
            print(f"Received response: {line[:200]}...")
            return
        
        # Check stderr for errors (non-blocking)
        import msvcrt
        if msvcrt.kbhit(): # Wait, this is for stdin.
            pass
        
        # We'll just check if the process is still alive
        if process.poll() is not None:
            print(f"Process exited with code {process.returncode}")
            print(f"Stderr: {process.stderr.read()}")
            return
        time.sleep(0.1)
    else:
        print("Timeout waiting for response after 30s")

    process.terminate()

if __name__ == "__main__":
    test_server()
