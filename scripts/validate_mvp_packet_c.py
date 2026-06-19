#!/usr/bin/env python3
"""Validate MVP Packet C structured error fixtures.

This is a static contract check only. It does not import or call live memory
backends, Burrow, OpenClaw, or public-safe eval runners.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "error.schema.json"
ERROR_FIXTURES = ROOT / "fixtures" / "errors"

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
VERIFICATION_STATES = {"missing", "unsupported", "unknown"}
CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]+$")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path.relative_to(ROOT)} is not valid JSON: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_schema() -> None:
    data = load_json(SCHEMA_PATH)
    require(data.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "error.schema.json must use draft 2020-12")
    require(data.get("additionalProperties") is False, "error.schema.json must reject unknown top-level fields")

    category = data.get("properties", {}).get("category", {})
    require(set(category.get("enum", [])) == ERROR_CATEGORIES, "error.schema.json category enum must match Packet C")


def validate_error(data: Any, label: str) -> str:
    require(isinstance(data, dict), f"{label} must be an object")
    require(set(data).issubset({"code", "category", "message", "verification_state", "details"}), f"{label} has unknown top-level fields")

    code = data.get("code")
    require(isinstance(code, str) and CODE_PATTERN.match(code) is not None, f"{label}.code is invalid")

    category = data.get("category")
    require(category in ERROR_CATEGORIES, f"{label}.category is not recognized")
    require(isinstance(data.get("message"), str) and data["message"].strip(), f"{label}.message is required")

    if "verification_state" in data:
        require(data["verification_state"] in VERIFICATION_STATES, f"{label}.verification_state is not recognized")
    if "details" in data:
        require(isinstance(data["details"], dict), f"{label}.details must be an object")

    if category == "pointer_missing":
        require(data.get("verification_state") == "missing", f"{label} must mark missing pointer verification_state")
    if category == "verification_unsupported":
        require(data.get("verification_state") == "unsupported", f"{label} must mark unsupported verification_state")

    return category


def main() -> int:
    try:
        validate_schema()

        categories: list[str] = []
        for path in sorted(ERROR_FIXTURES.glob("*.json")):
            categories.append(validate_error(load_json(path), str(path.relative_to(ROOT))))

        require(set(categories) == ERROR_CATEGORIES, "fixtures/errors must cover every Packet C error category")
        require(len(categories) == len(set(categories)), "fixtures/errors must include exactly one fixture per category")

    except ValueError as exc:
        print(f"MEMORYCORE_PACKET_C_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_PACKET_C_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
