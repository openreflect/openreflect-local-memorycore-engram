"""Fixture-only MCP tool surface contract for the MemoryCore MVP.

This module models the request/response behavior expected from MCP tools
without starting an MCP server or calling OpenClaw, Burrow, QMD, or
Lossless-Claw. It is a static contract layer for EVAL-011.
"""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from memorycore.audit_log import append_record, build_audit_record
from memorycore.cache_router import (
    DEFAULT_ROUTING,
    CacheStore,
    cache_read,
    cache_search,
    cache_write,
    flush_pending,
)
from memorycore.cli import DEFAULT_AUDIT_LOG, ROOT, _execute_request, resolve_backend_mode
from memorycore.qmd_adapter import DEFAULT_QMD_BIN, live_local_qmd_verify, live_local_qmd_write

DEFAULT_WRITE_COLLECTION = "memorycore-writes"
DEFAULT_CORPUS_DIR = "~/.memorycore/corpus"


DEFAULT_CACHE_DB = ROOT / ".memorycore" / "cache.sqlite3"

# Fixture-only flush acknowledgments. Real backend flush handlers arrive with
# the gated write adapters; until then flushes are marked fixture-only.
FIXTURE_FLUSH_BACKENDS = {
    "qmd": lambda record: {"status": "ok"},
    "lossless_claw": lambda record: {"status": "ok"},
    "mock_healthy": lambda record: {"status": "ok"},
}

CACHE_TOOL_NAMES = frozenset(
    {
        "memorycore_remember",
        "memorycore_recall",
        "memorycore_cache_search",
        "memorycore_flush",
    }
)


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
        "description": "Verify a pointer (fixture contract) or a cached record against real source state (record_id, live-local mode). Real verdicts update the cached stamp.",
        "input_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "pointer_id": {"type": "string", "minLength": 1},
                "record_id": {"type": "string", "minLength": 1},
                "backend": {"type": "string", "enum": ["qmd", "lossless_claw", "mock_healthy"], "default": "mock_healthy"},
                "state": {
                    "type": "string",
                    "enum": ["verified", "stale", "missing", "unsupported", "unknown"],
                    "default": "verified",
                },
                "client": {"type": "string", "enum": ["mcp", "openclaw"], "default": "mcp"},
            },
        },
    },
    {
        "name": "memorycore_health",
        "description": "Return MemoryCore backend health using public-safe fixture data.",
        "input_schema": {"type": "object", "additionalProperties": False, "properties": {}},
    },
    {
        "name": "memorycore_remember",
        "description": "Write a memory record into the local cache, routed by memory type. Provide content_ref to remember a pointer, or content for a transient write-through into the backend (ADR-0005).",
        "input_schema": {
            "type": "object",
            "required": ["memory_type"],
            "additionalProperties": False,
            "properties": {
                "memory_type": {"type": "string", "enum": ["file_corpus", "transcript"]},
                "content_ref": {"type": "string", "minLength": 1},
                "content": {"type": "string", "minLength": 1},
                "pointer_id": {"type": "string", "minLength": 1},
                "summary_id": {"type": "string", "minLength": 1},
                "verification": {
                    "type": "string",
                    "enum": ["verified", "stale", "missing", "unsupported", "unknown"],
                    "default": "unknown",
                },
                "client": {"type": "string", "enum": ["mcp", "openclaw"], "default": "mcp"},
            },
        },
    },
    {
        "name": "memorycore_recall",
        "description": "Read a memory record from the local cache by record id or pointer id.",
        "input_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "record_id": {"type": "string", "minLength": 1},
                "pointer_id": {"type": "string", "minLength": 1},
                "client": {"type": "string", "enum": ["mcp", "openclaw"], "default": "mcp"},
            },
        },
    },
    {
        "name": "memorycore_cache_search",
        "description": "Search cached memory records only; does not query live backends.",
        "input_schema": {
            "type": "object",
            "required": ["query"],
            "additionalProperties": False,
            "properties": {
                "query": {"type": "string", "minLength": 1},
                "memory_type": {"type": "string", "enum": ["file_corpus", "transcript"]},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 5},
                "client": {"type": "string", "enum": ["mcp", "openclaw"], "default": "mcp"},
            },
        },
    },
    {
        "name": "memorycore_flush",
        "description": "Flush pending cached records to their routed backends (fixture-only handlers).",
        "input_schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "client": {"type": "string", "enum": ["mcp", "openclaw"], "default": "mcp"},
            },
        },
    },
)


def list_tools() -> list[dict[str, Any]]:
    return [dict(tool) for tool in TOOL_DEFINITIONS]


