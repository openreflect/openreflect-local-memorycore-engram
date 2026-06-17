#!/usr/bin/env python3
"""Validate the MVP Lossless-Claw adapter contract against static fixtures.

This is a public-safe contract check only. It does not call lossless-claw,
Burrow, OpenClaw, or any live transcript store.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.lcm_adapter import lcm_health, normalize_lcm_get, normalize_lcm_search  # noqa: E402


LCM_FIXTURES = ROOT / "fixtures" / "lcm"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    try:
        search_request = {
            "request_id": "req_lcm_search_fixture",
            "client_surface": "test",
            "operation": "search",
            "intent": "transcript_continuity_recall",
            "backend_hint": "lossless_claw",
            "query": "\"continuity handoff\"",
        }
        search = normalize_lcm_search(search_request, load_json(LCM_FIXTURES / "grep-results.json"))
        require(search["status"] == "ok", "LCM search fixture should normalize successfully")
        require(search["selected_backend"] == "lossless_claw", "LCM search should select lossless_claw backend")
        require(len(search["results"]) == 2, "LCM search should preserve fixture result count")
        require(search["results"][0]["rank"] == 1, "LCM search should assign stable ranks")
        require(search["results"][0]["pointer"]["summary_id"] == "sum_public_fixture_001", "LCM summary pointer changed")
        require(search["results"][0]["verification_state"] == "unknown", "LCM search must not overclaim verification")

        get_request = {
            "request_id": "req_lcm_get_fixture",
            "client_surface": "test",
            "operation": "get",
            "intent": "source_get",
            "backend_hint": "lossless_claw",
            "pointer": {"backend_id": "lossless_claw", "pointer_id": "sum_public_fixture_001"},
        }
        get_result = normalize_lcm_get(get_request, load_json(LCM_FIXTURES / "expand-query-result.json"))
        require(get_result["status"] == "ok", "LCM get fixture should normalize successfully")
        require(get_result["results"][0]["content"].startswith("The public fixture says"), "LCM get content was not preserved")
        require(get_result["results"][0]["citations"][0]["summary_id"] == "sum_public_fixture_001", "LCM citations were not preserved")
        require(get_result["verification_state"] == "unknown", "LCM get must not overclaim freshness")

        missing = normalize_lcm_get(get_request, load_json(LCM_FIXTURES / "missing-pointer.json"))
        require(missing["status"] == "error", "LCM missing pointer should fail")
        require(missing["error"]["category"] == "pointer_missing", "LCM missing pointer should use pointer_missing")
        require(missing["verification_state"] == "missing", "LCM missing pointer should report missing verification")

        unavailable = normalize_lcm_search(search_request, load_json(LCM_FIXTURES / "unavailable-tool.json"))
        require(unavailable["status"] == "error", "LCM unavailable tool should fail")
        require(unavailable["error"]["category"] == "backend_unavailable", "LCM unavailable tool should use backend_unavailable")

        health = lcm_health("req_lcm_health_fixture")
        require(health["status"] == "ok", "LCM health fixture should return ok")
        require(health["verification_state"] == "unknown", "LCM health should not imply source verification")

    except (KeyError, ValueError) as exc:
        print(f"MEMORYCORE_LCM_ADAPTER_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_LCM_ADAPTER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
