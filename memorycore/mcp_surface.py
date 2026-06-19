"""Fixture-only MCP tool surface contract for the MemoryCore MVP.

This module models the request/response behavior expected from MCP tools
without starting an MCP server or calling OpenClaw, Burrow, QMD, or
Lossless-Claw. It is a static contract layer for EVAL-011.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from memorycore.audit_log import append_record, build_audit_record
from memorycore.cli import DEFAULT_AUDIT_LOG, _execute_request


TOOL_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "name": "memorycore_search",
        "description": "Search MemoryCore backends using public-safe fixture data.",
        "input_schema": {
            "type": "object",
            "required": ["query"],
            "additionalProperties": False,
            "properties": {
                "query": {"type": "string", "minLength": 1},
                "backend": {"type": "string", "enum": ["qmd", "lossless_claw", "mock_healthy"]},
                "intent": {
                    "type": "string",
                    "enum": ["file_corpus_recall", "transcript_continuity_recall"],
                    "default": "file_corpus_recall",
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 5},
            },
        },
    },
    {
        "name": "memorycore_get",
        "description": "Resolve a MemoryCore pointer using public-safe fixture data.",
        "input_schema": {
            "type": "object",
            "required": ["pointer_id"],
            "additionalProperties": False,
            "properties": {
                "pointer_id": {"type": "string", "minLength": 1},
                "backend": {"type": "string", "enum": ["qmd", "lossless_claw", "mock_healthy"], "default": "qmd"},
            },
        },
    },
    {
        "name": "memorycore_verify",
        "description": "Verify a MemoryCore pointer using public-safe fixture data.",
        "input_schema": {
            "type": "object",
            "required": ["pointer_id"],
            "additionalProperties": False,
            "properties": {
                "pointer_id": {"type": "string", "minLength": 1},
                "backend": {"type": "string", "enum": ["qmd", "lossless_claw", "mock_healthy"], "default": "mock_healthy"},
                "state": {
                    "type": "string",
                    "enum": ["verified", "stale", "missing", "unsupported", "unknown"],
                    "default": "verified",
                },
            },
        },
    },
    {
        "name": "memorycore_health",
        "description": "Return MemoryCore backend health using public-safe fixture data.",
        "input_schema": {"type": "object", "additionalProperties": False, "properties": {}},
    },
)


def list_tools() -> list[dict[str, Any]]:
    return [dict(tool) for tool in TOOL_DEFINITIONS]


def call_tool(tool_name: str, arguments: dict[str, Any] | None = None, *, audit_log: Path | None = None) -> dict[str, Any]:
    arguments = arguments or {}
    _validate_tool_arguments(tool_name, arguments)
    request = _request_from_tool(tool_name, arguments)
    result = _execute_request(request)

    if request["operation"] in {"search", "get", "verify"}:
        record = build_audit_record(request, result, timestamp=_timestamp())
        append_record(audit_log or DEFAULT_AUDIT_LOG, record)
        result = {**result, "audit_id": record["audit_id"]}

    return result


def _validate_tool_arguments(tool_name: str, arguments: dict[str, Any]) -> None:
    schema = _tool_schema(tool_name)
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    allowed = set(properties)

    if schema.get("additionalProperties") is False:
        extra = sorted(set(arguments) - allowed)
        if extra:
            raise ValueError(f"unexpected MCP argument(s) for {tool_name}: {', '.join(extra)}")

    for key in required:
        if key not in arguments:
            raise ValueError(f"missing required MCP argument: {key}")

    for key, value in arguments.items():
        constraints = properties.get(key)
        if constraints is None:
            continue
        expected_type = constraints.get("type")
        if expected_type == "string":
            if not isinstance(value, str):
                raise ValueError(f"MCP argument {key} must be a string")
            if constraints.get("minLength") and len(value) < constraints["minLength"]:
                raise ValueError(f"MCP argument {key} must not be empty")
        elif expected_type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"MCP argument {key} must be an integer")
            minimum = constraints.get("minimum")
            maximum = constraints.get("maximum")
            if minimum is not None and value < minimum:
                raise ValueError(f"MCP argument {key} must be >= {minimum}")
            if maximum is not None and value > maximum:
                raise ValueError(f"MCP argument {key} must be <= {maximum}")

        if "enum" in constraints and value not in constraints["enum"]:
            raise ValueError(f"MCP argument {key} has unsupported value: {value}")


def _tool_schema(tool_name: str) -> dict[str, Any]:
    for tool in TOOL_DEFINITIONS:
        if tool["name"] == tool_name:
            return tool["input_schema"]
    raise ValueError(f"unknown MemoryCore MCP tool: {tool_name}")


def _request_from_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    base = {
        "request_id": f"req_mcp_{tool_name.removeprefix('memorycore_')}",
        "client_surface": "mcp",
    }

    if tool_name == "memorycore_health":
        return {**base, "operation": "health", "intent": "backend_health"}

    if tool_name == "memorycore_search":
        query = _required_string(arguments, "query")
        request = {
            **base,
            "operation": "search",
            "intent": arguments.get("intent", "file_corpus_recall"),
            "query": query,
            "limit": int(arguments.get("limit", 5)),
        }
        if arguments.get("backend"):
            request["backend_hint"] = arguments["backend"]
        return request

    if tool_name == "memorycore_get":
        backend = arguments.get("backend", "qmd")
        pointer_id = _required_string(arguments, "pointer_id")
        return {
            **base,
            "operation": "get",
            "intent": "source_get",
            "pointer": {"backend_id": backend, "pointer_id": pointer_id, "source_uri": pointer_id},
        }

    if tool_name == "memorycore_verify":
        backend = arguments.get("backend", "mock_healthy")
        pointer_id = _required_string(arguments, "pointer_id")
        return {
            **base,
            "operation": "verify",
            "intent": "source_verify",
            "pointer": {"backend_id": backend, "pointer_id": pointer_id, "source_uri": pointer_id},
            "verification_state": arguments.get("state", "verified"),
        }

    raise ValueError(f"unknown MemoryCore MCP tool: {tool_name}")


def _required_string(arguments: dict[str, Any], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing required MCP argument: {key}")
    return value


def _timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
