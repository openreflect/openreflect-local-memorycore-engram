"""Lossless-Claw adapter contract for the MemoryCore MVP.

This module normalizes static fixture-shaped LCM output and host-injected
Lossless-Claw-shaped calls. It does not import lossless-claw tools, Burrow,
OpenClaw, or any live transcript store.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Protocol


BACKEND_ID = "lossless_claw"


class LcmHostBridge(Protocol):
    """Minimal host-injected Lossless-Claw tool boundary."""

    def lcm_grep(self, *, query: str, scope: str | None = None, limit: int | None = None) -> dict[str, Any]:
        """Return grep/search-shaped recall results."""

    def lcm_describe(
        self,
        *,
        summary_id: str | None = None,
        message_id: str | None = None,
    ) -> dict[str, Any]:
        """Resolve a summary or message pointer without expanding private text."""

    def lcm_expand_query(
        self,
        *,
        query: str | None = None,
        prompt: str | None = None,
        summary_ids: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Return answer/citation-shaped recall output."""


def lcm_health(request_id: str, status: str = "unknown") -> dict[str, Any]:
    return {
        "request_id": request_id,
        "operation": "health",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": [
            {
                "backend_id": BACKEND_ID,
                "pointer": {"backend_id": BACKEND_ID, "pointer_id": "lcm:health"},
                "snippet": f"Lossless-Claw fixture adapter health is {status}.",
                "verification_state": "unknown",
            }
        ],
        "verification_state": "unknown",
    }


def host_lcm_search(request: dict[str, Any], bridge: LcmHostBridge | None) -> dict[str, Any]:
    tool = _host_tool(request, bridge, "lcm_grep", "search")
    if not callable(tool):
        return tool

    try:
        output = tool(query=request["query"], scope=request.get("scope"), limit=request.get("limit"))
    except TimeoutError:
        return _error_result(request, "search", _host_error("backend_timeout", "LCM host grep timed out.", "lcm_grep"))
    except (KeyError, TypeError, ValueError) as exc:
        return _error_result(request, "search", _host_error("backend_error", str(exc), "lcm_grep"))

    return normalize_lcm_search(request, output)


def host_lcm_get(request: dict[str, Any], bridge: LcmHostBridge | None) -> dict[str, Any]:
    tool = _host_tool(request, bridge, "lcm_expand_query", "get")
    if not callable(tool):
        return tool

    pointer = request.get("pointer", {})
    summary_id = pointer.get("summary_id") or pointer.get("pointer_id")
    try:
        output = tool(
            query=request.get("query"),
            prompt=request.get("prompt"),
            summary_ids=[summary_id] if summary_id else None,
        )
    except TimeoutError:
        return _error_result(request, "get", _host_error("backend_timeout", "LCM host expand-query timed out.", "lcm_expand_query"))
    except (KeyError, TypeError, ValueError) as exc:
        return _error_result(request, "get", _host_error("backend_error", str(exc), "lcm_expand_query"))

    return normalize_lcm_get(request, output)


def host_lcm_verify(request: dict[str, Any], bridge: LcmHostBridge | None) -> dict[str, Any]:
    tool = _host_tool(request, bridge, "lcm_describe", "verify")
    if not callable(tool):
        return tool

    pointer = request.get("pointer", {})
    try:
        output = tool(
            summary_id=pointer.get("summary_id") or pointer.get("pointer_id"),
            message_id=pointer.get("message_id"),
        )
    except TimeoutError:
        return _error_result(request, "verify", _host_error("backend_timeout", "LCM host describe timed out.", "lcm_describe"))
    except (KeyError, TypeError, ValueError) as exc:
        return _error_result(request, "verify", _host_error("backend_error", str(exc), "lcm_describe"))

    return normalize_lcm_describe(request, output)


