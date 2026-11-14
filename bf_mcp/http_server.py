#!/usr/bin/env python3
"""Authenticated Streamable HTTP adapter for the existing bookfactory tools.

The stdio entry point in :mod:`bf_mcp.server` remains unchanged. This adapter
registers the same schemas and handlers, then applies separate bearer scopes:
read tokens can call only read-only handlers; write tokens can call both.

Runtime dependencies are FastMCP and Uvicorn. No secret is stored in this
repository. Configure BOOKFACTORY_MCP_READ_TOKEN and
BOOKFACTORY_MCP_WRITE_TOKEN through the service's secret manager.
"""
from __future__ import annotations

import hmac
import inspect
import json
import os
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bf_mcp.tools import HANDLERS, TOOLS, handle  # noqa: E402


# Every tool that creates or changes a file or factory record must be listed
# here. Unknown tool names fail closed in the HTTP authorization layer.
READ_TOOLS = frozenset({
    "factory_overview",
    "list_lanes",
    "check_lane",
    "next_actions",
    "read_thesis",
    "list_specs",
    "read_template",
    "read_entries",
    "read_book",
    "read_decisions",
    "read_docs",
    "read_file",
    "list_dir",
    "inspect_verse",
    "read_rule_boxes",
})
WRITE_TOOLS = frozenset({
    "decide",
    "new_book",
    "stage",
    "audio_plan",
    "epub",
    "package",
    "quote_preview",
})
MIN_TOKEN_LENGTH = 32
MAX_REQUEST_BYTES = 1024 * 1024


def validate_tokens(read_token: str | None, write_token: str | None) -> tuple[str, str]:
    """Fail closed on absent, weak, or shared read/write credentials."""
    if not read_token or not write_token:
        raise ValueError("both BOOKFACTORY_MCP_READ_TOKEN and BOOKFACTORY_MCP_WRITE_TOKEN are required")
    if len(read_token) < MIN_TOKEN_LENGTH or len(write_token) < MIN_TOKEN_LENGTH:
        raise ValueError(f"MCP bearer tokens must each be at least {MIN_TOKEN_LENGTH} characters")
    if not read_token.isascii() or not write_token.isascii():
        raise ValueError("MCP bearer tokens must use ASCII characters")
    if hmac.compare_digest(read_token, write_token):
        raise ValueError("read and write bearer tokens must be different")
    return read_token, write_token


def _tool_scope(message: Any) -> str:
    """Return the strongest scope required by one JSON-RPC message."""
    if not isinstance(message, dict):
        return "invalid"
    method = message.get("method")
    if method != "tools/call":
        return "read"
    params = message.get("params")
    name = params.get("name") if isinstance(params, dict) else None
    if name in READ_TOOLS:
        return "read"
    if name in WRITE_TOOLS:
        return "write"
    # New or malformed tools require write authorization until explicitly
    # classified; an accidental omission must never become a reader bypass.
    return "invalid"


def _request_scope(body: bytes) -> str:
    if not body:
        return "read"
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "invalid"
    messages = payload if isinstance(payload, list) else [payload]
    scopes = [_tool_scope(message) for message in messages]
    if not scopes or "invalid" in scopes:
        return "invalid"
    return "write" if "write" in scopes else "read"


