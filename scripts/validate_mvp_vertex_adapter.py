#!/usr/bin/env python3
"""Validate the EN-037 Vertex AI Memory Bank adapter contract.

Fixture-first and deterministic: normalizes Memory-Bank-shaped API output
(generateMemories, retrieveMemories, get) into the shared contract, proves
hash-at-observation verification (verified / stale-on-revision / missing),
and exercises the routed peer memory type end to end — the backend ships
installed but DISABLED (remote service), refuses writes honestly until the
operator enables it, write-throughs in fixture mode with a stable
resource-name pointer, degrades honestly in live-local until credentials
are wired, and reports an honest fanout lane. Content-sparse throughout.
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
from memorycore.mcp_surface import call_tool  # noqa: E402
from memorycore.vertex_adapter import (  # noqa: E402
    fact_hash,
    normalize_generate_result,
    normalize_retrieve_result,
    vertex_pointer,
    vertex_verify,
)
from memorycore.viewer import handle_control  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_fixture(name: str) -> dict:
    return json.loads((ROOT / "fixtures" / "vertex" / name).read_text(encoding="utf-8"))


def main() -> int:
    saved_env = dict(os.environ)
    request = {"request_id": "req_test_vertex", "operation": "cache_write"}
    try:
        # ---- normalization: generate ----
        out = normalize_generate_result(request, load_fixture("generate-result.json"))
        require(out["status"] == "ok" and out["selected_backend"] == "vertex_memory_bank", "generate normalize failed")
        require(len(out["results"]) == 2, "generate should normalize both memories")
        first = out["results"][0]
        require(first["pointer"]["pointer_id"].startswith("projects/"), "pointer must be the stable resource name")
        require(first["pointer"] == vertex_pointer(first["pointer"]["pointer_id"]), "pointer shape drifted")
        require(first["action"] == "CREATED" and out["results"][1]["action"] == "UPDATED",
                "consolidation actions must be preserved")
        require(first["source"] == "generated", "extraction source must be attributed")
        require(first["observed_hash"] == fact_hash(first["fact"]), "hash-at-observation must cover the fact")
        require(first["verification_state"] == "unknown", "generate must never overclaim verification")
        require(first["scope"] == {"user_id": "fixture-user"}, "user scope must survive normalization")

        empty = normalize_generate_result(request, load_fixture("generate-empty.json"))
        require(empty["status"] == "error" and empty["error"]["code"] == "VERTEX_GENERATE_EMPTY",
                "empty generate must error honestly")

        # ---- normalization: retrieve ----
        out = normalize_retrieve_result(request, load_fixture("retrieve-result.json"))
        require(out["status"] == "ok" and len(out["results"]) == 2, "retrieve normalize failed")
        require(out["results"][0]["distance"] == 0.12, "similarity distance must be preserved")
        require(out["results"][1]["source"] == "explicit", "explicit memories must be attributed as such")
        require(all(r["verification_state"] == "unknown" for r in out["results"]),
                "retrieve must never overclaim verification")

        # ---- verification: hash-at-observation against read-back ----
        observed = fact_hash(load_fixture("memory-result.json")["memory"]["fact"])
        verified = vertex_verify(request, load_fixture("memory-result.json"), expected_hash=observed)
        require(verified["verification_state"] == "verified", "unchanged fact should verify")

        stale = vertex_verify(request, load_fixture("memory-revised.json"), expected_hash=observed)
        require(stale["verification_state"] == "stale", "revised fact must be stale")
        require("consolidation" in stale["results"][0]["stale_reason"], "stale must name the revision cause")

        missing = vertex_verify(request, {"memory": {}}, expected_hash=observed)
        require(missing["status"] == "error" and missing["verification_state"] == "missing",
                "absent memory must be missing")
        existence = vertex_verify(request, load_fixture("memory-result.json"), expected_hash=None)
        require(existence["verification_state"] == "unknown", "read-back without a hash proves existence only")

        # ---- routed peer memory type through the cache surface ----
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cache_db = tmp / "cache.sqlite3"
            audit_log = tmp / "audit.jsonl"
            config_path = tmp / "config.json"
            kwargs = {"audit_log": audit_log, "cache_db": cache_db}
            ctl = {"cache_db": cache_db, "audit_log": audit_log, "config_path": config_path}

            for key in list(os.environ):
                if key.startswith("MEMORYCORE_"):
                    del os.environ[key]
            os.environ["MEMORYCORE_JSONL_STORE"] = str(tmp / "jsonl-store.jsonl")
            os.environ["MEMORYCORE_CONFIG"] = str(config_path)

            secret = "peer fact: the operator drinks their coffee before standup."

            # Remote backend ships disabled: writes are refused honestly.
            refused = call_tool("memorycore_remember", {"memory_type": "peer", "content": secret}, **kwargs)
            require(refused["status"] == "error" and refused["error"]["code"] == "BACKEND_DISABLED",
                    "vertex must ship disabled and refuse writes")

            # Operator enables it: fixture write-through with a resource-name pointer.
            require(handle_control("backend", {"backend_id": "vertex_memory_bank", "enabled": True}, **ctl)["status"] == "ok",
                    "enable control failed")
            written = call_tool("memorycore_remember", {"memory_type": "peer", "content": secret}, **kwargs)
            require(written["status"] == "ok" and written["write_mode"] == "fixture-only",
                    "enabled fixture write-through failed")
            item = written["results"][0]
            require(item["backend_id"] == "vertex_memory_bank", "peer write must route to vertex")
            require(item["pointer"]["pointer_id"].startswith("projects/fixture-project/"),
                    "fixture pointer must be resource-name shaped")
            require(item["flush_state"] == "flushed" and item["verification_state"] == "unknown",
                    "write-through must land flushed, unproven")

            # Pointer remember routes and flushes through the peer lane.
            pointer_name = "projects/fixture-project/locations/us-central1/reasoningEngines/fixture/memories/mem-pointer"
            pending = call_tool("memorycore_remember", {"memory_type": "peer", "content_ref": pointer_name}, **kwargs)
            require(pending["results"][0]["flush_state"] == "pending", "pointer remember should be pending")
            flushed = call_tool("memorycore_flush", {}, **kwargs)
            states = {r["record_id"]: r["flush_state"] for r in flushed["results"]}
            require(states.get(pending["results"][0]["record_id"]) == "flushed", "peer flush ack failed")

            # Live-local degrades honestly until GCP credentials are wired.
            os.environ["MEMORYCORE_BACKEND_MODE"] = "live-local"
            live = call_tool("memorycore_remember", {"memory_type": "peer", "content": secret}, **kwargs)
            require(live["status"] == "error" and live["error"]["code"] == "BACKEND_UNAVAILABLE",
                    "live-local must degrade honestly without credentials")
            require("credentials" in live["error"]["message"], "live refusal must name the missing credentials")
            del os.environ["MEMORYCORE_BACKEND_MODE"]

            # Fanout reports an honest vertex lane in both enabled and disabled states.
            fan = call_tool("memorycore_fanout_search", {"query": "peer"}, **kwargs)
            lanes = {lane["lane"]: lane for lane in fan["lanes"]}
            require(lanes["vertex_memory_bank_search"]["status"] == "unavailable",
                    "enabled vertex lane must say unavailable, not vanish")
            require("credentials" in lanes["vertex_memory_bank_search"]["reason"], "lane reason must name credentials")
            handle_control("backend", {"backend_id": "vertex_memory_bank", "enabled": False}, **ctl)
            fan = call_tool("memorycore_fanout_search", {"query": "peer"}, **kwargs)
            lanes = {lane["lane"]: lane for lane in fan["lanes"]}
            require(lanes["vertex_memory_bank_search"]["status"] == "disabled",
                    "disabled vertex lane must be labeled disabled")

            # Content-sparse: the fact rode the call only; receipts hold pointers and hashes.
            require(secret not in cache_db.read_bytes().decode("utf-8", errors="ignore"),
                    "content leaked into the cache")
            require(secret not in audit_log.read_text(encoding="utf-8"), "content leaked into the audit log")
            require(secret not in config_path.read_text(encoding="utf-8"), "content leaked into config")
            for line in audit_log.read_text(encoding="utf-8").splitlines():
                assert_public_safe(json.loads(line))

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"MEMORYCORE_VERTEX_ADAPTER_INVALID: {exc}", file=sys.stderr)
        return 1
    finally:
        os.environ.clear()
        os.environ.update(saved_env)

    print("MEMORYCORE_VERTEX_ADAPTER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
