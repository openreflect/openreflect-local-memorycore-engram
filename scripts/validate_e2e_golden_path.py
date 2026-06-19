#!/usr/bin/env python3
"""Validate EVAL-013 public-safe CLI/MCP golden path.

This fixture-only check proves successful and failed request loops through the
existing CLI and MCP-shaped surfaces, then records temporary content-sparse
audit and provenance metadata. It does not start an MCP server, call OpenClaw,
call live QMD/Lossless-Claw, or run EVAL-012.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.audit_log import PRIVATE_RESULT_FIELDS, read_recent  # noqa: E402
from memorycore.mcp_surface import call_tool  # noqa: E402
from memorycore.provenance_ledger import append_records, build_result_records  # noqa: E402


TIMESTAMP = "2026-06-19T12:00:00Z"
SUCCESS_POINTER = "fixtures/corpus/project-alpha.md"
FORBIDDEN_FIELD_TOKENS = [f'"{field}"' for field in PRIVATE_RESULT_FIELDS]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run_cli(audit_log: Path, *args: str, expect_ok: bool = True) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-m", "memorycore.cli", "--audit-log", str(audit_log), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if expect_ok and completed.returncode != 0:
        raise ValueError(f"CLI command failed: {' '.join(args)}\n{completed.stderr}\n{completed.stdout}")
    if not expect_ok and completed.returncode == 0:
        raise ValueError(f"CLI command unexpectedly succeeded: {' '.join(args)}")
    return json.loads(completed.stdout)


def assert_no_private_fields(value: Any, context: str) -> None:
    serialized = json.dumps(value, sort_keys=True)
    leaked = [token for token in FORBIDDEN_FIELD_TOKENS if token in serialized]
    require(not leaked, f"{context} leaked private result fields: {', '.join(leaked)}")


def assert_success_loop(surface: str, search: dict[str, Any], get: dict[str, Any], verify: dict[str, Any]) -> None:
    require(search["status"] == "ok", f"{surface} search should succeed")
    require(search["selected_backend"] == "qmd", f"{surface} search should route to qmd")
    require(search["results"][0]["pointer"]["pointer_id"] == SUCCESS_POINTER, f"{surface} search pointer changed")
    require(search["results"][0]["verification_state"] == "unknown", f"{surface} search verification changed")
    require(search["audit_id"].startswith("audit_"), f"{surface} search should include audit id")

    require(get["status"] == "ok", f"{surface} get should succeed")
    require(get["results"][0]["pointer"]["pointer_id"] == SUCCESS_POINTER, f"{surface} get pointer changed")
    require(get["audit_id"].startswith("audit_"), f"{surface} get should include audit id")

    require(verify["status"] == "ok", f"{surface} verify should succeed")
    require(verify["selected_backend"] == "mock_healthy", f"{surface} verify backend changed")
    require(verify["verification_state"] == "verified", f"{surface} verify state changed")
    require(verify["audit_id"].startswith("audit_"), f"{surface} verify should include audit id")


def assert_failed_loop(surface: str, result: dict[str, Any]) -> None:
    require(result["status"] == "error", f"{surface} unsupported verify should fail")
    require(result["operation"] == "verify", f"{surface} failure operation changed")
    require(result["error"]["code"] == "VERIFICATION_UNSUPPORTED", f"{surface} failure code changed")
    require(result["error"]["category"] == "verification_unsupported", f"{surface} failure category changed")
    require(result["error"]["verification_state"] == "unsupported", f"{surface} failure verification state changed")
    require(result["audit_id"].startswith("audit_"), f"{surface} failure should include audit id")


def assert_audit(path: Path, surface: str) -> list[dict[str, Any]]:
    records = read_recent(path, limit=10)
    require(len(records) == 4, f"{surface} should write four audit records")
    require([record["operation"] for record in records] == ["search", "get", "verify", "verify"], f"{surface} audit operation order changed")
    require(records[-1]["status"] == "error", f"{surface} failure audit status changed")
    require(records[-1]["error_state"]["category"] == "verification_unsupported", f"{surface} failure audit category changed")
    for record in records:
        require(record["client_surface"] == surface, f"{surface} audit client surface changed")
        assert_no_private_fields(record, f"{surface} audit record")
    return records


def append_provenance(path: Path, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for result in results:
        records.extend(build_result_records(result, timestamp=TIMESTAMP))
    append_records(path, records)
    return records


def assert_provenance(path: Path, records: list[dict[str, Any]], surface: str) -> None:
    require(path.exists(), f"{surface} provenance file should exist")
    persisted = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    require(persisted == records, f"{surface} provenance read-back changed")
    require(len(records) == 5, f"{surface} should write five provenance records")
    require(any(record["status"] == "error" for record in records), f"{surface} failure provenance missing")
    require(any(record.get("error", {}).get("category") == "verification_unsupported" for record in records), f"{surface} failure provenance category missing")
    require(any(record.get("pointer", {}).get("pointer_id") == SUCCESS_POINTER for record in records), f"{surface} success provenance pointer missing")
    for record in records:
        assert_no_private_fields(record, f"{surface} provenance record")


def assert_core_equivalence(cli_result: dict[str, Any], mcp_result: dict[str, Any], context: str) -> None:
    cli_core = {key: value for key, value in cli_result.items() if key not in {"request_id", "audit_id"}}
    mcp_core = {key: value for key, value in mcp_result.items() if key not in {"request_id", "audit_id"}}
    require(cli_core == mcp_core, f"{context} CLI/MCP core result diverged")


def main() -> int:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cli_audit = tmp / "cli-audit.jsonl"
            mcp_audit = tmp / "mcp-audit.jsonl"
            cli_provenance = tmp / "cli-provenance.jsonl"
            mcp_provenance = tmp / "mcp-provenance.jsonl"

            cli_health = run_cli(cli_audit, "health")
            mcp_health = call_tool("memorycore_health", {}, audit_log=mcp_audit)
            assert_core_equivalence(cli_health, mcp_health, "health")
            require(cli_health["status"] == "ok", "health should succeed")

            cli_search = run_cli(cli_audit, "search", "alpha-river-contract-fixture", "--intent", "file_corpus_recall")
            mcp_search = call_tool(
                "memorycore_search",
                {"query": "alpha-river-contract-fixture", "intent": "file_corpus_recall"},
                audit_log=mcp_audit,
            )
            assert_core_equivalence(cli_search, mcp_search, "search")

            cli_get = run_cli(cli_audit, "get", SUCCESS_POINTER, "--backend", "qmd")
            mcp_get = call_tool("memorycore_get", {"pointer_id": SUCCESS_POINTER, "backend": "qmd"}, audit_log=mcp_audit)
            assert_core_equivalence(cli_get, mcp_get, "get")

            cli_verify = run_cli(cli_audit, "verify", SUCCESS_POINTER, "--backend", "mock_healthy", "--state", "verified")
            mcp_verify = call_tool(
                "memorycore_verify",
                {"pointer_id": SUCCESS_POINTER, "backend": "mock_healthy", "state": "verified"},
                audit_log=mcp_audit,
            )
            assert_core_equivalence(cli_verify, mcp_verify, "verify")

            cli_failure = run_cli(cli_audit, "verify", SUCCESS_POINTER, "--backend", "qmd", expect_ok=False)
            mcp_failure = call_tool("memorycore_verify", {"pointer_id": SUCCESS_POINTER, "backend": "qmd"}, audit_log=mcp_audit)
            assert_core_equivalence(cli_failure, mcp_failure, "unsupported verify")

            assert_success_loop("cli", cli_search, cli_get, cli_verify)
            assert_success_loop("mcp", mcp_search, mcp_get, mcp_verify)
            assert_failed_loop("cli", cli_failure)
            assert_failed_loop("mcp", mcp_failure)

            assert_audit(cli_audit, "cli")
            assert_audit(mcp_audit, "mcp")

            cli_provenance_records = append_provenance(cli_provenance, [cli_search, cli_get, cli_verify, cli_failure])
            mcp_provenance_records = append_provenance(mcp_provenance, [mcp_search, mcp_get, mcp_verify, mcp_failure])
            assert_provenance(cli_provenance, cli_provenance_records, "cli")
            assert_provenance(mcp_provenance, mcp_provenance_records, "mcp")

            # EVAL-012/OpenClaw is deliberately represented only as a gate here.
            openclaw_status = {
                "eval_id": "MEMORYCORE_OPENCLAW_SMOKE",
                "status": "not-run-by-design",
                "reason": "hard stop remains active; PACKET-08 is fixture-only CLI/MCP coverage",
            }
            require(openclaw_status["status"] == "not-run-by-design", "OpenClaw smoke gate changed")

    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"MEMORYCORE_E2E_GOLDEN_PATH_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_E2E_GOLDEN_PATH_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
