#!/usr/bin/env python3
"""Validate MVP Packet B backend registry contracts and fixtures.

This is a static contract check only. It does not import or call live memory
backends, Burrow, OpenClaw, or public-safe eval runners.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
REGISTRY_FIXTURES = ROOT / "fixtures" / "backend-registry"

CAPABILITIES = {"search", "get", "verify", "health"}
HEALTH_STATES = {"healthy", "unavailable", "unknown"}
INTENTS = {
    "file_corpus_recall",
    "transcript_continuity_recall",
    "source_get",
    "source_verify",
    "backend_health",
}
INTENT_CAPABILITIES = {
    "file_corpus_recall": "search",
    "transcript_continuity_recall": "search",
    "source_get": "get",
    "source_verify": "verify",
    "backend_health": "health",
}
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


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path.relative_to(ROOT)} is not valid JSON: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_error(error: Any, label: str) -> None:
    require(isinstance(error, dict), f"{label}.error must be an object")
    require(isinstance(error.get("code"), str) and error["code"].isupper(), f"{label}.error.code is invalid")
    require(error.get("category") in ERROR_CATEGORIES, f"{label}.error.category is not recognized")
    require(isinstance(error.get("message"), str) and error["message"], f"{label}.error.message is required")


def validate_backend(data: Any, label: str) -> str:
    require(isinstance(data, dict), f"{label} must be an object")

    backend_id = data.get("backend_id")
    require(isinstance(backend_id, str) and backend_id, f"{label}.backend_id is required")
    require(isinstance(data.get("display_name"), str) and data["display_name"], f"{label}.display_name is required")
    require(data.get("health") in HEALTH_STATES, f"{label}.health is not recognized")

    capabilities = data.get("capabilities")
    require(isinstance(capabilities, list) and capabilities, f"{label}.capabilities must be a non-empty list")
    require(len(capabilities) == len(set(capabilities)), f"{label}.capabilities must be unique")
    for capability in capabilities:
        require(capability in CAPABILITIES, f"{label}.capabilities contains unsupported operation {capability!r}")

    intents = data.get("default_intents", [])
    require(isinstance(intents, list), f"{label}.default_intents must be a list")
    require(len(intents) == len(set(intents)), f"{label}.default_intents must be unique")
    for intent in intents:
        require(intent in INTENTS, f"{label}.default_intents contains unsupported intent {intent!r}")
        required_capability = INTENT_CAPABILITIES[intent]
        require(
            required_capability in capabilities,
            f"{label}.default_intents includes {intent!r} without {required_capability!r} capability",
        )

    if data.get("health") == "unavailable":
        require("error" in data, f"{label} must include error when health is unavailable")

    if "error" in data:
        validate_error(data["error"], label)

    return backend_id


def validate_backend_schema() -> None:
    data = load_json(SCHEMA_DIR / "backend.schema.json")
    require(data.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "backend.schema.json must use draft 2020-12")
    require(data.get("additionalProperties") is False, "backend.schema.json must reject unknown top-level fields")


def validate_registry(path: Path) -> None:
    data = load_json(path)
    label = str(path.relative_to(ROOT))
    require(isinstance(data, dict), f"{label} must be an object")

    backends = data.get("backends")
    require(isinstance(backends, list) and backends, f"{label}.backends must be a non-empty list")

    backend_ids: list[str] = []
    for index, backend in enumerate(backends):
        backend_ids.append(validate_backend(backend, f"{label}.backends[{index}]"))

    require(len(backend_ids) == len(set(backend_ids)), f"{label}.backends backend_id values must be unique")
    require(any("search" in backend.get("capabilities", []) for backend in backends), f"{label} must include a search-capable backend")
    require(any("health" in backend.get("capabilities", []) for backend in backends), f"{label} must include a health-capable backend")


def main() -> int:
    try:
        validate_backend_schema()
        for path in sorted(REGISTRY_FIXTURES.glob("*.json")):
            validate_registry(path)
    except ValueError as exc:
        print(f"MEMORYCORE_PACKET_B_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_PACKET_B_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
