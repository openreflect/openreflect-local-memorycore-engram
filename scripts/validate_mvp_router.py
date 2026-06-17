#!/usr/bin/env python3
"""Validate MVP registry/router behavior against static fixtures.

This is a deterministic contract check only. It does not call live QMD,
Lossless-Claw, Burrow, OpenClaw, or public-safe eval runners.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.registry_router import BackendRegistry, route_request  # noqa: E402


REGISTRY_PATH = ROOT / "fixtures" / "backend-registry" / "basic.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def fixture_request(**overrides: Any) -> dict[str, Any]:
    request: dict[str, Any] = {
        "request_id": "req_router_fixture",
        "client_surface": "test",
        "operation": "search",
        "intent": "file_corpus_recall",
        "query": "alpha-river-contract-fixture",
    }
    request.update(overrides)
    return request


def expect_ok(result: dict[str, Any], backend_id: str, label: str) -> None:
    require(result["status"] == "ok", f"{label} should route successfully")
    require(result["selected_backend"] == backend_id, f"{label} selected {result.get('selected_backend')!r}, expected {backend_id!r}")


def expect_error(result: dict[str, Any], category: str, label: str) -> None:
    require(result["status"] == "error", f"{label} should fail")
    require(result["error"]["category"] == category, f"{label} returned {result['error']['category']!r}, expected {category!r}")
    require(result["results"] == [], f"{label} must not return successful empty memory data")


def main() -> int:
    try:
        registry_data = load_json(REGISTRY_PATH)
        registry = BackendRegistry.from_dict(registry_data)

        expect_ok(route_request(fixture_request(), registry), "qmd", "file/corpus auto route")
        expect_ok(
            route_request(fixture_request(intent="transcript_continuity_recall"), registry),
            "lossless_claw",
            "transcript auto route",
        )
        expect_ok(
            route_request(fixture_request(backend_hint="mock_healthy"), registry),
            "mock_healthy",
            "explicit backend hint",
        )
        expect_ok(
            route_request(
                fixture_request(
                    operation="get",
                    intent="source_get",
                    pointer={"backend_id": "mock_healthy", "pointer_id": "fixture/project-alpha.md"},
                ),
                registry,
            ),
            "mock_healthy",
            "pointer backend route",
        )

        health = route_request(fixture_request(operation="health", intent="backend_health"), registry)
        require(health["status"] == "ok", "health request should succeed")
        require(len(health["results"]) == len(registry_data["backends"]), "health request should list every backend")

        expect_error(
            route_request(fixture_request(backend_hint="does_not_exist"), registry),
            "missing_backend",
            "missing backend",
        )
        expect_error(
            route_request(fixture_request(backend_hint="mock_unhealthy"), registry),
            "backend_unavailable",
            "unavailable backend",
        )
        expect_error(
            route_request(
                fixture_request(
                    operation="verify",
                    intent="source_verify",
                    pointer={"backend_id": "qmd", "pointer_id": "fixture/project-alpha.md"},
                ),
                registry,
            ),
            "verification_unsupported",
            "unsupported verify",
        )
        expect_error(
            route_request(fixture_request(operation="get", intent="file_corpus_recall"), registry),
            "unsupported_operation",
            "intent operation mismatch",
        )

        duplicate_data = {"backends": registry_data["backends"] + [registry_data["backends"][0]]}
        try:
            BackendRegistry.from_dict(duplicate_data)
        except ValueError as exc:
            require("duplicate backend_id" in str(exc), "duplicate rejection should name backend_id")
        else:
            raise ValueError("duplicate backend ids must be rejected")

    except (KeyError, ValueError) as exc:
        print(f"MEMORYCORE_ROUTER_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_ROUTER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
