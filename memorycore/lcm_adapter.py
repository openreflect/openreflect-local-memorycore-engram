"""Mocked Lossless-Claw adapter contract for the MemoryCore MVP.

This module normalizes static fixture-shaped LCM output. It does not import or
call lossless-claw tools, Burrow, OpenClaw, or any live transcript store.
"""

from __future__ import annotations

from typing import Any


BACKEND_ID = "lossless_claw"


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


def normalize_lcm_search(request: dict[str, Any], lcm_output: dict[str, Any]) -> dict[str, Any]:
    if "error" in lcm_output:
        return _error_result(request, "search", lcm_output["error"])

    items = []
    for rank, item in enumerate(lcm_output.get("results", []), start=1):
        pointer_id = item.get("summary_id") or item.get("message_id")
        items.append(
            {
                "backend_id": BACKEND_ID,
                "pointer": {
                    "backend_id": BACKEND_ID,
                    "pointer_id": pointer_id,
                    "summary_id": item.get("summary_id"),
                    "message_id": item.get("message_id"),
                    "conversation_id": item.get("conversation_id"),
                },
                "snippet": item.get("snippet", ""),
                "score": item.get("score"),
                "rank": rank,
                "recall_mode": lcm_output.get("mode", "lcm_fixture"),
                "verification_state": "unknown",
            }
        )

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
                "pointer": {
                    "backend_id": BACKEND_ID,
                    "pointer_id": summary_id,
                    "summary_id": summary_id,
                    "conversation_id": lcm_output.get("conversation_id"),
                },
                "content": lcm_output["answer"],
                "citations": lcm_output.get("citations", []),
                "recall_mode": "expand_query_fixture",
                "verification_state": lcm_output.get("verification_state", "unknown"),
            }
        ],
        "verification_state": lcm_output.get("verification_state", "unknown"),
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
