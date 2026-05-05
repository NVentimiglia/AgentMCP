
import subprocess
import json
import time
import os

def test_proper_mcp():
    env = os.environ.copy()
    env["AGENT_MCP_ROOT"] = "D:\\Projects\\AgentMCP"
    
    process = subprocess.Popen(
        ["agent-mcp", "serve"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        bufsize=0
    )

    def send(method, params, req_id):
        req = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
        process.stdin.write(json.dumps(req) + "\n")
        process.stdin.flush()

    def receive():
        line = process.stdout.readline()
        if line:
            return json.loads(line)
        return None

    try:
        print("Sending initialize...")
        send("initialize", {
            "protocolVersion": "1.0",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }, 1)
        resp = receive()
        print(f"Initialize response: {resp}")

        print("Sending initialized notification...")
        # Notifications don't have IDs and don't expect responses
        req = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        process.stdin.write(json.dumps(req) + "\n")
        process.stdin.flush()

        print("Sending list_skills tool call...")
        send("tools/call", {
            "name": "list_skills",
            "arguments": {}
        }, 2)
        resp = receive()
        print(f"list_skills response: {resp}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        process.terminate()

if __name__ == "__main__":
    test_proper_mcp()
