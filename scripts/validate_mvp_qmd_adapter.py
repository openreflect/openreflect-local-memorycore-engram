#!/usr/bin/env python3
"""Validate the MVP QMD adapter contract against static fixtures.

This is a public-safe contract check only. It does not call QMD, Burrow,
OpenClaw, or any live local index.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.qmd_adapter import normalize_qmd_get, normalize_qmd_search, qmd_health  # noqa: E402


QMD_FIXTURES = ROOT / "fixtures" / "qmd"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    try:
        search_request = {
            "request_id": "req_qmd_search_fixture",
            "client_surface": "test",
            "operation": "search",
            "intent": "file_corpus_recall",
            "backend_hint": "qmd",
            "query": "alpha-river-contract-fixture",
        }
        search = normalize_qmd_search(search_request, load_json(QMD_FIXTURES / "search-results.json"))
        require(search["status"] == "ok", "QMD search fixture should normalize successfully")
        require(search["selected_backend"] == "qmd", "QMD search should select qmd backend")
        require(len(search["results"]) == 2, "QMD search should preserve fixture result count")
        require(search["results"][0]["rank"] == 1, "QMD search should assign stable ranks")
        require(search["results"][0]["pointer"]["pointer_id"] == "fixtures/corpus/project-alpha.md", "QMD pointer path changed")
        require(search["results"][0]["verification_state"] == "unknown", "QMD search must not overclaim verification")

        get_request = {
            "request_id": "req_qmd_get_fixture",
            "client_surface": "test",
            "operation": "get",
            "intent": "source_get",
            "backend_hint": "qmd",
            "pointer": {"backend_id": "qmd", "pointer_id": "fixtures/corpus/project-alpha.md"},
        }
        get_result = normalize_qmd_get(get_request, load_json(QMD_FIXTURES / "get-result.json"))
        require(get_result["status"] == "ok", "QMD get fixture should normalize successfully")
        require(get_result["results"][0]["content"].startswith("# Project Alpha"), "QMD get content was not preserved")
        require(get_result["verification_state"] == "unknown", "QMD get must not overclaim verification")

        missing = normalize_qmd_get(get_request, load_json(QMD_FIXTURES / "missing-pointer.json"))
        require(missing["status"] == "error", "QMD missing pointer should fail")
        require(missing["error"]["category"] == "pointer_missing", "QMD missing pointer should use pointer_missing")
        require(missing["verification_state"] == "missing", "QMD missing pointer should report missing verification")

        health = qmd_health("req_qmd_health_fixture")
        require(health["status"] == "ok", "QMD health fixture should return ok")
        require(health["verification_state"] == "unknown", "QMD health should not imply source verification")

    except (KeyError, ValueError) as exc:
        print(f"MEMORYCORE_QMD_ADAPTER_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_QMD_ADAPTER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
