#!/usr/bin/env python3
"""Validate the OpenClaw-facing cache API on the MCP tool surface.

This check exercises memorycore_remember / recall / cache_search / flush
against a temporary SQLite cache and audit log. It does not call QMD,
lossless-claw, Burrow, OpenClaw, or any live runtime; flush handlers are
fixture-only acknowledgments.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.audit_log import assert_public_safe  # noqa: E402
from memorycore.mcp_surface import CACHE_TOOL_NAMES, call_tool, list_tools  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    saved_store = os.environ.get("MEMORYCORE_JSONL_STORE")
    try:
        tool_names = {tool["name"] for tool in list_tools()}
        require(CACHE_TOOL_NAMES <= tool_names, "Cache tools missing from MCP tool definitions")

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_db = Path(tmpdir) / "cache.sqlite3"
            audit_log = Path(tmpdir) / "audit.jsonl"
            kwargs = {"audit_log": audit_log, "cache_db": cache_db}
            # Isolate content fan-out from any operator jsonl store.
            os.environ["MEMORYCORE_JSONL_STORE"] = str(Path(tmpdir) / "jsonl-store.jsonl")
            os.environ.setdefault("MEMORYCORE_CONFIG", str(Path(tmpdir) / "config.json"))

            # remember: file_corpus record lands pending with a stamped pointer.
            written = call_tool(
                "memorycore_remember",
                {
                    "memory_type": "file_corpus",
                    "content_ref": "fixtures/corpus/project-alpha.md",
                },
                **kwargs,
            )
            require(written["status"] == "ok", "remember should succeed")
            item = written["results"][0]
            require(item["record_id"].startswith("cache_"), "remember record id prefix changed")
            require(item["flush_state"] == "pending", "remember should leave records pending")
            require(item["pointer"]["backend_id"] == "qmd", "file_corpus should route to qmd")
            require("audit_id" in written, "remember must append an audit record")

            # remember from OpenClaw: client surface is carried through to audit.
            transcript = call_tool(
                "memorycore_remember",
                {
                    "memory_type": "transcript",
                    "content_ref": "sum_public_fixture_001",
                    "summary_id": "sum_public_fixture_001",
                    "verification": "verified",
                    "client": "openclaw",
                },
                **kwargs,
            )
            require(transcript["results"][0]["pointer"]["backend_id"] == "lossless_claw", "transcript should route to lcm")
            require(transcript["results"][0]["verification_state"] == "verified", "explicit verification dropped")
            require(transcript["request_id"].startswith("req_openclaw_"), "openclaw client surface not reflected")

            audit_lines = [json.loads(line) for line in audit_log.read_text(encoding="utf-8").splitlines()]
            require(audit_lines[-1]["client_surface"] == "openclaw", "audit must record openclaw client surface")
            for record in audit_lines:
                assert_public_safe(record)

            # Content-sparse contract: raw content arguments are rejected.
            try:
                call_tool(
                    "memorycore_remember",
                    {
                        "memory_type": "file_corpus",
                        "content_ref": "fixtures/corpus/project-alpha.md",
                        "snippet": "private text that must not reach the cache",
                    },
                    **kwargs,
                )
                raise ValueError("remember accepted a forbidden content argument")
            except ValueError as exc:
                require("unexpected MCP argument" in str(exc), "forbidden-argument rejection changed")

            # recall: hit by record id, then by pointer id.
            recalled = call_tool("memorycore_recall", {"record_id": item["record_id"]}, **kwargs)
            require(recalled["status"] == "ok", "recall by record id failed")
            require(recalled["results"][0]["content_ref"] == "fixtures/corpus/project-alpha.md", "recall returned wrong record")
            by_pointer = call_tool("memorycore_recall", {"pointer_id": "fixtures/corpus/project-alpha.md"}, **kwargs)
            require(by_pointer["results"][0]["record_id"] == item["record_id"], "recall by pointer id failed")

            # recall: miss is an explicit content-sparse error, never a fake hit.
            miss = call_tool("memorycore_recall", {"record_id": "cache_missing"}, **kwargs)
            require(miss["status"] == "error", "cache miss should be an error result")
            require(miss["error"]["code"] == "CACHE_MISS", "cache miss code changed")
            require(miss["verification_state"] == "missing", "cache miss verification changed")

            # recall: id-less calls are rejected.
            try:
                call_tool("memorycore_recall", {}, **kwargs)
                raise ValueError("recall accepted a call without any id")
            except ValueError as exc:
                require("record_id or pointer_id" in str(exc), "recall id requirement changed")

            # cache_search: cached records only, filterable and limited.
            found = call_tool("memorycore_cache_search", {"query": "project-alpha"}, **kwargs)
            require(len(found["results"]) == 1, "cache_search should match the alpha record once")
            filtered = call_tool(
                "memorycore_cache_search",
                {"query": "fixture", "memory_type": "transcript"},
                **kwargs,
            )
            require(
                all(item["memory_type"] == "transcript" for item in filtered["results"]),
                "cache_search type filter failed",
            )

            # flush: pending records flush via fixture handlers, marked as such.
            flushed = call_tool("memorycore_flush", {}, **kwargs)
            require(flushed["status"] == "ok", "flush should succeed")
            require(flushed["flush_mode"] == "fixture-only", "flush must disclose fixture-only mode")
            require(len(flushed["results"]) == 2, "flush should process both pending records")
            require(
                all(item["flush_state"] == "flushed" for item in flushed["results"]),
                "fixture flush should mark records flushed",
            )

            # Second flush pass has nothing pending.
            require(call_tool("memorycore_flush", {}, **kwargs)["results"] == [], "flush must only touch pending records")

    except (KeyError, ValueError) as exc:
        print(f"MEMORYCORE_CACHE_API_INVALID: {exc}", file=sys.stderr)
        return 1
    finally:
        if saved_store is None:
            os.environ.pop("MEMORYCORE_JSONL_STORE", None)
        else:
            os.environ["MEMORYCORE_JSONL_STORE"] = saved_store

    print("MEMORYCORE_CACHE_API_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