def call_tool(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    *,
    audit_log: Path | None = None,
    cache_db: Path | None = None,
) -> dict[str, Any]:
    arguments = arguments or {}
    _validate_tool_arguments(tool_name, arguments)

    if tool_name == "memorycore_verify":
        if not (arguments.get("pointer_id") or arguments.get("record_id")):
            raise ValueError("memorycore_verify requires pointer_id or record_id")
        if arguments.get("record_id"):
            result = _verify_cached_record(arguments, cache_db or DEFAULT_CACHE_DB)
            request = {
                "request_id": f"req_{arguments.get('client', 'mcp')}_verify",
                "client_surface": arguments.get("client", "mcp"),
                "operation": "verify",
            }
            record = build_audit_record(request, result, timestamp=_timestamp())
            append_record(audit_log or DEFAULT_AUDIT_LOG, record)
            return {**result, "audit_id": record["audit_id"]}

    if tool_name in CACHE_TOOL_NAMES:
        request = _cache_request_from_tool(tool_name, arguments)
        result = _execute_cache_request(request, arguments, cache_db or DEFAULT_CACHE_DB)
        record = build_audit_record(request, result, timestamp=_timestamp())
        append_record(audit_log or DEFAULT_AUDIT_LOG, record)
        return {**result, "audit_id": record["audit_id"]}

    request = _request_from_tool(tool_name, arguments)
    result = _execute_request(request)

    if request["operation"] in {"search", "get", "verify"}:
        record = build_audit_record(request, result, timestamp=_timestamp())
        append_record(audit_log or DEFAULT_AUDIT_LOG, record)
        result = {**result, "audit_id": record["audit_id"]}

    return result


def _cache_request_from_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    client = arguments.get("client", "mcp")
    suffix = tool_name.removeprefix("memorycore_")
    operations = {
        "remember": "cache_write",
        "recall": "cache_read",
        "cache_search": "cache_search",
        "flush": "cache_flush",
    }
    if tool_name == "memorycore_recall" and not (arguments.get("record_id") or arguments.get("pointer_id")):
        raise ValueError("memorycore_recall requires record_id or pointer_id")
    if tool_name == "memorycore_remember" and not (arguments.get("content_ref") or arguments.get("content")):
        raise ValueError("memorycore_remember requires content_ref or content")
    return {
        "request_id": f"req_{client}_{suffix}",
        "client_surface": client,
        "operation": operations[suffix],
    }


def _execute_cache_request(
    request: dict[str, Any],
    arguments: dict[str, Any],
    cache_db: Path,
) -> dict[str, Any]:
    cache_db.parent.mkdir(parents=True, exist_ok=True)
    store = CacheStore(cache_db)
    try:
        operation = request["operation"]
        if operation == "cache_write":
            return _cache_write_result(request, arguments, store)
        if operation == "cache_read":
            return _cache_read_result(request, arguments, store)
        if operation == "cache_search":
            records = cache_search(store, arguments["query"], memory_type=arguments.get("memory_type"))
            records = records[: int(arguments.get("limit", 5))]
            return _ok_cache_result(request, [_cache_item(record) for record in records])
        if operation == "cache_flush":
            flushed = flush_pending(store, FIXTURE_FLUSH_BACKENDS, timestamp=_timestamp())
            result = _ok_cache_result(request, [_cache_item(record) for record in flushed])
            return {**result, "flush_mode": "fixture-only"}
        raise ValueError(f"unknown cache operation: {operation}")
    finally:
        store.close()


def _cache_write_result(request: dict[str, Any], arguments: dict[str, Any], store: CacheStore) -> dict[str, Any]:
    if arguments.get("content") is not None:
        return _content_write_through(request, arguments, store)

    memory_type = arguments["memory_type"]
    content_ref = arguments["content_ref"]
    backend_id = DEFAULT_ROUTING[memory_type][0]
    pointer: dict[str, Any] = {"backend_id": backend_id}
    if memory_type == "transcript":
        pointer["summary_id"] = arguments.get("summary_id") or content_ref
    pointer["pointer_id"] = arguments.get("pointer_id") or content_ref

    record = cache_write(
        store,
        {
            "memory_type": memory_type,
            "content_ref": content_ref,
            "source_pointer": pointer,
            "verification": arguments.get("verification", "unknown"),
        },
        timestamp=_timestamp(),
    )
    result = _ok_cache_result(request, [_cache_item(record)])
    return {**result, "selected_backend": backend_id}


