#!/usr/bin/env python3
"""Validate the EN-020 JSONL local file backend end to end.

Exercises the zero-dependency path: remember(local, content) writes through
to a JSONL store, recall serves the cached pointer, verification is
proof-based (hash match / tamper -> stale / removal -> missing), and the
content never leaks into the cache DB or audit log. Deterministic and
public-safe: no QMD, no LCM, no OpenClaw, no subprocess.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.audit_log import assert_public_safe  # noqa: E402
from memorycore.jsonl_adapter import jsonl_search  # noqa: E402
from memorycore.mcp_surface import call_tool  # noqa: E402


SECRET_CONTENT = "synthetic local memory: the trellis decision was ratified on the alpha river."


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    saved_env = dict(os.environ)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            store = tmp / "jsonl-store.jsonl"
            cache_db = tmp / "cache.sqlite3"
            audit_log = tmp / "audit.jsonl"
            kwargs = {"audit_log": audit_log, "cache_db": cache_db}

            for key in list(os.environ):
                if key.startswith("MEMORYCORE_"):
                    del os.environ[key]
            os.environ["MEMORYCORE_JSONL_STORE"] = str(store)

            # Write-through works with zero external dependencies, any mode.
            written = call_tool(
                "memorycore_remember",
                {"memory_type": "local", "content": SECRET_CONTENT, "client": "openclaw"},
                **kwargs,
            )
            require(written["status"] == "ok", "local remember should succeed")
            require(written["write_mode"] == "jsonl-local", "local write should disclose jsonl-local mode")
            item = written["results"][0]
            record_id = item["record_id"]
            require(item["verification_state"] == "verified", "read-back should earn verified")
            require(item["flush_state"] == "flushed", "write-through should not stay pending")
            require(item["pointer"]["pointer_id"].startswith("jsonl://memorycore/memory-"), "pointer shape changed")

            # The store holds exactly one line with hash and client attribution.
            lines = [json.loads(line) for line in store.read_text(encoding="utf-8").splitlines()]
            require(len(lines) == 1, "store should hold one memory line")
            require(lines[0]["content"] == SECRET_CONTENT, "store line should hold the content")
            require(lines[0]["client_surface"] == "openclaw", "store line should carry client attribution")

            # Recall serves the cached pointer.
            recalled = call_tool("memorycore_recall", {"record_id": record_id}, **kwargs)
            require(recalled["results"][0]["content_ref"].startswith("jsonl://"), "recall should serve jsonl pointer")

            # Adapter search finds content; a second memory respects limits.
            call_tool("memorycore_remember", {"memory_type": "local", "content": "unrelated second note"}, **kwargs)
            found = jsonl_search(store, "alpha river")
            require(len(found) == 1 and found[0]["content"] == SECRET_CONTENT, "jsonl search should match content")
            require(jsonl_search(store, "note", limit=1)[0]["content"] == "unrelated second note", "limit/order changed")

            # Verification: healthy record verifies, in fixture mode, no env flags.
            verified = call_tool("memorycore_verify", {"record_id": record_id}, **kwargs)
            require(verified["verification_state"] == "verified", "healthy jsonl record should verify")
            require(verified["results"][0]["record_id"] == record_id, "verify should carry record_id")

            # Tamper with the stored content -> stale, stamp updated.
            tampered = [dict(lines[0], content=SECRET_CONTENT + " tampered")]
            remaining = store.read_text(encoding="utf-8").splitlines()[1:]
            store.write_text(
                json.dumps(tampered[0], sort_keys=True, separators=(",", ":")) + "\n" + "\n".join(remaining) + "\n",
                encoding="utf-8",
            )
            stale = call_tool("memorycore_verify", {"record_id": record_id}, **kwargs)
            require(stale["verification_state"] == "stale", "tampered content should be stale")
            require(
                call_tool("memorycore_recall", {"record_id": record_id}, **kwargs)["results"][0]["verification_state"] == "stale",
                "stale verdict should update the cached stamp",
            )

            # Remove the line entirely -> missing.
            store.write_text("\n".join(remaining) + "\n", encoding="utf-8")
            missing = call_tool("memorycore_verify", {"record_id": record_id}, **kwargs)
            require(missing["verification_state"] == "missing", "removed line should be missing")

            # Store file gone -> missing for any record.
            store.unlink()
            require(
                call_tool("memorycore_verify", {"record_id": record_id}, **kwargs)["verification_state"] == "missing",
                "absent store should be missing",
            )

            # Transient contract: content lives in the store only.
            cache_dump = json.dumps(
                sqlite3.connect(cache_db).execute("SELECT * FROM cache_records").fetchall(), default=str
            )
            require(SECRET_CONTENT not in cache_dump, "content leaked into the cache DB")
            audit_text = audit_log.read_text(encoding="utf-8")
            require(SECRET_CONTENT not in audit_text, "content leaked into the audit log")
            for line in audit_text.splitlines():
                assert_public_safe(json.loads(line))

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"MEMORYCORE_JSONL_BACKEND_INVALID: {exc}", file=sys.stderr)
        return 1
    finally:
        os.environ.clear()
        os.environ.update(saved_env)

    print("MEMORYCORE_JSONL_BACKEND_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
