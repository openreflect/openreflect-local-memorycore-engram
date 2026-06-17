"""Mocked QMD adapter contract for the MemoryCore MVP.

This module normalizes static fixture-shaped QMD output. It does not import or
call QMD, Burrow, OpenClaw, or any live local index.
"""

from __future__ import annotations

from typing import Any


BACKEND_ID = "qmd"


def qmd_health(request_id: str, status: str = "unknown") -> dict[str, Any]:
    return {
        "request_id": request_id,
        "operation": "health",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": [
            {
                "backend_id": BACKEND_ID,
                "pointer": {"backend_id": BACKEND_ID, "pointer_id": "qmd:health"},
                "snippet": f"QMD fixture adapter health is {status}.",
                "verification_state": "unknown",
            }
        ],
        "verification_state": "unknown",
    }


def normalize_qmd_search(request: dict[str, Any], qmd_output: dict[str, Any]) -> dict[str, Any]:
    items = []
    for rank, item in enumerate(qmd_output.get("results", []), start=1):
        path = item["path"]
        items.append(
            {
                "backend_id": BACKEND_ID,
                "pointer": {
                    "backend_id": BACKEND_ID,
                    "pointer_id": path,
                    "source_uri": path,
                },
                "snippet": item.get("snippet", ""),
                "score": item.get("score"),
                "rank": rank,
                "recall_mode": "qmd_fixture",
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


def normalize_qmd_get(request: dict[str, Any], qmd_output: dict[str, Any]) -> dict[str, Any]:
    if "error" in qmd_output:
        return {
            "request_id": request["request_id"],
            "operation": "get",
            "status": "error",
            "selected_backend": BACKEND_ID,
            "results": [],
            "verification_state": qmd_output["error"].get("verification_state", "unknown"),
            "error": qmd_output["error"],
        }

    path = qmd_output["path"]
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
                    "pointer_id": path,
                    "source_uri": path,
                },
                "content": qmd_output["content"],
                "verification_state": "unknown",
            }
        ],
        "verification_state": "unknown",
    }
