#!/usr/bin/env python3
"""Validate EVAL-009 request/result audit records with static fixtures only.

This check writes only temporary public-safe metadata. It does not call QMD,
lossless-claw, Burrow, OpenClaw, or any live runtime.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.audit_log import append_record, assert_public_safe, build_audit_record, read_recent  # noqa: E402
from memorycore.lcm_adapter import normalize_lcm_search  # noqa: E402
from memorycore.qmd_adapter import normalize_qmd_search  # noqa: E402
from memorycore.registry_router import BackendRegistry, route_request  # noqa: E402


FIXTURES = ROOT / "fixtures"
TIMESTAMP = "2026-06-17T22:35:00Z"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_record(record: dict[str, Any]) -> None:
    required = {
        "audit_id",
        "request_id",
        "client_surface",
        "operation",
        "normalized_intent",
        "result_count",
        "pointer_ids",
        "verification_state",
        "error_state",
        "timestamp",
        "status",
    }
    require(required.issubset(record), f"audit record missing fields: {sorted(required - set(record))}")
    require(record["audit_id"].startswith("audit_"), "audit id prefix changed")
    require(record["verification_state"] in {"verified", "stale", "missing", "unsupported", "unknown"}, "bad verification state")
    assert_public_safe(record)


def main() -> int:
    try:
        qmd_request = {
            "request_id": "req_audit_qmd_search",
            "client_surface": "cli",
            "operation": "search",
            "intent": "file_corpus_recall",
            "backend_hint": "qmd",
            "query": "alpha-river-contract-fixture",
        }
        qmd_result = normalize_qmd_search(qmd_request, load_json(FIXTURES / "qmd" / "search-results.json"))
        qmd_record = build_audit_record(qmd_request, qmd_result, timestamp=TIMESTAMP)
        validate_record(qmd_record)
        require(qmd_record["selected_backend"] == "qmd", "QMD selected backend changed")
        require(qmd_record["result_count"] == 2, "QMD result count changed")
        require(qmd_record["pointer_ids"] == ["fixtures/corpus/project-alpha.md", "fixtures/corpus/runbook-memorycore.md"], "QMD pointer ids changed")
        require(qmd_record["error_state"] is None, "Successful QMD audit should not have error state")

        lcm_request = {
            "request_id": "req_audit_lcm_search",
            "client_surface": "mcp",
            "operation": "search",
            "intent": "transcript_continuity_recall",
            "backend_hint": "lossless_claw",
            "query": "\"continuity handoff\"",
        }
        lcm_result = normalize_lcm_search(lcm_request, load_json(FIXTURES / "lcm" / "grep-results.json"))
        lcm_record = build_audit_record(lcm_request, lcm_result, timestamp=TIMESTAMP)
        validate_record(lcm_record)
        require(lcm_record["selected_backend"] == "lossless_claw", "LCM selected backend changed")
        require(lcm_record["pointer_ids"] == ["sum_public_fixture_001", "sum_public_fixture_002"], "LCM pointer ids changed")

        registry = BackendRegistry.from_dict(load_json(FIXTURES / "backend-registry" / "basic.json"))
        unsupported_request = {
            "request_id": "req_audit_unsupported",
            "client_surface": "test",
            "operation": "verify",
            "intent": "source_verify",
            "backend_hint": "qmd",
            "pointer": {"backend_id": "qmd", "pointer_id": "fixtures/corpus/project-alpha.md"},
        }
        unsupported_record = build_audit_record(unsupported_request, route_request(unsupported_request, registry), timestamp=TIMESTAMP)
        validate_record(unsupported_record)
        require(unsupported_record["status"] == "error", "Unsupported operation should audit as error")
        require(unsupported_record["selected_backend"] == "qmd", "Unsupported selected backend changed")
        require(unsupported_record["error_state"]["category"] == "verification_unsupported", "Unsupported category changed")
        require(unsupported_record["verification_state"] == "unsupported", "Unsupported verification state changed")

        unavailable_request = {
            "request_id": "req_audit_unavailable",
            "client_surface": "test",
            "operation": "search",
            "intent": "file_corpus_recall",
            "backend_hint": "mock_unhealthy",
            "query": "public fixture",
        }
        unavailable_record = build_audit_record(unavailable_request, route_request(unavailable_request, registry), timestamp=TIMESTAMP)
        validate_record(unavailable_record)
        require(unavailable_record["error_state"]["category"] == "backend_unavailable", "Unavailable category changed")

        validation_request = {
            "request_id": "req_audit_validation",
            "client_surface": "openclaw",
            "operation": "search",
            "intent": "file_corpus_recall",
            "query": "",
        }
        validation_result = {
            "request_id": validation_request["request_id"],
            "operation": validation_request["operation"],
            "status": "error",
            "results": [],
            "verification_state": "unknown",
            "error": load_json(FIXTURES / "errors" / "validation.json"),
        }
        validation_record = build_audit_record(validation_request, validation_result, timestamp=TIMESTAMP)
        validate_record(validation_record)
        require(validation_record["error_state"]["category"] == "validation", "Validation category changed")

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit.jsonl"
            for record in [qmd_record, lcm_record, unsupported_record, unavailable_record, validation_record]:
                append_record(audit_path, record)
            recent = read_recent(audit_path, limit=3)
            require(len(recent) == 3, "Recent audit limit changed")
            require(recent[-1]["request_id"] == "req_audit_validation", "Recent audit ordering changed")
            require(read_recent(audit_path.with_name("missing.jsonl")) == [], "Missing audit log should read as empty")

    except (KeyError, TypeError, ValueError) as exc:
        print(f"MEMORYCORE_AUDIT_LOG_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_AUDIT_LOG_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
