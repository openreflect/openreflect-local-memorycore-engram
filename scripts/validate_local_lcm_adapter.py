#!/usr/bin/env python3
"""Validate the local-only host-injected LCM adapter boundary.

This eval uses synthetic in-memory data only. It does not call Lossless-Claw,
OpenClaw, Burrow, or any private transcript store.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.lcm_adapter import host_lcm_get, host_lcm_search, host_lcm_verify  # noqa: E402


class SyntheticLcmBridge:
    def __init__(self) -> None:
        self.records = {
            "sum_synthetic_lcm_001": {
                "summary_id": "sum_synthetic_lcm_001",
                "message_id": "msg_synthetic_lcm_001",
                "conversation_id": "conv_synthetic_lcm",
                "snippet": "Synthetic continuity checkpoint with public-safe local-only content.",
                "score": 9.5,
                "answer": "Synthetic LCM recall preserved pointer identity without proving freshness.",
            },
            "sum_synthetic_lcm_unsupported": {
                "summary_id": "sum_synthetic_lcm_unsupported",
                "message_id": "msg_synthetic_lcm_unsupported",
                "conversation_id": "conv_synthetic_lcm",
                "snippet": "Synthetic pointer exists but the host cannot prove freshness.",
                "score": 2.0,
                "answer": "Synthetic unsupported freshness answer.",
            },
        }

    def lcm_grep(self, *, query: str, scope: str | None = None, limit: int | None = None) -> dict[str, Any]:
        del scope
        results = [record for record in self.records.values() if "synthetic" in query.lower()]
        return {"query": query, "mode": "synthetic_host_grep", "results": results[:limit]}

    def lcm_expand_query(
        self,
        *,
        query: str | None = None,
        prompt: str | None = None,
        summary_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        del query, prompt
        summary_id = (summary_ids or [""])[0]
        record = self.records.get(summary_id)
        if record is None:
            return {
                "error": {
                    "code": "POINTER_MISSING",
                    "category": "pointer_missing",
                    "message": "Synthetic LCM pointer was not found.",
                    "verification_state": "missing",
                }
            }

        return {
            "summary_id": record["summary_id"],
            "conversation_id": record["conversation_id"],
            "answer": record["answer"],
            "citations": [
                {
                    "summary_id": record["summary_id"],
                    "message_id": record["message_id"],
                }
            ],
            "verification_state": "unknown",
        }

    def lcm_describe(self, *, summary_id: str | None = None, message_id: str | None = None) -> dict[str, Any]:
        record = self.records.get(summary_id or "")
        if record is None:
            return {
                "summary_id": summary_id,
                "message_id": message_id,
                "exists": False,
            }

        if summary_id == "sum_synthetic_lcm_unsupported":
            return {
                "summary_id": record["summary_id"],
                "message_id": record["message_id"],
                "conversation_id": record["conversation_id"],
                "exists": True,
                "verification_state": "unsupported",
            }

        return {
            "summary_id": record["summary_id"],
            "message_id": record["message_id"],
            "conversation_id": record["conversation_id"],
            "exists": True,
        }


class TimeoutLcmBridge(SyntheticLcmBridge):
    def lcm_grep(self, *, query: str, scope: str | None = None, limit: int | None = None) -> dict[str, Any]:
        del query, scope, limit
        raise TimeoutError("synthetic timeout")


class UnavailableLcmBridge:
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def search_request() -> dict[str, Any]:
    return {
        "request_id": "req_local_lcm_search_synthetic",
        "client_surface": "local_eval",
        "operation": "search",
        "intent": "transcript_continuity_recall",
        "backend_hint": "lossless_claw",
        "query": "synthetic continuity",
        "limit": 1,
    }


def get_request(pointer_id: str) -> dict[str, Any]:
    return {
        "request_id": "req_local_lcm_get_synthetic",
        "client_surface": "local_eval",
        "operation": "get",
        "intent": "source_get",
        "backend_hint": "lossless_claw",
        "pointer": {"backend_id": "lossless_claw", "pointer_id": pointer_id, "summary_id": pointer_id},
    }


def verify_request(pointer_id: str) -> dict[str, Any]:
    return {
        "request_id": "req_local_lcm_verify_synthetic",
        "client_surface": "local_eval",
        "operation": "verify",
        "intent": "source_verify",
        "backend_hint": "lossless_claw",
        "pointer": {"backend_id": "lossless_claw", "pointer_id": pointer_id, "summary_id": pointer_id},
    }


def run_synthetic() -> None:
    bridge = SyntheticLcmBridge()

    search = host_lcm_search(search_request(), bridge)
    require(search["status"] == "ok", "synthetic grep should normalize")
    require(search["results"][0]["pointer"]["summary_id"] == "sum_synthetic_lcm_001", "grep summary pointer changed")
    require(search["results"][0]["verification_state"] == "unknown", "grep recall must not verify freshness")

    get = host_lcm_get(get_request("sum_synthetic_lcm_001"), bridge)
    require(get["status"] == "ok", "synthetic expand-query should normalize")
    require(get["results"][0]["citations"][0]["message_id"] == "msg_synthetic_lcm_001", "expand-query citation changed")
    require(get["verification_state"] == "unknown", "expand-query recall must not verify freshness")

    verified = host_lcm_verify(verify_request("sum_synthetic_lcm_001"), bridge)
    require(verified["status"] == "ok", "synthetic describe should normalize")
    require(verified["verification_state"] == "verified", "describe existence should verify pointer presence")

    missing = host_lcm_verify(verify_request("sum_synthetic_lcm_missing"), bridge)
    require(missing["status"] == "error", "missing summary should be structured error")
    require(missing["error"]["category"] == "pointer_missing", "missing summary category changed")
    require(missing["verification_state"] == "missing", "missing summary verification state changed")

    unsupported = host_lcm_verify(verify_request("sum_synthetic_lcm_unsupported"), bridge)
    require(unsupported["status"] == "ok", "unsupported freshness should still resolve pointer")
    require(unsupported["verification_state"] == "unsupported", "unsupported freshness state changed")

    unavailable = host_lcm_search(search_request(), UnavailableLcmBridge())
    require(unavailable["status"] == "error", "unavailable host tool should be structured error")
    require(unavailable["error"]["category"] == "backend_unavailable", "unavailable host category changed")

    timed_out = host_lcm_search(search_request(), TimeoutLcmBridge())
    require(timed_out["status"] == "error", "timeout host tool should be structured error")
    require(timed_out["error"]["category"] == "backend_timeout", "timeout host category changed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true", required=True)
    parser.parse_args()

    try:
        run_synthetic()
    except (KeyError, ValueError) as exc:
        print(f"MEMORYCORE_LCM_LIVE_BACKEND_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_LCM_LIVE_BACKEND_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
