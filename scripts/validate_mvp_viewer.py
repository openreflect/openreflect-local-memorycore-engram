#!/usr/bin/env python3
"""Validate the EN-024 local provenance viewer against synthetic stores.

Builds a temp cache and audit log via the MCP surface, generates the viewer,
and asserts the receipt surface renders records, verification badges, backend
attribution, and audit ids — while staying content-sparse (memory content
never enters the HTML). Deterministic and public-safe.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.mcp_surface import call_tool  # noqa: E402
from memorycore.viewer import collect_viewer_data, write_viewer  # noqa: E402


SECRET_CONTENT = "synthetic viewer secret: the alpha river ledger was ratified."


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    saved_env = dict(os.environ)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cache_db = tmp / "cache.sqlite3"
            audit_log = tmp / "audit.jsonl"
            kwargs = {"audit_log": audit_log, "cache_db": cache_db}

            for key in list(os.environ):
                if key.startswith("MEMORYCORE_"):
                    del os.environ[key]
            os.environ["MEMORYCORE_JSONL_STORE"] = str(tmp / "jsonl-store.jsonl")
            os.environ["MEMORYCORE_CONFIG"] = str(tmp / "config.json")

            # Seed: one local content memory (verified), one pointer memory.
            written = call_tool("memorycore_remember", {"memory_type": "local", "content": SECRET_CONTENT}, **kwargs)
            record_id = written["results"][0]["record_id"]
            call_tool(
                "memorycore_remember",
                {"memory_type": "file_corpus", "content_ref": "fixtures/corpus/project-alpha.md"},
                **kwargs,
            )
            call_tool("memorycore_verify", {"record_id": record_id}, **kwargs)

            data = collect_viewer_data(cache_db, audit_log)
            require(len(data["records"]) == 2, "viewer should collect both records")
            require(data["verification_counts"]["verified"] == 1, "verified count changed")
            require(data["backend_counts"].get("jsonl_store") == 1, "backend attribution changed")

            output = write_viewer(cache_db, audit_log, tmp / "viewer.html")
            html = output.read_text(encoding="utf-8")

            require("Engram — Memory Receipts" in html, "viewer title missing")
            require(record_id in html, "record id missing from viewer data")
            require("jsonl_store" in html and "qmd" in html, "backend attribution missing")
            require('"verified"' in html or "verified" in html, "verification states missing")
            require("audit_" in html, "audit ids missing")
            require("data-theme" in html and "prefers-color-scheme" in html, "theme support missing")
            require("__ENGRAM_DATA__" not in html, "data placeholder not substituted")
            for element_id in ("mf-text", "af-op", "trend-mem", "cfghistory", "declare", "controlplane"):
                require(f'id="{element_id}"' in html, f"console element missing: {element_id}")
            require("revealpane" in html and "exportPack" in html, "reveal/pack surface missing")
            require("data-help" in html and "bindHelp" in html, "help tooltip layer missing")
            require("Quick Markdown Search" in html, "backend descriptions missing from data")
            require("npmjs.com/package/@tobilu/qmd" in html, "backend docs url missing")
            require("Conversation moments" in html, "memory type descriptions missing")

            # Content-sparse: memory content never enters the receipt surface.
            require(SECRET_CONTENT not in html, "memory content leaked into the viewer")
            require("alpha river ledger" not in html, "memory content fragment leaked into the viewer")

            # Empty stores render an honest empty state, not an error.
            empty = write_viewer(tmp / "no-cache.sqlite3", tmp / "no-audit.jsonl", tmp / "empty.html")
            require("Engram — Memory Receipts" in empty.read_text(encoding="utf-8"), "empty-store viewer failed")

    except (KeyError, ValueError) as exc:
        print(f"MEMORYCORE_VIEWER_INVALID: {exc}", file=sys.stderr)
        return 1
    finally:
        os.environ.clear()
        os.environ.update(saved_env)

    print("MEMORYCORE_VIEWER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
