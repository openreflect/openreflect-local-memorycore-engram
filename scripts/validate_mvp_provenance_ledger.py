#!/usr/bin/env python3
"""Validate the MVP provenance pointer ledger against static fixtures.

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

from memorycore.lcm_adapter import normalize_lcm_search  # noqa: E402
from memorycore.provenance_ledger import append_records, build_result_records, read_record  # noqa: E402
from memorycore.qmd_adapter import normalize_qmd_get, normalize_qmd_search  # noqa: E402


QMD_FIXTURES = ROOT / "fixtures" / "qmd"
LCM_FIXTURES = ROOT / "fixtures" / "lcm"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    try:
        timestamp = "2026-06-17T21:45:00Z"
        qmd_request = {
            "request_id": "req_qmd_search_fixture",
            "client_surface": "test",
            "operation": "search",
            "intent": "file_corpus_recall",
            "backend_hint": "qmd",
            "query": "alpha-river-contract-fixture",
        }
        qmd_search = normalize_qmd_search(qmd_request, load_json(QMD_FIXTURES / "search-results.json"))
        qmd_records = build_result_records(qmd_search, timestamp=timestamp)
        require(len(qmd_records) == 2, "QMD search should produce one ledger record per result")
        require(qmd_records[0]["backend_id"] == "qmd", "QMD ledger backend changed")
        require(qmd_records[0]["pointer"]["pointer_id"] == "fixtures/corpus/project-alpha.md", "QMD pointer changed")
        require("snippet" not in qmd_records[0], "Ledger must not store snippets")
        require("content" not in qmd_records[0], "Ledger must not store content")

        lcm_request = {
            "request_id": "req_lcm_search_fixture",
            "client_surface": "test",
            "operation": "search",
            "intent": "transcript_continuity_recall",
            "backend_hint": "lossless_claw",
            "query": "\"continuity handoff\"",
        }
        lcm_search = normalize_lcm_search(lcm_request, load_json(LCM_FIXTURES / "grep-results.json"))
        lcm_records = build_result_records(lcm_search, timestamp=timestamp)
        require(len(lcm_records) == 2, "LCM search should produce one ledger record per result")
        require(lcm_records[0]["pointer"]["summary_id"] == "sum_public_fixture_001", "LCM summary pointer changed")
        require(lcm_records[0]["verification_state"] == "unknown", "LCM ledger must not overclaim verification")

        missing_request = {
            "request_id": "req_qmd_missing_fixture",
            "client_surface": "test",
            "operation": "get",
            "intent": "source_get",
            "backend_hint": "qmd",
            "pointer": {"backend_id": "qmd", "pointer_id": "fixtures/corpus/missing.md"},
        }
        missing_result = normalize_qmd_get(missing_request, load_json(QMD_FIXTURES / "missing-pointer.json"))
        missing_records = build_result_records(missing_result, timestamp=timestamp)
        require(len(missing_records) == 1, "Missing pointer should produce an error ledger record")
        require(missing_records[0]["status"] == "error", "Missing pointer ledger status should be error")
        require(missing_records[0]["error"]["category"] == "pointer_missing", "Missing pointer category changed")
        require(missing_records[0]["verification_state"] == "missing", "Missing pointer verification changed")

        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "provenance.jsonl"
            append_records(ledger_path, qmd_records + lcm_records + missing_records)
            fetched = read_record(ledger_path, lcm_records[0]["ledger_id"])
            require(fetched is not None, "Ledger record could not be read back by id")
            require(fetched["pointer"]["summary_id"] == "sum_public_fixture_001", "Read-back pointer changed")
            require(read_record(ledger_path, "prov_missing") is None, "Missing ledger id should return None")

    except (KeyError, ValueError) as exc:
        print(f"MEMORYCORE_PROVENANCE_LEDGER_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_PROVENANCE_LEDGER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