def normalize_lcm_search(request: dict[str, Any], lcm_output: dict[str, Any]) -> dict[str, Any]:
    if "error" in lcm_output:
        return _error_result(request, "search", lcm_output["error"])

    items = []
    for rank, item in enumerate(lcm_output.get("results", []), start=1):
        pointer_id = item.get("summary_id") or item.get("message_id")
        result = {
            "backend_id": BACKEND_ID,
            "pointer": _without_none(
                {
                    "backend_id": BACKEND_ID,
                    "pointer_id": pointer_id,
                    "summary_id": item.get("summary_id"),
                    "message_id": item.get("message_id"),
                    "conversation_id": item.get("conversation_id"),
                }
            ),
            "snippet": item.get("snippet", ""),
            "rank": rank,
            "recall_mode": lcm_output.get("mode", "lcm_fixture"),
            "verification_state": "unknown",
        }
        if item.get("score") is not None:
            result["score"] = item["score"]
        items.append(result)

    return {
        "request_id": request["request_id"],
        "operation": "search",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": items,
        "verification_state": "unknown",
    }


def normalize_lcm_get(request: dict[str, Any], lcm_output: dict[str, Any]) -> dict[str, Any]:
    if "error" in lcm_output:
        return _error_result(request, "get", lcm_output["error"])

    summary_id = lcm_output["summary_id"]
    return {
        "request_id": request["request_id"],
        "operation": "get",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": [
            {
                "backend_id": BACKEND_ID,
                "pointer": _without_none(
                    {
                        "backend_id": BACKEND_ID,
                        "pointer_id": summary_id,
                        "summary_id": summary_id,
                        "conversation_id": lcm_output.get("conversation_id"),
                    }
                ),
                "content": lcm_output["answer"],
                "citations": lcm_output.get("citations", []),
                "recall_mode": "expand_query_fixture",
                "verification_state": lcm_output.get("verification_state", "unknown"),
            }
        ],
        "verification_state": lcm_output.get("verification_state", "unknown"),
    }


def normalize_lcm_describe(request: dict[str, Any], lcm_output: dict[str, Any]) -> dict[str, Any]:
    if "error" in lcm_output:
        return _error_result(request, "verify", lcm_output["error"])

    summary_id = lcm_output.get("summary_id")
    message_id = lcm_output.get("message_id")
    pointer_id = summary_id or message_id or request.get("pointer", {}).get("pointer_id")
    exists = lcm_output.get("exists")
    if exists is False:
        return _error_result(
            request,
            "verify",
            {
                "code": "POINTER_MISSING",
                "category": "pointer_missing",
                "message": "Lossless-Claw pointer was not found.",
                "verification_state": "missing",
            },
        )

    verification_state = lcm_output.get("verification_state")
    if verification_state is None:
        verification_state = "verified" if exists is True else "unsupported"

    return {
        "request_id": request["request_id"],
        "operation": "verify",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": [
            {
                "backend_id": BACKEND_ID,
                "pointer": _without_none(
                    {
                        "backend_id": BACKEND_ID,
                        "pointer_id": pointer_id,
                        "summary_id": summary_id,
                        "message_id": message_id,
                        "conversation_id": lcm_output.get("conversation_id"),
                    }
                ),
                "verification_state": verification_state,
            }
        ],
        "verification_state": verification_state,
    }


def _error_result(request: dict[str, Any], operation: str, error: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_id": request["request_id"],
        "operation": operation,
        "status": "error",
        "selected_backend": BACKEND_ID,
        "results": [],
        "verification_state": error.get("verification_state", "unknown"),
        "error": error,
    }


def _host_tool(
    request: dict[str, Any],
    bridge: LcmHostBridge | None,
    tool_name: str,
    operation: str,
) -> Callable[..., dict[str, Any]] | dict[str, Any]:
    if bridge is None:
        return _error_result(request, operation, _host_error("backend_unavailable", "LCM host bridge is not configured.", tool_name))

    tool = getattr(bridge, tool_name, None)
    if not callable(tool):
        return _error_result(request, operation, _host_error("backend_unavailable", f"LCM host tool {tool_name} is unavailable.", tool_name))

    return tool


def _host_error(category: str, message: str, tool: str) -> dict[str, Any]:
    code_by_category = {
        "backend_unavailable": "BACKEND_UNAVAILABLE",
        "backend_timeout": "BACKEND_TIMEOUT",
        "backend_error": "BACKEND_ERROR",
    }
    return {
        "code": code_by_category.get(category, "BACKEND_ERROR"),
        "category": category,
        "message": message,
        "verification_state": "unknown",
        "details": {"tool": tool},
    }


def _without_none(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None}
