#!/usr/bin/env python3
"""Validate the ADR-0006 callback delivery contract with a simulated executor.

Plays both sides: the caller that remembers transcript content, and a
simulated OpenClaw executor that receives the delivery instruction,
"ingests" it, and confirms back with a backend pointer. Deterministic and
public-safe: no OpenClaw, no LCM, no live runtime.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.audit_log import assert_public_safe  # noqa: E402
from memorycore.mcp_surface import call_tool  # noqa: E402


SECRET_CONTENT = "synthetic transcript moment: the continuity handoff decision was ratified."


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def simulated_openclaw_executor(delivery: dict) -> dict:
    """Pretend to be OpenClaw: ingest natively, return the resulting pointer."""
    require(delivery["action"] == "lcm_ingest", "unexpected delivery action")
    require(delivery["backend_id"] == "lossless_claw", "unexpected delivery backend")
    require(SECRET_CONTENT in delivery["content"], "executor should receive the content")
    return {"summary_id": "sum_synthetic_delivery_001", "conversation_id": "conv_synthetic_001"}


def main() -> int:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cache_db = tmp / "cache.sqlite3"
            audit_log = tmp / "audit.jsonl"
            kwargs = {"audit_log": audit_log, "cache_db": cache_db}

            # Leg 1: transcript remember returns a delivery instruction.
            written = call_tool(
                "memorycore_remember",
                {"memory_type": "transcript", "content": SECRET_CONTENT, "client": "openclaw"},
                **kwargs,
            )
            require(written["status"] == "ok", "transcript remember should succeed")
            require(written["write_mode"] == "callback", "transcript write should disclose callback mode")
            item = written["results"][0]
            record_id = item["record_id"]
            require(item["flush_state"] == "awaiting_delivery", "record should await delivery")
            require(item["verification_state"] == "unknown", "undelivered record must be unknown")
            require(written["delivery"]["record_id"] == record_id, "delivery must reference the record")

            # Awaiting-delivery records are ignored by the generic flush pass.
            flushed = call_tool("memorycore_flush", {}, **kwargs)
            require(
                all(r["record_id"] != record_id for r in flushed["results"]),
                "flush must not touch records awaiting delivery",
            )

            # Leg 2: the simulated executor ingests and confirms with a pointer.
            pointer = simulated_openclaw_executor(written["delivery"])
            confirmed = call_tool(
                "memorycore_confirm_delivery",
                {"record_id": record_id, "outcome": "delivered", **pointer, "client": "openclaw"},
                **kwargs,
            )
            require(confirmed["status"] == "ok", "confirmation should succeed")
            result = confirmed["results"][0]
            require(result["flush_state"] == "flushed", "confirmed record should be flushed")
            require(result["pointer"]["summary_id"] == "sum_synthetic_delivery_001", "pointer should update")
            require(
                result["verification_state"] == "unknown",
                "delivered is not proven; verification stays unknown until describe",
            )

            # Round trip: recall serves the delivered pointer.
            recalled = call_tool("memorycore_recall", {"record_id": record_id}, **kwargs)
            require(
                recalled["results"][0]["content_ref"] == "sum_synthetic_delivery_001",
                "recall should serve the delivered pointer",
            )

            # Double-confirmation is rejected: the record is no longer awaiting.
            double = call_tool(
                "memorycore_confirm_delivery",
                {"record_id": record_id, "outcome": "delivered", "summary_id": "sum_other"},
                **kwargs,
            )
            require(double["error"]["code"] == "INVALID_DELIVERY_STATE", "double confirmation should be rejected")

            # Delivered without any pointer field is rejected.
            second = call_tool(
                "memorycore_remember",
                {"memory_type": "transcript", "content": SECRET_CONTENT + " second"},
                **kwargs,
            )
            second_id = second["results"][0]["record_id"]
            no_pointer = call_tool(
                "memorycore_confirm_delivery",
                {"record_id": second_id, "outcome": "delivered"},
                **kwargs,
            )
            require(no_pointer["error"]["code"] == "POINTER_MISSING", "delivered needs a pointer field")

            # Failed delivery marks the record failed.
            failed = call_tool(
                "memorycore_confirm_delivery",
                {"record_id": second_id, "outcome": "failed"},
                **kwargs,
            )
            require(failed["results"][0]["flush_state"] == "failed", "failed outcome should mark failed")

            # Unknown record id is a cache miss.
            miss = call_tool(
                "memorycore_confirm_delivery",
                {"record_id": "cache_nonexistent", "outcome": "delivered", "summary_id": "sum_x"},
                **kwargs,
            )
            require(miss["error"]["code"] == "CACHE_MISS", "unknown record should be a cache miss")

            # Transient contract: content never persisted in cache or audit.
            cache_dump = json.dumps(
                sqlite3.connect(cache_db).execute("SELECT * FROM cache_records").fetchall(), default=str
            )
            require(SECRET_CONTENT not in cache_dump, "content leaked into the cache DB")
            audit_text = audit_log.read_text(encoding="utf-8")
            require(SECRET_CONTENT not in audit_text, "content leaked into the audit log")
            records = [json.loads(line) for line in audit_text.splitlines()]
            require(len(records) >= 7, "each callback leg should append an audit record")
            for record in records:
                assert_public_safe(record)

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"MEMORYCORE_CALLBACK_DELIVERY_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_CALLBACK_DELIVERY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
