"""Public-safe request/result audit records for the MemoryCore MVP.

Audit records explain routing and outcome decisions after the fact. They store
request/result metadata and pointer ids only, never answer text or source text.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PRIVATE_RESULT_FIELDS = {"snippet", "content", "citations", "summary", "answer", "text"}


def build_audit_record(request: dict[str, Any], result: dict[str, Any], *, timestamp: str) -> dict[str, Any]:
    results = result.get("results", [])
    error = result.get("error")
    record: dict[str, Any] = {
        "request_id": request["request_id"],
        "client_surface": request["client_surface"],
        "operation": request["operation"],
        "normalized_intent": request.get("intent"),
        "selected_backend": result.get("selected_backend") or _requested_backend(request),
        "result_count": len(results),
        "pointer_ids": _pointer_ids(results),
        "verification_state": _verification_state(result, results, error),
        "error_state": _error_state(error),
        "timestamp": timestamp,
        "status": result.get("status", "error"),
    }
    record["audit_id"] = _audit_id(record)
    return record


def append_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.open("a", encoding="utf-8").write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def read_recent(path: Path, limit: int = 10) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-limit:]]


def assert_public_safe(record: dict[str, Any]) -> None:
    serialized = json.dumps(record, sort_keys=True)
    leaked = [field for field in PRIVATE_RESULT_FIELDS if f'"{field}"' in serialized]
    if leaked:
        raise ValueError(f"audit record contains private result fields: {', '.join(sorted(leaked))}")


def _requested_backend(request: dict[str, Any]) -> str | None:
    return request.get("backend_hint") or request.get("pointer", {}).get("backend_id")


def _pointer_ids(results: list[dict[str, Any]]) -> list[str]:
    pointer_ids = []
    for item in results:
        pointer = item.get("pointer", {})
        pointer_id = pointer.get("pointer_id")
        if pointer_id:
            pointer_ids.append(pointer_id)
    return pointer_ids


def _verification_state(result: dict[str, Any], results: list[dict[str, Any]], error: dict[str, Any] | None) -> str:
    if result.get("verification_state"):
        return result["verification_state"]
    states = {item.get("verification_state") for item in results if item.get("verification_state")}
    if len(states) == 1:
        return states.pop()
    if error and error.get("verification_state"):
        return error["verification_state"]
    return "unknown"


def _error_state(error: dict[str, Any] | None) -> dict[str, str | None] | None:
    if not error:
        return None
    return {
        "code": error.get("code"),
        "category": error.get("category"),
    }


def _audit_id(record: dict[str, Any]) -> str:
    stable = {
        "request_id": record["request_id"],
        "client_surface": record["client_surface"],
        "operation": record["operation"],
        "selected_backend": record.get("selected_backend"),
        "timestamp": record["timestamp"],
        "status": record["status"],
        "error_state": record.get("error_state"),
    }
    digest = hashlib.sha256(json.dumps(stable, sort_keys=True).encode("utf-8")).hexdigest()
    return f"audit_{digest[:16]}"
