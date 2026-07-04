"""Real MCP server entrypoint for the MemoryCore MVP.

This module binds the existing fixture-only ``memorycore.mcp_surface`` contract
to the Python MCP SDK. It does not change backend adapter behavior and does not
call live QMD, Lossless-Claw, Burrow, OpenClaw, or private memory stores.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from memorycore.mcp_surface import TOOL_DEFINITIONS, call_tool

try:  # pragma: no cover - dependency absence is exercised by validator status.
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None  # type: ignore[assignment]


SERVER_NAME = "memorycore"
SUPPORTED_TRANSPORTS = ("stdio", "sse", "streamable-http")


def dependency_status() -> dict[str, Any]:
    """Return a structured dependency status for validators and operators."""

    return {
        "status": "available" if FastMCP is not None else "missing",
        "package": "mcp",
        "server_api": "mcp.server.fastmcp.FastMCP",
        "transport": list(SUPPORTED_TRANSPORTS),
    }


def create_server(name: str = SERVER_NAME) -> Any:
    """Create a FastMCP server with MemoryCore MVP tools registered."""

    if FastMCP is None:
        raise RuntimeError("missing MCP server library: install package 'mcp'")

    server = FastMCP(name)
    _register_tools(server)
    return server


def _register_tools(server: Any) -> None:
    by_name = {tool["name"]: tool for tool in TOOL_DEFINITIONS}

    @server.tool(
        name="memorycore_search",
        description=by_name["memorycore_search"]["description"],
        structured_output=False,
    )
    def memorycore_search(
        query: str,
        backend: str | None = None,
        intent: str = "file_corpus_recall",
        limit: int = 5,
    ) -> dict[str, Any]:
        arguments: dict[str, Any] = {"query": query, "intent": intent, "limit": limit}
        if backend is not None:
            arguments["backend"] = backend
        return _call_surface("memorycore_search", arguments)

    @server.tool(
        name="memorycore_get",
        description=by_name["memorycore_get"]["description"],
        structured_output=False,
    )
    def memorycore_get(pointer_id: str, backend: str = "qmd") -> dict[str, Any]:
        return _call_surface("memorycore_get", {"pointer_id": pointer_id, "backend": backend})

    @server.tool(
        name="memorycore_verify",
        description=by_name["memorycore_verify"]["description"],
        structured_output=False,
    )
    def memorycore_verify(
        pointer_id: str,
        backend: str = "mock_healthy",
        state: str = "verified",
    ) -> dict[str, Any]:
        return _call_surface(
            "memorycore_verify",
            {"pointer_id": pointer_id, "backend": backend, "state": state},
        )

    @server.tool(
        name="memorycore_health",
        description=by_name["memorycore_health"]["description"],
        structured_output=False,
    )
    def memorycore_health() -> dict[str, Any]:
        return _call_surface("memorycore_health", {})

    @server.tool(
        name="memorycore_remember",
        description=by_name["memorycore_remember"]["description"],
        structured_output=False,
    )
    def memorycore_remember(
        memory_type: str,
        content_ref: str | None = None,
        content: str | None = None,
        pointer_id: str | None = None,
        summary_id: str | None = None,
        verification: str = "unknown",
        client: str = "mcp",
    ) -> dict[str, Any]:
        arguments: dict[str, Any] = {
            "memory_type": memory_type,
            "verification": verification,
            "client": client,
        }
        if content_ref is not None:
            arguments["content_ref"] = content_ref
        if content is not None:
            arguments["content"] = content
        if pointer_id is not None:
            arguments["pointer_id"] = pointer_id
        if summary_id is not None:
            arguments["summary_id"] = summary_id
        return _call_surface("memorycore_remember", arguments)

    @server.tool(
        name="memorycore_recall",
        description=by_name["memorycore_recall"]["description"],
        structured_output=False,
    )
    def memorycore_recall(
        record_id: str | None = None,
        pointer_id: str | None = None,
        client: str = "mcp",
    ) -> dict[str, Any]:
        arguments: dict[str, Any] = {"client": client}
        if record_id is not None:
            arguments["record_id"] = record_id
        if pointer_id is not None:
            arguments["pointer_id"] = pointer_id
        return _call_surface("memorycore_recall", arguments)

    @server.tool(
        name="memorycore_cache_search",
        description=by_name["memorycore_cache_search"]["description"],
        structured_output=False,
    )
    def memorycore_cache_search(
        query: str,
        memory_type: str | None = None,
        limit: int = 5,
        client: str = "mcp",
    ) -> dict[str, Any]:
        arguments: dict[str, Any] = {"query": query, "limit": limit, "client": client}
        if memory_type is not None:
            arguments["memory_type"] = memory_type
        return _call_surface("memorycore_cache_search", arguments)

    @server.tool(
        name="memorycore_flush",
        description=by_name["memorycore_flush"]["description"],
        structured_output=False,
    )
    def memorycore_flush(client: str = "mcp") -> dict[str, Any]:
        return _call_surface("memorycore_flush", {"client": client})


def _call_surface(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        audit_log = os.environ.get("MEMORYCORE_MCP_AUDIT_LOG")
        cache_db = os.environ.get("MEMORYCORE_CACHE_DB")
        return call_tool(
            tool_name,
            arguments,
            audit_log=Path(audit_log) if audit_log else None,
            cache_db=Path(cache_db) if cache_db else None,
        )
    except Exception as exc:  # noqa: BLE001 - MCP boundary returns structured errors.
        return _server_error(tool_name, exc)


def _server_error(tool_name: str, exc: Exception) -> dict[str, Any]:
    return {
        "operation": tool_name.removeprefix("memorycore_") or "unknown",
        "status": "error",
        "results": [],
        "error": {
            "code": "MCP_SERVER_TOOL_ERROR",
            "category": "client_surface",
            "message": "MemoryCore MCP server tool call failed.",
            "details": {
                "tool_name": tool_name,
                "exception_type": exc.__class__.__name__,
            },
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m memorycore.mcp_server")
    parser.add_argument(
        "--transport",
        choices=SUPPORTED_TRANSPORTS,
        default="stdio",
        help="MCP transport to serve; stdio is the default agent launch mode.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print dependency and tool registration status without starting the server.",
    )
    args = parser.parse_args(argv)

    if args.check:
        status = dependency_status()
        if status["status"] == "available":
            status = {**status, "tools": [tool["name"] for tool in TOOL_DEFINITIONS]}
        print(json.dumps(status, indent=2, sort_keys=True))
        return 0 if status["status"] == "available" else 2

    server = create_server()
    server.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
