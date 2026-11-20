"""Run a Python file inside the user's open Blender (MCP for Blender add-on, port 9876).
Usage: python tools/blender_gui.py <script.py>   -> prints the add-on's JSON reply.
Inside the script, assign a dict to `result` to get data back."""
import json, socket, sys

code = open(sys.argv[1], encoding="utf-8").read()
s = socket.create_connection(("127.0.0.1", 9876), timeout=600)
s.sendall(json.dumps({"type": "execute_code", "params": {"code": code}}).encode())
buf = b""
while True:
    chunk = s.recv(65536)
    if not chunk:
        break
    buf += chunk
    try:
        reply = json.loads(buf)  # add-on sends one JSON object, no framing
        break
    except json.JSONDecodeError:
        continue
print(json.dumps(reply)[:4000])
