#!/usr/bin/env python3
"""Validate MEMORYCORE_CONTRACT_SECURITY with public-safe fixtures only.

This check validates contract/security guardrails without calling QMD,
Lossless-Claw, Burrow, OpenClaw, or any live runtime.
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

warnings.filterwarnings("ignore", message="jsonschema.RefResolver is deprecated.*", category=DeprecationWarning)
from jsonschema.validators import RefResolver


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.audit_log import assert_public_safe, build_audit_record  # noqa: E402
from memorycore.lcm_adapter import normalize_lcm_get, normalize_lcm_search  # noqa: E402
from memorycore.provenance_ledger import build_result_records  # noqa: E402
from memorycore.qmd_adapter import normalize_qmd_get, normalize_qmd_search  # noqa: E402
from memorycore.registry_router import BackendRegistry, route_request  # noqa: E402


FIXTURES = ROOT / "fixtures"
SCHEMAS = ROOT / "schemas"
DOCS = ROOT / "docs"
TIMESTAMP = "2026-06-19T14:30:00Z"

FORBIDDEN_PERSISTED_FIELDS = {"snippet", "content", "citations", "summary", "answer", "text"}
OBSERVABILITY_ALLOWED_FIELDS = {
    "event_name",
    "request_id",
    "operation",
    "normalized_intent",
    "client_surface",
    "backend_id",
    "backend_mode",
    "status",
    "error_code",
    "error_category",
    "pointer_id",
    "result_count",
    "result_index",
    "verification_state",
    "elapsed_ms",
    "timestamp",
    "eval_id",
}
OBSERVABILITY_FORBIDDEN_FIELDS = {
    "snippet",
    "content",
    "citations",
    "summary",
    "answer",
    "text",
    "transcript",
    "prompt",
    "credential",
    "token",
    "raw_exception",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema(name: str) -> dict[str, Any]:
    return load_json(SCHEMAS / name)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validator(name: str) -> Draft202012Validator:
    schema_path = SCHEMAS / name
    schema = load_json(schema_path)
    resolver = RefResolver(base_uri=schema_path.as_uri(), referrer=schema)
    return Draft202012Validator(schema, resolver=resolver)


def validate_schema(name: str, instance: dict[str, Any]) -> None:
    try:
        validator(name).validate(instance)
    except ValidationError as exc:
        path = ".".join(str(item) for item in exc.absolute_path) or "<root>"
        raise ValueError(f"{name} rejected {path}: {exc.message}") from exc


def expect_schema_rejects(name: str, instance: dict[str, Any], reason: str) -> None:
    try:
        validator(name).validate(instance)
    except ValidationError:
        return
    raise ValueError(f"{name} accepted invalid instance: {reason}")


def reject_forbidden_fields(value: Any, *, context: str) -> None:
    if isinstance(value, dict):
        bad = sorted(FORBIDDEN_PERSISTED_FIELDS.intersection(value))
        require(not bad, f"{context} contains forbidden persisted fields: {bad}")
        for nested in value.values():
            reject_forbidden_fields(nested, context=context)
    elif isinstance(value, list):
        for nested in value:
            reject_forbidden_fields(nested, context=context)


def validate_request_result_error_contracts() -> None:
    search_request = load_json(FIXTURES / "requests" / "search.json")
    get_request = load_json(FIXTURES / "requests" / "get.json")
    verify_request = load_json(FIXTURES / "requests" / "verify.json")
    validate_schema("request.schema.json", search_request)
    validate_schema("request.schema.json", get_request)
    validate_schema("request.schema.json", verify_request)
    expect_schema_rejects("request.schema.json", load_json(FIXTURES / "requests" / "missing-query.json"), "search without query")
    expect_schema_rejects("request.schema.json", load_json(FIXTURES / "requests" / "invalid-op.json"), "unsupported operation")

    qmd_request = {
        "request_id": "req_contract_qmd_search",
        "client_surface": "test",
        "operation": "search",
        "intent": "file_corpus_recall",
        "backend_hint": "qmd",
        "query": "alpha-river-contract-fixture",
        "limit": 5,
    }
    qmd_search = normalize_qmd_search(qmd_request, load_json(FIXTURES / "qmd" / "search-results.json"))
    validate_schema("result.schema.json", qmd_search)
    require(qmd_search["request_id"] == qmd_request["request_id"], "result request id must echo request")
    require(qmd_search["operation"] == qmd_request["operation"], "result operation must echo request")
    require(qmd_search["status"] == "ok", "fixture search should be ok")
    require(qmd_search["results"][0]["verification_state"] in {"verified", "stale", "missing", "unsupported", "unknown"}, "bad result verification state")

    qmd_get_request = {
        "request_id": "req_contract_qmd_get",
        "client_surface": "test",
        "operation": "get",
        "intent": "source_get",
        "pointer": {"backend_id": "qmd", "pointer_id": "fixtures/corpus/project-alpha.md"},
    }
    qmd_get = normalize_qmd_get(qmd_get_request, load_json(FIXTURES / "qmd" / "get-result.json"))
    validate_schema("result.schema.json", qmd_get)
    require("content" in qmd_get["results"][0], "get response content should remain immediate response data")

    lcm_get_request = {
        "request_id": "req_contract_lcm_get",
        "client_surface": "test",
        "operation": "get",
        "intent": "source_get",
        "pointer": {"backend_id": "lossless_claw", "pointer_id": "sum_public_fixture_001"},
    }
    lcm_get = normalize_lcm_get(lcm_get_request, load_json(FIXTURES / "lcm" / "expand-query-result.json"))
    validate_schema("result.schema.json", lcm_get)
    require("citations" in lcm_get["results"][0], "LCM citations should be schema-described response data")

    registry = BackendRegistry.from_dict(load_json(FIXTURES / "backend-registry" / "basic.json"))
    unsupported_request = {
        "request_id": "req_contract_unsupported_verify",
        "client_surface": "test",
        "operation": "verify",
        "intent": "source_verify",
        "backend_hint": "qmd",
        "pointer": {"backend_id": "qmd", "pointer_id": "fixtures/corpus/project-alpha.md"},
    }
    unsupported_result = route_request(unsupported_request, registry)
    validate_schema("result.schema.json", unsupported_result)
    validate_schema("error.schema.json", unsupported_result["error"])
    require(unsupported_result["error"]["category"] == "verification_unsupported", "unsupported verification category changed")
    require(unsupported_result["error"]["verification_state"] == "unsupported", "unsupported verification state changed")

    for error_fixture in (FIXTURES / "errors").glob("*.json"):
        validate_schema("error.schema.json", load_json(error_fixture))


def validate_public_safe_persistence() -> None:
    qmd_request = {
        "request_id": "req_contract_audit_qmd",
        "client_surface": "test",
        "operation": "search",
        "intent": "file_corpus_recall",
        "backend_hint": "qmd",
        "query": "alpha-river-contract-fixture",
    }
    qmd_search = normalize_qmd_search(qmd_request, load_json(FIXTURES / "qmd" / "search-results.json"))
    audit_record = build_audit_record(qmd_request, qmd_search, timestamp=TIMESTAMP)
    assert_public_safe(audit_record)
    reject_forbidden_fields(audit_record, context="audit record")
    require(audit_record["pointer_ids"] == ["fixtures/corpus/project-alpha.md", "fixtures/corpus/runbook-memorycore.md"], "audit must persist pointer ids")

    provenance_records = build_result_records(qmd_search, timestamp=TIMESTAMP)
    require(len(provenance_records) == 2, "provenance should record one pointer per result")
    for record in provenance_records:
        reject_forbidden_fields(record, context="provenance record")
        require(record["pointer"]["pointer_id"].startswith("fixtures/corpus/"), "provenance must persist pointer ids")

    lcm_request = {
        "request_id": "req_contract_audit_lcm",
        "client_surface": "test",
        "operation": "search",
        "intent": "transcript_continuity_recall",
        "backend_hint": "lossless_claw",
        "query": "\"continuity handoff\"",
    }
    lcm_search = normalize_lcm_search(lcm_request, load_json(FIXTURES / "lcm" / "grep-results.json"))
    lcm_audit = build_audit_record(lcm_request, lcm_search, timestamp=TIMESTAMP)
    assert_public_safe(lcm_audit)
    reject_forbidden_fields(lcm_audit, context="LCM audit record")
    for record in build_result_records(lcm_search, timestamp=TIMESTAMP):
        reject_forbidden_fields(record, context="LCM provenance record")

    try:
        assert_public_safe({"request_id": "req_bad", "snippet": "private fixture text"})
    except ValueError:
        pass
    else:
        raise ValueError("audit public-safe guard accepted forbidden snippet field")


def validate_retrieved_content_is_data() -> None:
    api_contract = (DOCS / "API_CONTRACT.md").read_text(encoding="utf-8")
    threat_model = (DOCS / "THREAT_MODEL.md").read_text(encoding="utf-8")
    combined = f"{api_contract}\n{threat_model}".lower()
    required_phrases = [
        "immediate response data only",
        "not instructions",
        "retrieved content is data",
        "untrusted data",
    ]
    for phrase in required_phrases:
        require(phrase in combined, f"retrieved-content-as-data rule missing phrase: {phrase}")


def validate_observability_contract() -> None:
    observability = (DOCS / "OBSERVABILITY.md").read_text(encoding="utf-8").lower()
    for field in OBSERVABILITY_ALLOWED_FIELDS:
        require(field.replace("_", " ") in observability or f"`{field}`" in observability, f"observability allowed field missing: {field}")
    for field in OBSERVABILITY_FORBIDDEN_FIELDS:
        require(field.replace("_", " ") in observability or field in observability, f"observability forbidden field missing: {field}")

    event = {
        "event_name": "result returned",
        "request_id": "req_contract_qmd_search",
        "operation": "search",
        "client_surface": "test",
        "backend_id": "qmd",
        "backend_mode": "fixture-only",
        "status": "ok",
        "pointer_id": "fixtures/corpus/project-alpha.md",
        "result_count": 2,
        "verification_state": "unknown",
        "elapsed_ms": 4,
        "timestamp": TIMESTAMP,
    }
    require(set(event).issubset(OBSERVABILITY_ALLOWED_FIELDS), "sample observability event has non-allowed field")
    reject_observability_forbidden(event)

    bad_event = {**event, "content": "private fixture text"}
    try:
        reject_observability_forbidden(bad_event)
    except ValueError:
        pass
    else:
        raise ValueError("observability guard accepted forbidden content field")


def reject_observability_forbidden(event: dict[str, Any]) -> None:
    bad = sorted(OBSERVABILITY_FORBIDDEN_FIELDS.intersection(event))
    require(not bad, f"observability event contains forbidden fields: {bad}")


def main() -> int:
    try:
        validate_request_result_error_contracts()
        validate_public_safe_persistence()
        validate_retrieved_content_is_data()
        validate_observability_contract()
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        print(f"MEMORYCORE_CONTRACT_SECURITY_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_CONTRACT_SECURITY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
