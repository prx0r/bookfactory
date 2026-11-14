from __future__ import annotations

import asyncio
import inspect
import json
import unittest
from unittest.mock import patch

from bf_mcp import http_server
from bf_mcp.tools import HANDLERS


READ_TOKEN = "r" * 48
WRITE_TOKEN = "w" * 48


class EchoASGI:
    def __init__(self):
        self.calls = []

    async def __call__(self, scope, receive, send):
        body = b""
        while True:
            event = await receive()
            body += event.get("body", b"")
            if not event.get("more_body", False):
                break
        self.calls.append((scope, body))
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


async def request(app, token=None, payload=None, method="POST", path="/mcp"):
    events = []
    if method == "POST":
        body = json.dumps(payload).encode() if payload is not None else b""
        events.append({"type": "http.request", "body": body, "more_body": False})
    sent = []

    async def receive():
        if events:
            return events.pop(0)
        return {"type": "http.disconnect"}

    async def send(event):
        sent.append(event)

    headers = [] if token is None else [(b"authorization", f"Bearer {token}".encode())]
    scope = {"type": "http", "method": method, "path": path, "headers": headers}
    await app(scope, receive, send)
    status = next(event["status"] for event in sent if event["type"] == "http.response.start")
    body = b"".join(event.get("body", b"") for event in sent if event["type"] == "http.response.body")
    return status, body


def call(tool_name):
    return {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": tool_name, "arguments": {}}}


class FakeFastMCP:
    def __init__(self, name):
        self.name = name
        self.tools = {}
        self.asgi = EchoASGI()

    def tool(self):
        def register(fn):
            self.tools[fn.__name__] = fn
            return fn
        return register

    def http_app(self, path):
        self.path = path
        return self.asgi


class BearerScopeTests(unittest.TestCase):
    def test_both_tokens_required_and_must_be_distinct_strong_secrets(self):
        for pair in ((None, WRITE_TOKEN), (READ_TOKEN, None), ("short", WRITE_TOKEN),
                     (READ_TOKEN, READ_TOKEN)):
            with self.subTest(pair=pair), self.assertRaises(ValueError):
                http_server.validate_tokens(*pair)

    def test_read_token_cannot_call_mutating_tool(self):
        downstream = EchoASGI()
        app = http_server.BearerScopeMiddleware(downstream, READ_TOKEN, WRITE_TOKEN)
        status, body = asyncio.run(request(app, READ_TOKEN, call("package")))
        self.assertEqual(status, 403)
        self.assertIn(b"write-scoped", body)
        self.assertEqual(downstream.calls, [])

    def test_write_token_can_call_mutating_tool_and_body_is_forwarded(self):
        downstream = EchoASGI()
        app = http_server.BearerScopeMiddleware(downstream, READ_TOKEN, WRITE_TOKEN)
        payload = call("package")
        status, _ = asyncio.run(request(app, WRITE_TOKEN, payload))
        self.assertEqual(status, 200)
        self.assertEqual(downstream.calls[0][1], json.dumps(payload).encode())

    def test_read_token_can_call_read_tool_and_write_token_can_read(self):
        for token in (READ_TOKEN, WRITE_TOKEN):
            downstream = EchoASGI()
            app = http_server.BearerScopeMiddleware(downstream, READ_TOKEN, WRITE_TOKEN)
            status, _ = asyncio.run(request(app, token, call("factory_overview")))
            self.assertEqual(status, 200)
            self.assertEqual(len(downstream.calls), 1)

    def test_missing_or_invalid_token_is_401(self):
        for token in (None, "x" * 48):
            downstream = EchoASGI()
            app = http_server.BearerScopeMiddleware(downstream, READ_TOKEN, WRITE_TOKEN)
            status, _ = asyncio.run(request(app, token, call("factory_overview")))
            self.assertEqual(status, 401)
            self.assertEqual(downstream.calls, [])

    def test_unknown_tool_and_malformed_body_fail_closed(self):
        for payload in (call("new_unclassified_tool"), b"not-json"):
            downstream = EchoASGI()
            app = http_server.BearerScopeMiddleware(downstream, READ_TOKEN, WRITE_TOKEN)
            if isinstance(payload, bytes):
                events = [{"type": "http.request", "body": payload, "more_body": False}]
                sent = []
                async def receive():
                    return events.pop(0) if events else {"type": "http.disconnect"}
                async def send(event):
                    sent.append(event)
                async def run():
                    await app({"type": "http", "method": "POST", "path": "/mcp",
                               "headers": [(b"authorization", f"Bearer {READ_TOKEN}".encode())]},
                              receive, send)
                asyncio.run(run())
                status = next(x["status"] for x in sent if x["type"] == "http.response.start")
            else:
                status, _ = asyncio.run(request(app, READ_TOKEN, payload))
            self.assertEqual(status, 403)
            self.assertEqual(downstream.calls, [])

    def test_mixed_batch_requires_write_scope(self):
        downstream = EchoASGI()
        app = http_server.BearerScopeMiddleware(downstream, READ_TOKEN, WRITE_TOKEN)
        payload = [call("factory_overview"), call("decide")]
        status, _ = asyncio.run(request(app, READ_TOKEN, payload))
        self.assertEqual(status, 403)
        self.assertEqual(downstream.calls, [])

    def test_dynamic_adapter_registers_every_existing_handler_and_schema(self):
        instances = []
        class Factory(FakeFastMCP):
            def __init__(self, name):
                super().__init__(name)
                instances.append(self)

        app = http_server.create_http_app(READ_TOKEN, WRITE_TOKEN, Factory)
        instance = instances[0]
        self.assertEqual(set(instance.tools), set(HANDLERS))
        self.assertEqual(instance.path, "/mcp")
        self.assertEqual(http_server.WRITE_TOOLS | http_server.READ_TOOLS, set(HANDLERS))
        self.assertEqual(len(http_server.WRITE_TOOLS), 7)
        signature = inspect.signature(instance.tools["read_entries"])
        self.assertIn("book", signature.parameters)
        self.assertIs(signature.parameters["book"].default, inspect.Parameter.empty)
        self.assertEqual(signature.parameters["entry_id"].default, None)
        self.assertIsNotNone(app)

    def test_new_handler_must_be_classified_before_server_starts(self):
        with patch.dict(http_server.HANDLERS, {"future_mutator": lambda args: {"ok": True}}):
            with self.assertRaisesRegex(RuntimeError, "authorization/schema inventory"):
                http_server.create_http_app(READ_TOKEN, WRITE_TOKEN, FakeFastMCP)


if __name__ == "__main__":
    unittest.main()
