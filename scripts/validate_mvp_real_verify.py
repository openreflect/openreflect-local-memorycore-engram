#!/usr/bin/env python3
"""Validate EN-018 backend-proof verification against a lagging stub index.

The stub qmd keeps an index snapshot directory that only syncs on `update`,
faithfully reproducing the index-lag behavior observed on the real QMD
2026-07-04: deleted files still served, modified files served stale.
Deterministic and public-safe.
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

from memorycore.mcp_surface import call_tool  # noqa: E402


STUB_QMD = """#!/usr/bin/env python3
import json, os, pathlib, shutil, sys
args = sys.argv[1:]
corpus = pathlib.Path(os.environ["MEMORYCORE_CORPUS_DIR"])
index = pathlib.Path(os.environ["STUB_INDEX_DIR"])
if "update" in args:
    index.mkdir(parents=True, exist_ok=True)
    for old in index.glob("*.md"):
        old.unlink()
    for f in corpus.glob("*.md"):
        shutil.copy(f, index / f.name)
    print("reindexed")
elif "multi-get" in args:
    raw = args[args.index("multi-get") + 1]
    name = raw.split("/")[-1] if raw.startswith("qmd://") else pathlib.Path(raw).name
    target = index / name
    if not target.exists():
        print("No files matched pattern: " + raw)
        raise SystemExit(0)
    print(json.dumps([{"file": name, "body": target.read_text()}]))
else:
    print("stub qmd ok")
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def recall_state(record_id: str, kwargs: dict) -> str:
    return call_tool("memorycore_recall", {"record_id": record_id}, **kwargs)["results"][0]["verification_state"]


def main() -> int:
    saved_env = dict(os.environ)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            stub_bin = tmp / "qmd-stub"
            stub_bin.write_text(STUB_QMD, encoding="utf-8")
            stub_bin.chmod(stub_bin.stat().st_mode | stat.S_IXUSR)
            corpus = tmp / "corpus"
            kwargs = {"audit_log": tmp / "audit.jsonl", "cache_db": tmp / "cache.sqlite3"}

            for key in list(os.environ):
                if key.startswith("MEMORYCORE_"):
                    del os.environ[key]
            os.environ.update(
                {
                    "MEMORYCORE_BACKEND_MODE": "live-local",
                    "MEMORYCORE_QMD_BIN": str(stub_bin),
                    "MEMORYCORE_QMD_COLLECTION": "stub-collection",
                    "MEMORYCORE_CORPUS_DIR": str(corpus),
                    "STUB_INDEX_DIR": str(tmp / "index"),
                }
            )

            # Write a memory; write-through stores its content hash.
            written = call_tool(
                "memorycore_remember",
                {"memory_type": "file_corpus", "content": "verification target: the alpha river decision."},
                **kwargs,
            )
            record_id = written["results"][0]["record_id"]
            require(written["results"][0]["verification_state"] == "verified", "write-through should verify")

            # Healthy record: disk and index agree, hash matches -> verified.
            verified = call_tool("memorycore_verify", {"record_id": record_id}, **kwargs)
            require(verified["verification_state"] == "verified", "healthy record should verify")
            require(verified["results"][0]["record_id"] == record_id, "verify result should carry record_id")

            # Backend gone while source intact -> unknown, never a guess.
            os.environ["MEMORYCORE_QMD_BIN"] = str(tmp / "no-such-qmd")
            require(
                call_tool("memorycore_verify", {"record_id": record_id}, **kwargs)["verification_state"] == "unknown",
                "unavailable backend should verify unknown",
            )
            os.environ["MEMORYCORE_QMD_BIN"] = str(stub_bin)

            # Tamper with disk, index snapshot still has the old body -> stale.
            memory_file = next(corpus.glob("memory-*.md"))
            memory_file.write_text(memory_file.read_text(encoding="utf-8") + "\ntampered line\n", encoding="utf-8")
            stale = call_tool("memorycore_verify", {"record_id": record_id}, **kwargs)
            require(stale["verification_state"] == "stale", "modified disk should be stale")
            require(recall_state(record_id, kwargs) == "stale", "stale verdict should update the cached stamp")

            # Delete from disk; the lagging index STILL serves it -> missing anyway.
            memory_file.unlink()
            missing = call_tool("memorycore_verify", {"record_id": record_id}, **kwargs)
            require(missing["verification_state"] == "missing", "deleted source must be missing despite index lag")
            require(recall_state(record_id, kwargs) == "missing", "missing verdict should update the cached stamp")

            # Unknown record id -> CACHE_MISS.
            miss = call_tool("memorycore_verify", {"record_id": "cache_nonexistent"}, **kwargs)
            require(miss["error"]["code"] == "CACHE_MISS", "unknown record should be a cache miss")

            # Fixture mode cannot prove anything -> unsupported, stamp untouched.
            os.environ["MEMORYCORE_BACKEND_MODE"] = "fixture"
            unsupported = call_tool("memorycore_verify", {"record_id": record_id}, **kwargs)
            require(unsupported["verification_state"] == "unsupported", "fixture mode should be unsupported")
            os.environ["MEMORYCORE_BACKEND_MODE"] = "live-local"
            require(recall_state(record_id, kwargs) == "missing", "unsupported must not overwrite the stamp")

            # Id-less verify is rejected.
            try:
                call_tool("memorycore_verify", {}, **kwargs)
                raise ValueError("verify accepted a call without any id")
            except ValueError as exc:
                require("pointer_id or record_id" in str(exc), "verify one-of requirement changed")

    except (json.JSONDecodeError, KeyError, StopIteration, ValueError) as exc:
        print(f"MEMORYCORE_REAL_VERIFY_INVALID: {exc}", file=sys.stderr)
        return 1
    finally:
        os.environ.clear()
        os.environ.update(saved_env)

    print("MEMORYCORE_REAL_VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
