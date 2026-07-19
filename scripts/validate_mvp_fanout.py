#!/usr/bin/env python3
"""Validate EN-021 attributed multi-backend recall (the fan-out merge contract).

Proves the contract's spine: every lane reports honestly (ok with counts
and latency, or skipped/disabled/unavailable with a reason — never silently
missing), every merged item carries backend attribution and verification
state, and the same memory found by two lanes collapses into one entry
listing its corroborating lanes. Runs fixture mode and a live-local pass
against a stub qmd binary. Deterministic and public-safe.
"""

from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.audit_log import assert_public_safe  # noqa: E402
from memorycore.mcp_surface import call_tool  # noqa: E402
from memorycore.viewer import handle_control  # noqa: E402


STUB_QMD = """#!/usr/bin/env python3
import json, sys
args = sys.argv[1:]
if "search" in args:
    print(json.dumps([{"file": "qmd://stub/alpha-fixture.md", "snippet": "stub corroborating hit", "score": 0.9}]))
else:
    print("stub ok")
"""

SECRET = "fanout target memory: the synthesizer merges every lane with receipts."


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def lanes_by_id(result):
    return {lane["lane"]: lane for lane in result["lanes"]}


def main() -> int:
    saved_env = dict(os.environ)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            kwargs = {"audit_log": tmp / "audit.jsonl", "cache_db": tmp / "cache.sqlite3"}
            ctl = {"cache_db": kwargs["cache_db"], "audit_log": kwargs["audit_log"],
                   "config_path": tmp / "config.json"}
            for key in list(os.environ):
                if key.startswith("MEMORYCORE_"):
                    del os.environ[key]
            os.environ["MEMORYCORE_JSONL_STORE"] = str(tmp / "jsonl-store.jsonl")
            os.environ["MEMORYCORE_CONFIG"] = str(tmp / "config.json")

            call_tool("memorycore_remember", {"memory_type": "local", "content": SECRET}, **kwargs)
            call_tool("memorycore_remember",
                      {"memory_type": "file_corpus", "content_ref": "qmd://stub/alpha-fixture.md"}, **kwargs)

            # ---- fixture mode ----
            out = call_tool("memorycore_fanout_search", {"query": "fanout target"}, **kwargs)
            require(out["status"] == "ok" and out["merge_contract_version"] == 1, "contract header missing")
            lanes = lanes_by_id(out)
            require(lanes["cache"]["status"] == "ok" and "latency_ms" in lanes["cache"], "cache lane malformed")
            require(lanes["jsonl_content"]["status"] == "ok", "jsonl lane should run")
            require(lanes["qmd_index"]["status"] == "skipped" and "fixture" in lanes["qmd_index"]["reason"],
                    "qmd lane must say why it did not run")
            require(lanes["lossless_claw_search"]["status"] == "unavailable", "lcm lane must be honest")
            require(lanes["gbrain_search"]["status"] == "unavailable", "gbrain lane must be honest")
            hit = next(r for r in out["results"] if r.get("snippet"))
            require(hit["backend_id"] == "jsonl_store" and hit["corroborated_by"] == ["jsonl_content"],
                    "content hit attribution wrong")
            require(hit["record_id"] and hit["verification_state"] == "verified", "content hit should link and verify")

            # Disabled backend: the lane says so instead of vanishing.
            handle_control("backend", {"backend_id": "jsonl_store", "enabled": False}, **ctl)
            out = call_tool("memorycore_fanout_search", {"query": "fanout target"}, **kwargs)
            require(lanes_by_id(out)["jsonl_content"]["status"] == "disabled", "disabled lane must be labeled")
            handle_control("backend", {"backend_id": "jsonl_store", "enabled": True}, **ctl)

            # ---- live-local with stub qmd: corroboration across lanes ----
            stub = tmp / "qmd-stub"
            stub.write_text(STUB_QMD, encoding="utf-8")
            stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
            os.environ.update({
                "MEMORYCORE_BACKEND_MODE": "live-local",
                "MEMORYCORE_QMD_BIN": str(stub),
                "MEMORYCORE_QMD_COLLECTION": "stub-collection",
            })
            out = call_tool("memorycore_fanout_search", {"query": "alpha-fixture"}, **kwargs)
            lanes = lanes_by_id(out)
            require(lanes["qmd_index"]["status"] == "ok" and lanes["qmd_index"]["count"] == 1,
                    "live qmd lane should run against the stub")
            top = out["results"][0]
            require(top["identity_key"] == "qmd://stub/alpha-fixture.md", "corroborated item should rank first")
            require(sorted(top["corroborated_by"]) == ["cache", "qmd_index"],
                    f"expected two-lane corroboration, got {top['corroborated_by']}")
            require(top.get("record_id"), "corroborated item should keep its cache record linkage")
            for key in ("MEMORYCORE_BACKEND_MODE", "MEMORYCORE_QMD_BIN", "MEMORYCORE_QMD_COLLECTION"):
                del os.environ[key]

            # Receipts: fanout calls are audited, content-sparse.
            audit_lines = [json.loads(line) for line in kwargs["audit_log"].read_text(encoding="utf-8").splitlines()]
            fan_receipts = [r for r in audit_lines if r["operation"] == "fanout_search"]
            require(len(fan_receipts) == 3, "each fanout call should leave a receipt")
            require(SECRET not in kwargs["audit_log"].read_text(encoding="utf-8"), "content leaked into audit")
            for record in audit_lines:
                assert_public_safe(record)

    except (json.JSONDecodeError, KeyError, StopIteration, ValueError) as exc:
        print(f"MEMORYCORE_FANOUT_INVALID: {exc}", file=sys.stderr)
        return 1
    finally:
        os.environ.clear()
        os.environ.update(saved_env)

    print("MEMORYCORE_FANOUT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
