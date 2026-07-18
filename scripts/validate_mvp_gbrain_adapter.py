#!/usr/bin/env python3
"""Validate the EN-035 gbrain adapter contract and knowledge memory type.

Fixture-first: normalizes gbrain-shaped capture and page output into the
shared contract, and proves the knowledge routing path end to end (pointer
remembers, fixture write-through with capture-receipt shape, honest
live-local degradation, flush acknowledgment, operator toggles). It does
not call a live gbrain install.
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
from memorycore.gbrain_adapter import normalize_gbrain_capture, normalize_gbrain_page  # noqa: E402
from memorycore.mcp_surface import call_tool  # noqa: E402


def load_json(name: str):
    return json.loads((ROOT / "fixtures" / "gbrain" / name).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    saved_env = dict(os.environ)
    try:
        request = {"request_id": "req_gbrain_fixture", "client_surface": "test", "operation": "cache_write"}

        # Capture normalization: slug pointer + hash receipt, never overclaimed.
        captured = normalize_gbrain_capture(request, load_json("capture-result.json"))
        require(captured["status"] == "ok", "capture fixture should normalize ok")
        require(captured["results"][0]["pointer"]["pointer_id"] == "gbrain://pages/alpha-river-decision",
                "capture pointer shape changed")
        require(captured["content_hash"].startswith("1f6d0c4a"), "capture hash receipt missing")
        require(captured["verification_state"] == "unknown", "capture ack must not claim verified")

        failed = normalize_gbrain_capture(request, load_json("capture-failed.json"))
        require(failed["status"] == "error" and failed["error"]["code"] == "GBRAIN_CAPTURE_FAILED",
                "rejected capture should be a structured error")

        page = normalize_gbrain_page({"request_id": "req_gbrain_page"}, load_json("page-result.json"))
        require(page["status"] == "ok" and page["results"][0]["recall_mode"] == "gbrain_page",
                "page fixture should normalize")
        missing = normalize_gbrain_page({"request_id": "req_gbrain_missing"}, {})
        require(missing["error"]["category"] == "pointer_missing", "missing page should be pointer_missing")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            kwargs = {"audit_log": tmp / "audit.jsonl", "cache_db": tmp / "cache.sqlite3"}
            for key in list(os.environ):
                if key.startswith("MEMORYCORE_"):
                    del os.environ[key]
            os.environ["MEMORYCORE_JSONL_STORE"] = str(tmp / "jsonl-store.jsonl")
            os.environ["MEMORYCORE_CONFIG"] = str(tmp / "config.json")

            # Knowledge pointer remember routes to gbrain and flushes via ack.
            pointer_mem = call_tool(
                "memorycore_remember",
                {"memory_type": "knowledge", "content_ref": "gbrain://pages/synthetic-fixture-page"},
                **kwargs,
            )
            require(pointer_mem["results"][0]["pointer"]["backend_id"] == "gbrain", "knowledge should route to gbrain")
            flushed = call_tool("memorycore_flush", {}, **kwargs)
            require(flushed["results"][0]["flush_state"] == "flushed", "gbrain flush ack should mark flushed")

            # Fixture write-through synthesizes the capture receipt shape.
            secret = "synthetic knowledge: the trellis governs the alpha river."
            written = call_tool("memorycore_remember", {"memory_type": "knowledge", "content": secret}, **kwargs)
            require(written["write_mode"] == "fixture-only", "knowledge write must disclose fixture-only")
            item = written["results"][0]
            require(item["pointer"]["pointer_id"].startswith("gbrain://pages/memory-"), "knowledge pointer shape changed")
            require(item["flush_state"] == "flushed" and item["verification_state"] == "unknown",
                    "knowledge fixture write semantics changed")

            # Live-local degrades honestly instead of guessing CLI flags.
            os.environ["MEMORYCORE_BACKEND_MODE"] = "live-local"
            live = call_tool("memorycore_remember", {"memory_type": "knowledge", "content": secret}, **kwargs)
            require(live["status"] == "error" and live["error"]["category"] == "backend_unavailable",
                    "live knowledge write should degrade honestly")
            require("EN-035" in live["error"]["message"], "degradation should name the pending work")
            del os.environ["MEMORYCORE_BACKEND_MODE"]

            # Operator disable is honored for gbrain like every backend.
            from memorycore.viewer import handle_control
            handle_control("backend", {"backend_id": "gbrain", "enabled": False},
                           cache_db=kwargs["cache_db"], audit_log=kwargs["audit_log"],
                           config_path=Path(os.environ["MEMORYCORE_CONFIG"]))
            refused = call_tool("memorycore_remember", {"memory_type": "knowledge", "content": secret}, **kwargs)
            require(refused["error"]["code"] == "BACKEND_DISABLED", "disabled gbrain should refuse writes")

            # Content-sparse: knowledge content never persists in cache or audit.
            import sqlite3
            dump = json.dumps(sqlite3.connect(kwargs["cache_db"]).execute("SELECT * FROM cache_records").fetchall(), default=str)
            require(secret not in dump, "content leaked into cache DB")
            audit_text = kwargs["audit_log"].read_text(encoding="utf-8")
            require(secret not in audit_text, "content leaked into audit log")
            for line in audit_text.splitlines():
                assert_public_safe(json.loads(line))

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"MEMORYCORE_GBRAIN_ADAPTER_INVALID: {exc}", file=sys.stderr)
        return 1
    finally:
        os.environ.clear()
        os.environ.update(saved_env)

    print("MEMORYCORE_GBRAIN_ADAPTER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