def _verify_cached_record(arguments: dict[str, Any], cache_db: Path) -> dict[str, Any]:
    """EN-018: prove a cached record against real source state, update its stamp."""
    client = arguments.get("client", "mcp")
    request = {
        "request_id": f"req_{client}_verify",
        "client_surface": client,
        "operation": "verify",
    }
    cache_db.parent.mkdir(parents=True, exist_ok=True)
    store = CacheStore(cache_db)
    try:
        record = store.get(arguments["record_id"])
        if record is None:
            return {
                **request,
                "status": "error",
                "results": [],
                "verification_state": "missing",
                "error": {
                    "code": "CACHE_MISS",
                    "category": "pointer_missing",
                    "message": "No cached record matches the requested id.",
                    "verification_state": "missing",
                },
            }

        backend_id = record["source_pointer"].get("backend_id")
        if resolve_backend_mode() != "live-local" or backend_id != "qmd":
            return {
                **request,
                "status": "error",
                "results": [],
                "verification_state": "unsupported",
                "error": {
                    "code": "VERIFICATION_UNSUPPORTED",
                    "category": "verification_unsupported",
                    "message": "Real verification requires live-local mode and a qmd-backed record.",
                    "verification_state": "unsupported",
                },
            }

        verify_request = {
            **request,
            "pointer": record["source_pointer"],
            "content_hash": record.get("content_hash") or None,
        }
        result = live_local_qmd_verify(
            verify_request,
            qmd_bin=os.environ.get("MEMORYCORE_QMD_BIN", DEFAULT_QMD_BIN),
            timeout_seconds=float(os.environ.get("MEMORYCORE_QMD_TIMEOUT_SECONDS", "10")),
        )

        state = result.get("verification_state", "unknown")
        record["verification"] = state
        record["updated_at"] = _timestamp()
        store.upsert(record)

        if result.get("results"):
            result["results"][0]["record_id"] = record["record_id"]
        return {**result, "request_id": request["request_id"]}
    finally:
        store.close()


def _content_write_through(request: dict[str, Any], arguments: dict[str, Any], store: CacheStore) -> dict[str, Any]:
    """ADR-0005: content rides the call, lands in the backend, cache keeps the pointer."""
    memory_type = arguments["memory_type"]
    if memory_type != "file_corpus":
        return {
            "request_id": request["request_id"],
            "operation": request["operation"],
            "status": "error",
            "results": [],
            "verification_state": "unknown",
            "error": {
                "code": "BACKEND_UNAVAILABLE",
                "category": "backend_unavailable",
                "message": "Content write-through supports file_corpus only until the LCM bridge transport exists.",
            },
        }

    content = arguments["content"]
    timestamp = _timestamp()
    memory_id = "memory-" + hashlib.sha256(f"{content}{timestamp}".encode()).hexdigest()[:16]
    collection = os.environ.get("MEMORYCORE_QMD_WRITE_COLLECTION", DEFAULT_WRITE_COLLECTION)

    if resolve_backend_mode() == "live-local":
        write_result = live_local_qmd_write(
            request,
            content=content,
            corpus_dir=os.environ.get("MEMORYCORE_CORPUS_DIR", DEFAULT_CORPUS_DIR),
            collection=collection,
            memory_id=memory_id,
            frontmatter={
                "memorycore": "true",
                "memory_id": memory_id,
                "memory_type": memory_type,
                "client_surface": arguments.get("client", "mcp"),
                "created_at": timestamp,
            },
            qmd_bin=os.environ.get("MEMORYCORE_QMD_BIN", DEFAULT_QMD_BIN),
            timeout_seconds=float(os.environ.get("MEMORYCORE_QMD_TIMEOUT_SECONDS", "10")),
        )
        if write_result["status"] == "error":
            return write_result
        pointer = write_result["results"][0]["pointer"]
        verification = write_result["verification_state"]
        content_hash = write_result.get("content_hash", "")
        write_mode = "live-local"
    else:
        pointer = {"backend_id": "qmd", "pointer_id": f"qmd://{collection}/{memory_id}.md"}
        verification = "unknown"
        content_hash = ""
        write_mode = "fixture-only"

    record = cache_write(
        store,
        {
            "memory_type": memory_type,
            "content_ref": pointer["pointer_id"],
            "source_pointer": pointer,
            "verification": verification,
            "content_hash": content_hash,
        },
        timestamp=timestamp,
    )
    record["flush_state"] = "flushed"
    record["updated_at"] = timestamp
    store.upsert(record)

    result = _ok_cache_result(request, [_cache_item(record)])
    return {**result, "selected_backend": "qmd", "write_mode": write_mode}


def _cache_read_result(request: dict[str, Any], arguments: dict[str, Any], store: CacheStore) -> dict[str, Any]:
    record = cache_read(
        store,
        record_id=arguments.get("record_id"),
        pointer_id=None if arguments.get("record_id") else arguments.get("pointer_id"),
    )
    if record is None:
        return {
            "request_id": request["request_id"],
            "operation": request["operation"],
            "status": "error",
            "results": [],
            "verification_state": "missing",
            "error": {
                "code": "CACHE_MISS",
                "category": "pointer_missing",
                "message": "No cached record matches the requested id.",
                "verification_state": "missing",
            },
        }
    return _ok_cache_result(request, [_cache_item(record)])


def _ok_cache_result(request: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    states = {item["verification_state"] for item in items}
    return {
        "request_id": request["request_id"],
        "operation": request["operation"],
        "status": "ok",
        "results": items,
        "verification_state": states.pop() if len(states) == 1 else "unknown",
    }


def _cache_item(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "backend_id": record["source_pointer"].get("backend_id"),
        "pointer": record["source_pointer"],
        "verification_state": record["verification"],
        "record_id": record["record_id"],
        "memory_type": record["memory_type"],
        "content_ref": record["content_ref"],
        "flush_state": record["flush_state"],
    }


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
