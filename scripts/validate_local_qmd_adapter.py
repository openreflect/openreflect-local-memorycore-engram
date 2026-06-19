#!/usr/bin/env python3
"""Validate the local-only QMD live adapter.

This eval is intentionally excluded from public-safe evals. It shells out to a
local QMD CLI only after the caller explicitly supplies a collection.
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.qmd_adapter import live_local_qmd_get, live_local_qmd_search, live_local_qmd_status  # noqa: E402


EVAL_ID = "MEMORYCORE_QMD_LIVE_BACKEND"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def search_request(collection: str) -> dict[str, Any]:
    return {
        "request_id": "req_local_qmd_search",
        "client_surface": "local_eval",
        "operation": "search",
        "intent": "file_corpus_recall",
        "backend_hint": "qmd",
        "query": "alpha river contract fixture",
        "limit": 5,
        "collection": collection,
    }


def get_request(pointer_id: str) -> dict[str, Any]:
    return {
        "request_id": "req_local_qmd_get",
        "client_surface": "local_eval",
        "operation": "get",
        "intent": "source_get",
        "backend_hint": "qmd",
        "pointer": {"backend_id": "qmd", "pointer_id": pointer_id, "source_uri": pointer_id},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", required=True, help="Existing local QMD collection to use for live-local validation")
    parser.add_argument("--qmd-bin", default=os.environ.get("QMD_BIN", "qmd"))
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    args = parser.parse_args()

    try:
        _validate_error_outcomes()

        status = live_local_qmd_status(
            "req_local_qmd_status",
            qmd_bin=args.qmd_bin,
            timeout_seconds=args.timeout_seconds,
        )
        if _blocked(status):
            print(f"{EVAL_ID}_BLOCKED: {status['error']['message']}", file=sys.stderr)
            return 2
        require(status["status"] == "ok", "QMD status did not return ok")
        require(status["results"][0]["recall_mode"] == "qmd_live_local", "status did not use live-local mode")

        search = live_local_qmd_search(
            search_request(args.collection),
            collection=args.collection,
            qmd_bin=args.qmd_bin,
            timeout_seconds=args.timeout_seconds,
        )
        if _blocked(search):
            print(f"{EVAL_ID}_BLOCKED: {search['error']['message']}", file=sys.stderr)
            return 2
        require(search["status"] == "ok", "QMD live-local search did not return ok")
        require(search["results"], "QMD live-local search returned no results")
        require(search["results"][0]["recall_mode"] == "qmd_live_local", "search fell back from live-local mode")
        require(search["verification_state"] == "unknown", "search must not overclaim freshness")

        pointer_id = search["results"][0]["pointer"]["pointer_id"]
        get = live_local_qmd_get(
            get_request(pointer_id),
            qmd_bin=args.qmd_bin,
            timeout_seconds=args.timeout_seconds,
        )
        require(get["status"] == "ok", "QMD live-local get did not return ok")
        require(get["results"][0]["recall_mode"] == "qmd_live_local", "get fell back from live-local mode")
        require(get["verification_state"] == "verified", "resolving a live QMD pointer should verify pointer existence")

        missing = live_local_qmd_get(
            get_request(f"qmd://{args.collection}/memorycore-intentionally-missing-pointer.md"),
            qmd_bin=args.qmd_bin,
            timeout_seconds=args.timeout_seconds,
        )
        require(missing["status"] == "error", "missing live QMD pointer should fail")
        require(missing["error"]["category"] == "pointer_missing", "missing pointer should use pointer_missing")
        require(missing["verification_state"] == "missing", "missing pointer should report missing verification")

    except ValueError as exc:
        print(f"{EVAL_ID}_INVALID: {exc}", file=sys.stderr)
        return 1

    print(f"{EVAL_ID}_OK")
    return 0


def _validate_error_outcomes() -> None:
    unavailable = live_local_qmd_status("req_local_qmd_unavailable", qmd_bin="memorycore-qmd-not-installed")
    require(unavailable["status"] == "error", "unavailable QMD should fail")
    require(unavailable["error"]["category"] == "backend_unavailable", "unavailable QMD should use backend_unavailable")
    require(unavailable["verification_state"] == "unknown", "unavailable QMD should leave freshness unknown")

    with tempfile.TemporaryDirectory() as tmp:
        timeout_bin = _script(Path(tmp) / "qmd-timeout", "import time; time.sleep(2)")
        timed_out = live_local_qmd_status("req_local_qmd_timeout", qmd_bin=str(timeout_bin), timeout_seconds=0.1)
        require(timed_out["status"] == "error", "timeout should fail")
        require(timed_out["error"]["category"] == "backend_timeout", "timeout should use backend_timeout")
        require(timed_out["verification_state"] == "unknown", "timeout should leave freshness unknown")

        error_bin = _script(Path(tmp) / "qmd-error", "import sys; print('synthetic qmd command error', file=sys.stderr); sys.exit(7)")
        command_error = live_local_qmd_status("req_local_qmd_command_error", qmd_bin=str(error_bin), timeout_seconds=1.0)
        require(command_error["status"] == "error", "command error should fail")
        require(command_error["error"]["category"] == "unknown_failure", "command error should use unknown_failure")
        require(command_error["verification_state"] == "unknown", "command error should leave freshness unknown")


def _script(path: Path, body: str) -> Path:
    path.write_text(f"#!/usr/bin/env python3\n{body}\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def _blocked(result: dict[str, Any]) -> bool:
    if result.get("status") != "error":
        return False
    error = result.get("error", {})
    return error.get("category") == "backend_unavailable"


if __name__ == "__main__":
    raise SystemExit(main())
