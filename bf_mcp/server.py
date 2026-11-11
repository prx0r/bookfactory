#!/usr/bin/env python3
"""bookfactory MCP server.

Two front-ends over the same tool surface (bf_mcp.tools):

  stdio (default, local agents):
    python3 bf_mcp/server.py

  Streamable HTTP (remote agents / ChatGPT connectors):
    python3 bf_mcp/server.py --serve-http --host 127.0.0.1 --port 8932

HTTP auth (optional shared secret):
    BOOKFACTORY_MCP_TOKEN=<secret>
      -> Authorization: Bearer <secret>   or   ?token=<secret>

The wire format matches neuro_mix/mcp/server.py for stdio. HTTP is a small
stateless JSON-RPC endpoint: POST one message (or a batch), get JSON back.

Echo test:
  echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python3 server.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Ensure package imports work when run as a file
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bf_mcp.tools import TOOLS, handle  # noqa: E402

PROTOCOL = "2024-11-05"
SERVER_INFO = {
    "name": "bookfactory",
    "version": "0.1.0",
    "description": "Publishing factory: thesis, decisions, stages, gate, lessons",
}


def _result(mid, result):
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def _error(mid, code, message):
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}}


def dispatch(msg: dict):
    """Handle one JSON-RPC message. Returns a response dict, or None for notifications."""
    if not isinstance(msg, dict):
        return _error(None, -32600, "invalid request")
    method = msg.get("method")
    mid = msg.get("id")

    # Notifications carry no id and must not be answered.
    if mid is None or (isinstance(method, str) and method.startswith("notifications/")):
        return None

    if msg.get("jsonrpc") != "2.0":
        return _error(mid, -32600, "invalid request")

    if method == "initialize":
        params = msg.get("params") or {}
        # Echo the client's protocol version when offered (both 2024-11-05 and
        # 2025-06-18 clients work with this tool-only server).
        proto = params.get("protocolVersion") or PROTOCOL
        return _result(mid, {
            "protocolVersion": proto,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })

    if method == "ping":
        return _result(mid, {})

    if method == "tools/list":
        tools = []
        for name, schema in TOOLS.items():
            t = dict(schema)
            t["name"] = name
            tools.append(t)
        return _result(mid, {"tools": tools})

    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        try:
            result = handle(name, args)
        except Exception as exc:  # handle() already catches; belt and braces
            result = {"ok": False, "error": str(exc)}
        return _result(mid, {
            "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
        })

    return _result(mid, {
        "content": [{"type": "text", "text": json.dumps({"unsupported": method})}]
    })


# --------------------------------------------------------------------------- #
# stdio
# --------------------------------------------------------------------------- #

def serve_stdio() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        resp = dispatch(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


# --------------------------------------------------------------------------- #
# Streamable HTTP (stateless)
# --------------------------------------------------------------------------- #

class _Handler(BaseHTTPRequestHandler):
    server_version = "bookfactory-mcp/0.1.0"
    protocol_version = "HTTP/1.1"
    token = None  # set by main()

    def log_message(self, fmt, *args):  # quiet, to stderr
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, obj=None, extra: dict | None = None) -> None:
        body = b"" if obj is None else json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Mcp-Session-Id")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _authorised(self) -> bool:
        if not self.token:
            return True
        if self.headers.get("Authorization", "") == f"Bearer {self.token}":
            return True
        q = parse_qs(urlparse(self.path).query)
        return q.get("token", [None])[0] == self.token

    def do_OPTIONS(self):
        self._send(204)

    def do_GET(self):
        # This server has no server-initiated SSE stream; clients must POST.
        self._send(405, {"error": "use POST for JSON-RPC (Streamable HTTP)"}, {"Allow": "POST"})

    def do_DELETE(self):
        self._send(204)

    def do_POST(self):
        if not self._authorised():
            self._send(401, {"error": "unauthorized"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw.decode("utf-8") or "null")
        except Exception:
            self._send(400, _error(None, -32700, "parse error"))
            return
        try:
            if isinstance(payload, list):
                out = [r for r in (dispatch(m) for m in payload) if r is not None]
                if not out:
                    self._send(202)
                else:
                    self._send(200, out)
            else:
                resp = dispatch(payload)
                if resp is None:
                    self._send(202)
                else:
                    self._send(200, resp)
        except Exception as exc:
            mid = payload.get("id") if isinstance(payload, dict) else None
            self._send(500, _error(mid, -32603, str(exc)))


def serve_http(host: str, port: int) -> None:
    _Handler.token = (os.environ.get("BOOKFACTORY_MCP_TOKEN", "") or "").strip() or None
    httpd = ThreadingHTTPServer((host, port), _Handler)
    sys.stderr.write(
        "bookfactory MCP (streamable http) on http://%s:%d auth=%s\n"
        % (host, port, "on" if _Handler.token else "off")
    )
    sys.stderr.flush()
    httpd.serve_forever()


def main() -> None:
    ap = argparse.ArgumentParser(description="bookfactory MCP server")
    ap.add_argument("--serve-http", action="store_true", help="serve Streamable HTTP instead of stdio")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8932)
    args = ap.parse_args()
    if args.serve_http:
        serve_http(args.host, args.port)
    else:
        serve_stdio()


if __name__ == "__main__":
    main()
