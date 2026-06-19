#!/usr/bin/env python3
"""Validate MVP Packet A schemas and public-safe fixtures.

This is intentionally stdlib-only. It checks the contract invariants the MVP
depends on before router/backend code exists, without exercising any live
memory backend.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
REQUEST_FIXTURES = ROOT / "fixtures" / "requests"
BACKEND_FIXTURES = ROOT / "fixtures" / "mock-backends"

CLIENT_SURFACES = {"cli", "mcp", "openclaw", "test"}
OPERATIONS = {"search", "get", "verify", "health"}
INTENTS = {
    "file_corpus_recall",
    "transcript_continuity_recall",
    "source_get",
    "source_verify",
    "backend_health",
}
CAPABILITIES = OPERATIONS
HEALTH_STATES = {"healthy", "unavailable"}
VERIFICATION_STATES = {"verified", "stale", "missing", "unsupported", "unknown"}
ERROR_CATEGORIES = {
    "validation",
    "unsupported_operation",
    "missing_backend",
    "backend_unavailable",
    "backend_timeout",
    "backend_error",
    "pointer_missing",
    "verification_unsupported",
    "unknown_failure",
}

EXPECTED_INVALID_REQUESTS = {
    "invalid-op.json": "operation is not recognized",
    "missing-query.json": "search request requires query",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path.relative_to(ROOT)} is not valid JSON: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_pointer(pointer: Any, label: str) -> None:
    require(isinstance(pointer, dict), f"{label}.pointer must be an object")
    require(isinstance(pointer.get("backend_id"), str), f"{label}.pointer.backend_id is required")
    require(isinstance(pointer.get("pointer_id"), str), f"{label}.pointer.pointer_id is required")
    if "source_uri" in pointer:
        require(isinstance(pointer["source_uri"], str), f"{label}.pointer.source_uri must be a string")


def validate_request(data: Any, label: str) -> list[str]:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    check(isinstance(data, dict), "request must be an object")
    if not isinstance(data, dict):
        return errors

    request_id = data.get("request_id")
    check(isinstance(request_id, str) and request_id.startswith("req_"), "request_id must start with req_")
    check(data.get("client_surface") in CLIENT_SURFACES, "client_surface is not recognized")

    operation = data.get("operation")
    check(operation in OPERATIONS, "operation is not recognized")

    if "intent" in data:
        check(data["intent"] in INTENTS, "intent is not recognized")
    if "query" in data:
        check(isinstance(data["query"], str) and bool(data["query"].strip()), "query must be a non-empty string")
    if "limit" in data:
        check(isinstance(data["limit"], int) and 1 <= data["limit"] <= 50, "limit must be 1..50")
    if "verify" in data:
        check(isinstance(data["verify"], bool), "verify must be a boolean")

    if operation == "search":
        check(isinstance(data.get("query"), str) and bool(data.get("query", "").strip()), "search request requires query")
    if operation in {"get", "verify"}:
        try:
            validate_pointer(data.get("pointer"), label)
        except ValueError as exc:
            errors.append(str(exc))

    return errors


def validate_backend(data: Any, label: str) -> None:
    require(isinstance(data, dict), f"{label} must be an object")
    require(isinstance(data.get("backend_id"), str), f"{label}.backend_id is required")
    require(data.get("health") in HEALTH_STATES, f"{label}.health is not recognized")

    capabilities = data.get("capabilities")
    require(isinstance(capabilities, list) and capabilities, f"{label}.capabilities must be a non-empty list")
    for capability in capabilities:
        require(capability in CAPABILITIES, f"{label}.capabilities contains unsupported operation {capability!r}")

    if "verify_result" in data:
        verify_result = data["verify_result"]
        require(isinstance(verify_result, dict), f"{label}.verify_result must be an object")
        require(
            verify_result.get("verification_state") in VERIFICATION_STATES,
            f"{label}.verify_result.verification_state is not recognized",
        )

    if "error" in data:
        error = data["error"]
        require(isinstance(error, dict), f"{label}.error must be an object")
        require(isinstance(error.get("code"), str) and error["code"].isupper(), f"{label}.error.code is invalid")
        require(error.get("category") in ERROR_CATEGORIES, f"{label}.error.category is not recognized")
        require(isinstance(error.get("message"), str) and error["message"], f"{label}.error.message is required")


def validate_schema_files() -> None:
    for name in ("request.schema.json", "result.schema.json", "error.schema.json"):
        data = load_json(SCHEMA_DIR / name)
        require(data.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{name} must use draft 2020-12")
        require(data.get("additionalProperties") is False, f"{name} must reject unknown top-level fields")


def main() -> int:
    try:
        validate_schema_files()

        for path in sorted(REQUEST_FIXTURES.glob("*.json")):
            errors = validate_request(load_json(path), path.name)
            expected = EXPECTED_INVALID_REQUESTS.get(path.name)
            if expected is None:
                require(not errors, f"{path.relative_to(ROOT)} should be valid: {errors}")
            else:
                require(expected in errors, f"{path.relative_to(ROOT)} should fail with {expected!r}; got {errors}")

        for path in sorted(BACKEND_FIXTURES.glob("*.json")):
            validate_backend(load_json(path), path.name)

    except ValueError as exc:
        print(f"MEMORYCORE_PACKET_A_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_PACKET_A_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
