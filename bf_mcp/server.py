#!/usr/bin/env python3
"""bookfactory MCP server (stdio JSON-RPC).

Same wire format as neuro_mix/mcp/server.py (stdio JSON-RPC).

OpenCode only:
  ~/.config/opencode/mcp.json + opencode.jsonc → mcp.bookfactory

Echo test:
  echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python3 server.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure package imports work when run as a file
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bf_mcp.tools import HANDLERS, TOOLS, handle  # noqa: E402


def send(msg: dict) -> None:
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        if msg.get("jsonrpc") != "2.0":
            continue
        mid = msg.get("id")
        method = msg.get("method")
        if mid is None:
            continue

        if method == "initialize":
            send({
                "jsonrpc": "2.0",
                "id": mid,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "bookfactory",
                        "version": "0.1.0",
                        "description": "Publishing factory: thesis, decisions, stages, gate, lessons",
                    },
                },
            })
        elif method == "notifications/initialized":
            continue
        elif method == "ping":
            send({"jsonrpc": "2.0", "id": mid, "result": {}})
        elif method == "tools/list":
            tools = []
            for name, schema in TOOLS.items():
                t = dict(schema)
                t["name"] = name
                tools.append(t)
            send({"jsonrpc": "2.0", "id": mid, "result": {"tools": tools}})
        elif method == "tools/call":
            params = msg.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            try:
                result = handle(name, args)
            except Exception as exc:
                result = {"ok": False, "error": str(exc)}
            text = json.dumps(result, ensure_ascii=False, indent=2)
            send({
                "jsonrpc": "2.0",
                "id": mid,
                "result": {"content": [{"type": "text", "text": text}]},
            })
        else:
            send({
                "jsonrpc": "2.0",
                "id": mid,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({"unsupported": method}),
                    }]
                },
            })


if __name__ == "__main__":
    main()
