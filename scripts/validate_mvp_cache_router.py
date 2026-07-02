#!/usr/bin/env python3
"""Validate the caching memory router against deterministic in-memory backends.

This check writes only a temporary SQLite cache with public-safe synthetic
pointers. It does not call QMD, lossless-claw, Burrow, OpenClaw, or any live
runtime; flush targets are injected callables.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memorycore.cache_router import (  # noqa: E402
    CacheStore,
    cache_read,
    cache_search,
    cache_write,
    flush_pending,
)


TIMESTAMP = "2026-07-02T18:00:00Z"
LATER = "2026-07-02T18:05:00Z"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CacheStore(Path(tmpdir) / "cache.sqlite3")

            # Write path: records land pending, stamped, routed by type.
            file_record = cache_write(
                store,
                {
                    "memory_type": "file_corpus",
                    "content_ref": "fixtures/corpus/project-alpha.md",
                    "source_pointer": {"backend_id": "qmd", "pointer_id": "fixtures/corpus/project-alpha.md"},
                },
                timestamp=TIMESTAMP,
            )
            require(file_record["record_id"].startswith("cache_"), "Cache record id prefix changed")
            require(file_record["flush_state"] == "pending", "New cache records should be pending")
            require(file_record["verification"] == "unknown", "Unverified writes must stay unknown")

            transcript_record = cache_write(
                store,
                {
                    "memory_type": "transcript",
                    "content_ref": "sum_public_fixture_001",
                    "source_pointer": {"backend_id": "lossless_claw", "summary_id": "sum_public_fixture_001"},
                    "verification": "verified",
                },
                timestamp=TIMESTAMP,
            )
            require(transcript_record["verification"] == "verified", "Explicit verification state dropped")

            # Determinism: same entry, same timestamp -> same record id.
            replay = cache_write(
                store,
                {
                    "memory_type": "file_corpus",
                    "content_ref": "fixtures/corpus/project-alpha.md",
                    "source_pointer": {"backend_id": "qmd", "pointer_id": "fixtures/corpus/project-alpha.md"},
                },
                timestamp=TIMESTAMP,
            )
            require(replay["record_id"] == file_record["record_id"], "Cache record ids must be deterministic")

            # Content-sparse contract: forbidden fields are rejected.
            try:
                cache_write(
                    store,
                    {
                        "memory_type": "file_corpus",
                        "content_ref": "fixtures/corpus/project-alpha.md",
                        "snippet": "private text that must not be cached",
                    },
                    timestamp=TIMESTAMP,
                )
                raise ValueError("Forbidden content field was accepted by the cache")
            except ValueError as exc:
                require("forbidden" in str(exc), "Forbidden-field rejection message changed")

            # Unroutable memory types are rejected at write time.
            try:
                cache_write(
                    store,
                    {"memory_type": "peer", "content_ref": "peer_fixture_001"},
                    timestamp=TIMESTAMP,
                )
                raise ValueError("Unroutable memory type was accepted by the cache")
            except ValueError as exc:
                require("unroutable" in str(exc), "Unroutable-type rejection message changed")

            # Read path: hit by id and by pointer.
            hit = cache_read(store, record_id=file_record["record_id"])
            require(hit is not None and hit["content_ref"] == "fixtures/corpus/project-alpha.md", "Cache hit by id failed")
            pointer_hit = cache_read(store, pointer_id="fixtures/corpus/project-alpha.md")
            require(pointer_hit is not None and pointer_hit["record_id"] == file_record["record_id"], "Cache hit by pointer failed")

            # Read path: miss without fallback returns None.
            require(cache_read(store, record_id="cache_missing") is None, "Cache miss should return None")

            # Read path: miss with fallback re-caches the fetched record.
            fetched = cache_read(
                store,
                record_id="cache_not_there",
                fallback=lambda: {
                    "memory_type": "file_corpus",
                    "content_ref": "fixtures/corpus/project-beta.md",
                    "source_pointer": {"backend_id": "qmd", "pointer_id": "fixtures/corpus/project-beta.md"},
                },
                timestamp=LATER,
            )
            require(fetched is not None and fetched["flush_state"] == "pending", "Fallback fetch was not re-cached")
            require(store.find_by_pointer("fixtures/corpus/project-beta.md") is not None, "Re-cached record not findable")

            # Search: cached records only, filterable by memory type.
            found = cache_search(store, "project-alpha")
            require(len(found) == 1, "Search should match the alpha record once")
            require(cache_search(store, "fixture", memory_type="transcript")[0]["memory_type"] == "transcript", "Type filter failed")
            require(cache_search(store, "no-such-token") == [], "Search should return no false positives")

            # Flush: routed targets succeed and fail independently.
            backends: dict[str, Any] = {
                "qmd": lambda record: {"status": "ok"},
            }
            flushed = flush_pending(store, backends, timestamp=LATER)
            by_id = {record["record_id"]: record for record in flushed}
            require(by_id[file_record["record_id"]]["flush_state"] == "flushed", "QMD-routed record should flush")
            require(
                by_id[transcript_record["record_id"]]["flush_state"] == "failed",
                "Transcript record should fail without an LCM handler",
            )
            require(
                by_id[transcript_record["record_id"]]["verification"] == "unknown",
                "Failed flush must downgrade verification conservatively",
            )

            # Mirroring: one record routed to two backends becomes mirrored.
            mirror_routing = {"file_corpus": ("qmd", "mock_healthy")}
            mirrored_record = cache_write(
                store,
                {
                    "memory_type": "file_corpus",
                    "content_ref": "fixtures/corpus/project-gamma.md",
                    "source_pointer": {"backend_id": "qmd", "pointer_id": "fixtures/corpus/project-gamma.md"},
                },
                timestamp=LATER,
                routing=mirror_routing,
            )
            mirror_backends = {
                "qmd": lambda record: {"status": "ok"},
                "mock_healthy": lambda record: {"status": "ok"},
            }
            mirrored = flush_pending(store, mirror_backends, timestamp=LATER, routing=mirror_routing)
            mirrored_by_id = {record["record_id"]: record for record in mirrored}
            require(
                mirrored_by_id[mirrored_record["record_id"]]["flush_state"] == "mirrored",
                "Multi-target flush should be marked mirrored",
            )

            # Failed records are not retried by a later flush pass (no pending left).
            require(flush_pending(store, backends, timestamp=LATER) == [], "Flush should only touch pending records")

            store.close()

    except (KeyError, ValueError) as exc:
        print(f"MEMORYCORE_CACHE_ROUTER_INVALID: {exc}", file=sys.stderr)
        return 1

    print("MEMORYCORE_CACHE_ROUTER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
