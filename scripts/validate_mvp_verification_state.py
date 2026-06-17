#!/usr/bin/env python3
"""Validate the MVP verification-state contract against static fixtures.

This is a public-safe contract check only. It does not call QMD, lossless-claw,
Burrow, OpenClaw, or any live runtime.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.lcm_adapter import normalize_lcm_search  # noqa: E402
from memorycore.qmd_adapter import normalize_qmd_get  # noqa: E402
from memorycore.verification_state import (  # noqa: E402
    VERIFICATION_STATES,
    normalize_verification_state,
    normalize_verify_result,
    result_verification_state,
    state_from_error,
)


MOCK_FIXTURES = ROOT / "fixtures" / "mock-backends"
QMD_FIXTURES = ROOT / "fixtures" / "qmd"
LCM_FIXTURES = ROOT / "fixtures" / "lcm"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_request(pointer_id: str | None = "fixtures/corpus/project-alpha.md") -> dict[str, Any]:
    pointer = {"backend_id": "mock_healthy"}
    if pointer_id is not None:
        pointer["pointer_id"] = pointer_id
    return {
        "request_id": "req_verify_fixture",
        "client_surface": "test",
        "operation": "verify",
        "intent": "source_verify",
        "backend_hint": "mock_healthy",
        "pointer": pointer,
    }


def main() -> int:
    try:
        require(
            VERIFICATION_STATES == {"verified", "stale", "missing", "unsupported", "unknown"},
            "Verification states changed",
        )
        require(normalize_verification_state("verified") == "verified", "Verified state should pass through")
        require(normalize_verification_state("fresh") == "unknown", "Unknown states should normalize to unknown")

        verified = normalize_verify_result(
            verify_request(),
            "mock_healthy",
            {"verification_state": "verified"},
        )
        require(verified["verification_state"] == "verified", "Verified fixture should verify")
        require(verified["results"][0]["verification_state"] == "verified", "Result item should preserve verified")

        stale_fixture = load_json(MOCK_FIXTURES / "stale-pointer.json")
        stale = normalize_verify_result(verify_request(), "mock_stale_pointer", stale_fixture["verify_result"])
        require(stale["verification_state"] == "stale", "Stale fixture should normalize to stale")

        missing_fixture = load_json(MOCK_FIXTURES / "missing-pointer.json")
        missing = normalize_verify_result(verify_request(), "mock_missing_pointer", missing_fixture["verify_result"])
        require(missing["verification_state"] == "missing", "Missing fixture should normalize to missing")

        missing_pointer = normalize_verify_result(verify_request(pointer_id=None), "mock_healthy", {"verification_state": "verified"})
        require(missing_pointer["verification_state"] == "missing", "Missing pointer id must never return verified")

        unsupported = normalize_verify_result(
            verify_request(),
            "mock_no_verify",
            {
                "error": {
                    "code": "VERIFICATION_UNSUPPORTED",
                    "category": "verification_unsupported",
                    "message": "Mock backend does not support verification.",
                }
            },
        )
        require(unsupported["status"] == "error", "Unsupported verification should fail")
        require(unsupported["verification_state"] == "unsupported", "Unsupported verification must not return verified")

        timeout = normalize_verify_result(
            verify_request(),
            "mock_timeout",
            {
                "error": {
                    "code": "BACKEND_TIMEOUT",
                    "category": "backend_timeout",
                    "message": "Mock backend timed out.",
                }
            },
        )
        require(timeout["verification_state"] == "unknown", "Backend timeout should normalize to unknown")

        qmd_missing = normalize_qmd_get(verify_request(), load_json(QMD_FIXTURES / "missing-pointer.json"))
        require(result_verification_state(qmd_missing) == "missing", "QMD missing pointer state changed")

        lcm_unavailable = normalize_lcm_search(verify_request(), load_json(LCM_FIXTURES / "unavailable-tool.json"))
        require(result_verification_state(lcm_unavailable) == "unknown", "LCM unavailable state should be unknown")

        require(
            state_from_error({"category": "verification_unsupported"}) == "unsupported",
            "Verification unsupported category should imply unsupported",
        )

    except (KeyError, ValueError) as exc:
        print(f"MEMORYCORE_VERIFICATION_STATE_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_VERIFICATION_STATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