class BearerScopeMiddleware:
    """ASGI bearer gate for MCP's Streamable HTTP request/response transport."""

    def __init__(self, app: Callable[..., Awaitable[None]], read_token: str, write_token: str):
        self.app = app
        self.read_token, self.write_token = validate_tokens(read_token, write_token)

    @staticmethod
    async def _respond(send: Callable[..., Awaitable[None]], status: int, message: str) -> None:
        body = json.dumps({"error": message}, separators=(",", ":")).encode()
        headers = [(b"content-type", b"application/json"),
                   (b"content-length", str(len(body)).encode())]
        if status == 401:
            headers.append((b"www-authenticate", b'Bearer realm="bookfactory-mcp"'))
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})

    async def __call__(self, scope: dict, receive: Callable[..., Awaitable[dict]],
                       send: Callable[..., Awaitable[None]]) -> None:
        if scope.get("type") != "http" or scope.get("path", "").rstrip("/") != "/mcp":
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        authorization = headers.get(b"authorization", b"").decode("latin-1")
        scheme, _, supplied = authorization.partition(" ")
        if scheme.lower() != "bearer" or not supplied:
            await self._respond(send, 401, "bearer token required")
            return
        has_read = hmac.compare_digest(supplied, self.read_token)
        has_write = hmac.compare_digest(supplied, self.write_token)
        if not has_read and not has_write:
            await self._respond(send, 401, "invalid bearer token")
            return

        request_body = b""
        if scope.get("method", "GET").upper() == "POST":
            chunks: list[bytes] = []
            size = 0
            while True:
                event = await receive()
                if event["type"] == "http.disconnect":
                    return
                chunk = event.get("body", b"")
                size += len(chunk)
                if size > MAX_REQUEST_BYTES:
                    await self._respond(send, 413, "MCP request exceeds size limit")
                    return
                chunks.append(chunk)
                if not event.get("more_body", False):
                    break
            request_body = b"".join(chunks)

            required = _request_scope(request_body)
            if required == "invalid":
                await self._respond(send, 403, "unknown or malformed tool call; authorization denied")
                return
            if required == "write" and not has_write:
                await self._respond(send, 403, "write-scoped bearer token required")
                return

        if request_body:
            replayed = False

            async def replay_receive() -> dict:
                nonlocal replayed
                if not replayed:
                    replayed = True
                    return {"type": "http.request", "body": request_body, "more_body": False}
                return await receive()

            await self.app(scope, replay_receive, send)
        else:
            await self.app(scope, receive, send)


def _python_type(schema: dict[str, Any]) -> Any:
    kind = schema.get("type")
    if kind == "array":
        item_type = _python_type(schema.get("items") or {})
        return list[item_type]
    if kind == "string":
        return str
    if kind == "integer":
        return int
    if kind == "number":
        return float
    if kind == "boolean":
        return bool
    return Any


def _make_tool(name: str, description: str, schema: dict[str, Any]) -> Callable[..., dict]:
    """Create a typed FastMCP wrapper while dispatching to the canonical handler."""
    input_schema = schema.get("inputSchema") or {}
    properties = input_schema.get("properties") or {}
    required = set(input_schema.get("required") or [])
    parameters = []
    annotations: dict[str, Any] = {}
    for parameter_name, parameter_schema in properties.items():
        annotation = _python_type(parameter_schema)
        annotations[parameter_name] = annotation
        default = inspect.Parameter.empty if parameter_name in required else None
        parameters.append(inspect.Parameter(
            parameter_name,
            inspect.Parameter.KEYWORD_ONLY,
            default=default,
            annotation=annotation,
        ))

    def dispatch(**kwargs: Any) -> dict:
        return handle(name, kwargs)

    dispatch.__name__ = name
    dispatch.__qualname__ = name
    dispatch.__doc__ = description
    annotations["return"] = dict
    dispatch.__annotations__ = annotations
    dispatch.__signature__ = inspect.Signature(
        parameters, return_annotation=dict
    )
    return dispatch


def create_http_app(read_token: str, write_token: str, fastmcp_factory: Any = None) -> Any:
    """Build the FastMCP app with all existing tools and scoped bearer auth."""
    read_token, write_token = validate_tokens(read_token, write_token)
    if (READ_TOOLS & WRITE_TOOLS
            or READ_TOOLS | WRITE_TOOLS != set(HANDLERS)
            or set(TOOLS) != set(HANDLERS)):
        raise RuntimeError("MCP tool authorization/schema inventory is incomplete; classify every handler explicitly")
    if fastmcp_factory is None:
        from fastmcp import FastMCP
        fastmcp_factory = FastMCP

    mcp = fastmcp_factory("bookfactory")
    for name, handler in HANDLERS.items():
        schema = TOOLS[name]
        description = schema.get("description") or handler.__doc__ or name
        mcp.tool()(_make_tool(name, description, schema))
    app = mcp.http_app(path="/mcp")
    return BearerScopeMiddleware(app, read_token, write_token)


def main() -> None:
    read_token = os.environ.get("BOOKFACTORY_MCP_READ_TOKEN")
    write_token = os.environ.get("BOOKFACTORY_MCP_WRITE_TOKEN")
    validate_tokens(read_token, write_token)
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("HTTP serving requires FastMCP and Uvicorn; install the pinned MCP runtime dependencies") from exc
    app = create_http_app(read_token, write_token)
    host = os.environ.get("BOOKFACTORY_MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("BOOKFACTORY_MCP_PORT", "8950"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
