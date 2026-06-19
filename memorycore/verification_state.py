"""Shared verification-state helpers for the MemoryCore MVP.

This module normalizes static contract results only. It does not call live
backends or inspect source content.
"""

from __future__ import annotations

from typing import Any


VERIFICATION_STATES = frozenset(
    {
        "verified",
        "stale",
        "missing",
        "unsupported",
        "unknown",
    }
)

ERROR_CATEGORY_STATES = {
    "pointer_missing": "missing",
    "verification_unsupported": "unsupported",
    "backend_timeout": "unknown",
    "backend_error": "unknown",
    "backend_unavailable": "unknown",
}


def normalize_verification_state(value: Any) -> str:
    if value in VERIFICATION_STATES:
        return value
    return "unknown"


def state_from_error(error: dict[str, Any]) -> str:
    explicit = normalize_verification_state(error.get("verification_state"))
    if explicit != "unknown":
        return explicit
    return ERROR_CATEGORY_STATES.get(error.get("category"), "unknown")


def result_verification_state(result: dict[str, Any]) -> str:
    if result.get("status") == "error":
        return state_from_error(result.get("error", {}))
    return normalize_verification_state(result.get("verification_state"))


def normalize_verify_result(
    request: dict[str, Any],
    backend_id: str,
    verify_output: dict[str, Any],
) -> dict[str, Any]:
    if "error" in verify_output:
        error = verify_output["error"]
        state = state_from_error(error)
        return {
            "request_id": request["request_id"],
            "operation": "verify",
            "status": "error",
            "selected_backend": backend_id,
            "results": [],
            "verification_state": state,
            "error": {**error, "verification_state": state},
        }

    state = normalize_verification_state(verify_output.get("verification_state"))
    if request.get("pointer", {}).get("pointer_id") is None:
        state = "missing"

    return {
        "request_id": request["request_id"],
        "operation": "verify",
        "status": "ok",
        "selected_backend": backend_id,
        "results": [
            {
                "backend_id": backend_id,
                "pointer": request.get("pointer", {}),
                "verification_state": state,
            }
        ],
        "verification_state": state,
    }
