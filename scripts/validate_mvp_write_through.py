#!/usr/bin/env python3
"""Validate ADR-0005 transient content write-through against a stub QMD.

The stub qmd binary's multi-get actually reads the materialized file from
disk, so the verified stamp is earned by a real read-back, not asserted.
Deterministic and public-safe: no real QMD, no private index, no OpenClaw.
"""

from __future__ import annotations

import json
import os
import sqlite3
import stat
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.audit_log import assert_public_safe  # noqa: E402
from memorycore.mcp_surface import call_tool  # noqa: E402


STUB_QMD = """#!/usr/bin/env python3
import json, pathlib, sys
args = sys.argv[1:]
if "update" in args:
    print("reindexed")
elif "multi-get" in args:
    import os
    raw = args[args.index("multi-get") + 1]
    if raw.startswith("qmd://"):
        name = raw.split("/")[-1]
        raw = os.path.join(os.environ.get("MEMORYCORE_CORPUS_DIR", "."), name)
    target = pathlib.Path(raw)
    if not target.exists():
        print("No files matched pattern: " + raw)
        raise SystemExit(0)
    print(json.dumps([{"file": str(target), "content": target.read_text()}]))
else:
    print("stub qmd ok")
"""

SECRET_CONTENT = "synthetic-write-through-memory: the alpha river decision was ratified."


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    saved_env = dict(os.environ)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            stub_bin = tmp / "qmd-stub"
            stub_bin.write_text(STUB_QMD, encoding="utf-8")
            stub_bin.chmod(stub_bin.stat().st_mode | stat.S_IXUSR)
            corpus = tmp / "corpus"
            cache_db = tmp / "cache.sqlite3"
            audit_log = tmp / "audit.jsonl"
            kwargs = {"audit_log": audit_log, "cache_db": cache_db}

            for key in list(os.environ):
                if key.startswith("MEMORYCORE_"):
                    del os.environ[key]

            # Fixture mode: no disk, no subprocess, synthesized pointer, disclosed.
            fixture = call_tool(
                "memorycore_remember",
                {"memory_type": "file_corpus", "content": SECRET_CONTENT},
                **kwargs,
            )
            require(fixture["status"] == "ok", "fixture write-through should succeed")
            require(fixture["write_mode"] == "fixture-only", "fixture write must disclose its mode")
            require(fixture["results"][0]["flush_state"] == "flushed", "write-through should not stay pending")
            require(not corpus.exists(), "fixture mode must not touch disk")

            # Live-local mode: file materialized, indexed, read back, verified.
            os.environ.update(
                {
                    "MEMORYCORE_BACKEND_MODE": "live-local",
                    "MEMORYCORE_QMD_BIN": str(stub_bin),
                    "MEMORYCORE_QMD_COLLECTION": "stub-collection",
                    "MEMORYCORE_QMD_WRITE_COLLECTION": "memorycore-writes",
                    "MEMORYCORE_CORPUS_DIR": str(corpus),
                }
            )
            live = call_tool(
                "memorycore_remember",
                {"memory_type": "file_corpus", "content": SECRET_CONTENT, "client": "openclaw"},
                **kwargs,
            )
            require(live["status"] == "ok", "live write-through should succeed")
            require(live["write_mode"] == "live-local", "live write must disclose its mode")
            item = live["results"][0]
            require(item["verification_state"] == "verified", "read-back should earn verified")
            require(item["pointer"]["pointer_id"].startswith("qmd://memorycore-writes/memory-"), "write pointer shape changed")

            files = list(corpus.glob("memory-*.md"))
            require(len(files) == 1, "exactly one memory file should be materialized")
            body = files[0].read_text(encoding="utf-8")
            require(body.startswith("---"), "memory file should carry frontmatter")
            require("memorycore: true" in body, "frontmatter should mark memorycore authorship")
            require("client_surface: openclaw" in body, "frontmatter should carry client surface")
            require(SECRET_CONTENT in body, "memory file should contain the content")

            # Round trip: the cached pointer recalls the flushed record.
            recalled = call_tool("memorycore_recall", {"record_id": item["record_id"]}, **kwargs)
            require(recalled["results"][0]["flush_state"] == "flushed", "recalled record should be flushed")

            # Transcript content is rejected until the LCM transport exists.
            transcript = call_tool(
                "memorycore_remember",
                {"memory_type": "transcript", "content": SECRET_CONTENT},
                **kwargs,
            )
            require(transcript["status"] == "error", "transcript write-through should fail")
            require(transcript["error"]["category"] == "backend_unavailable", "transcript failure category changed")

            # Remember with neither content nor content_ref is rejected.
            try:
                call_tool("memorycore_remember", {"memory_type": "file_corpus"}, **kwargs)
                raise ValueError("remember accepted a call without content or content_ref")
            except ValueError as exc:
                require("content_ref or content" in str(exc), "remember one-of requirement changed")

            # Transient contract: content never lands in cache DB or audit log.
            cache_dump = json.dumps(
                sqlite3.connect(cache_db).execute("SELECT * FROM cache_records").fetchall(), default=str
            )
            require(SECRET_CONTENT not in cache_dump, "content leaked into the cache DB")
            audit_text = audit_log.read_text(encoding="utf-8")
            require(SECRET_CONTENT not in audit_text, "content leaked into the audit log")
            for line in audit_text.splitlines():
                assert_public_safe(json.loads(line))

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"MEMORYCORE_WRITE_THROUGH_INVALID: {exc}", file=sys.stderr)
        return 1
    finally:
        os.environ.clear()
        os.environ.update(saved_env)

    print("MEMORYCORE_WRITE_THROUGH_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
