#!/usr/bin/env python3
"""Validate the real MCP server entrypoint without live backend calls.

This check imports ``memorycore.mcp_server``, builds the FastMCP server when the
SDK is installed, and calls the registered tools through the server's tool
manager. It does not start an OpenClaw smoke test, call live QMD/LCM backends,
or mutate runtime configuration.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore import mcp_server  # noqa: E402
from memorycore.mcp_surface import TOOL_DEFINITIONS, call_tool  # noqa: E402


EXPECTED_TOOLS = {tool["name"] for tool in TOOL_DEFINITIONS}
PRIVATE_FIELD_MARKERS = ('"snippet"', '"content"', '"citations"', '"summary"', '"answer"', '"text"')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


async def validate_server() -> None:
    status = mcp_server.dependency_status()
    if status["status"] != "available":
        raise RuntimeError(
            "MEMORYCORE_MCP_SERVER_ENTRYPOINT_BLOCKED: "
            f"missing {status['package']} server API {status['server_api']}"
        )

    server = mcp_server.create_server()
    tools = await server.list_tools()
    tool_names = {tool.name for tool in tools}
    require(tool_names == EXPECTED_TOOLS, f"MCP server tool names changed: {sorted(tool_names)}")

    for tool in tools:
        require(tool.description, f"{tool.name} should keep the mcp_surface description")
        require(tool.inputSchema["type"] == "object", f"{tool.name} should expose object arguments")

    health = await _call_raw(server, "memorycore_health", {})
    require(health["status"] == "ok", "server health tool should succeed")
    require({item["backend_id"] for item in health["results"]} >= {"qmd", "lossless_claw", "mock_healthy"}, "server health backend list changed")

    search_args = {"query": "alpha-river-contract-fixture", "intent": "file_corpus_recall", "limit": 5}
    server_search = await _call_raw(server, "memorycore_search", search_args)
    surface_search = call_tool("memorycore_search", search_args)
    require(_core_result(server_search) == _core_result(surface_search), "server search diverged from mcp_surface")

    get_args = {"pointer_id": "fixtures/corpus/project-alpha.md", "backend": "qmd"}
    server_get = await _call_raw(server, "memorycore_get", get_args)
    surface_get = call_tool("memorycore_get", get_args)
    require(_core_result(server_get) == _core_result(surface_get), "server get diverged from mcp_surface")

    verify_args = {"pointer_id": "fixtures/corpus/project-alpha.md", "backend": "mock_healthy", "state": "verified"}
    server_verify = await _call_raw(server, "memorycore_verify", verify_args)
    surface_verify = call_tool("memorycore_verify", verify_args)
    require(_core_result(server_verify) == _core_result(surface_verify), "server verify diverged from mcp_surface")

    error = await _call_raw(server, "memorycore_search", {"query": ""})
    require(error["status"] == "error", "server should serialize mcp_surface exceptions")
    require(error["error"]["code"] == "MCP_SERVER_TOOL_ERROR", "server error code changed")
    serialized_error = json.dumps(error, sort_keys=True)
    for marker in PRIVATE_FIELD_MARKERS:
        require(marker not in serialized_error, f"server error leaked private field marker {marker}")


async def _call_raw(server: Any, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    result = await server._tool_manager.call_tool(tool_name, arguments, convert_result=False)  # noqa: SLF001
    require(isinstance(result, dict), f"{tool_name} should return a structured dict")
    return result


def _core_result(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if key not in {"request_id", "audit_id"}}


def validate_check_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "memorycore.mcp_server", "--check"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    require(completed.returncode == 0, f"mcp_server --check failed: {completed.stderr.strip() or completed.stdout.strip()}")
    status = json.loads(completed.stdout)
    require(status["status"] == "available", "mcp_server --check should report available SDK")
    require(set(status["tools"]) == EXPECTED_TOOLS, "mcp_server --check tool list changed")


def main() -> int:
    try:
        validate_check_command()
        with tempfile.TemporaryDirectory() as tmpdir:
            old_audit_log = os.environ.get("MEMORYCORE_MCP_AUDIT_LOG")
            os.environ["MEMORYCORE_MCP_AUDIT_LOG"] = str(Path(tmpdir) / "mcp-server-audit.jsonl")
            try:
                asyncio.run(validate_server())
            finally:
                if old_audit_log is None:
                    os.environ.pop("MEMORYCORE_MCP_AUDIT_LOG", None)
                else:
                    os.environ["MEMORYCORE_MCP_AUDIT_LOG"] = old_audit_log
    except (json.JSONDecodeError, KeyError, RuntimeError, TypeError, ValueError) as exc:
        print(str(exc))
        return 1

    print("MEMORYCORE_MCP_SERVER_ENTRYPOINT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
