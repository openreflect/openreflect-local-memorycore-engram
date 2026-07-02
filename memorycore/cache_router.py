"""Caching memory router for the MemoryCore MVP.

Implements docs/CACHING_MEMORY_ROUTER.md: a local content-sparse cache in
front of typed backends, with read / write / search verbs and
flush-by-memory-type policies. The cache stamps every record with a
provenance pointer and verification state on entry.

This module is fixture-first. It does not import or call QMD,
Lossless-Claw, Burrow, OpenClaw, or any live backend; flush targets are
injected callables so validation stays deterministic.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Callable

from memorycore.provenance_ledger import POINTER_FIELDS
from memorycore.verification_state import normalize_verification_state, state_from_error


DEFAULT_ROUTING: dict[str, tuple[str, ...]] = {
    "file_corpus": ("qmd",),
    "transcript": ("lossless_claw",),
}

FLUSH_STATES = frozenset({"pending", "flushed", "failed", "mirrored"})

FORBIDDEN_FIELDS = ("snippet", "content", "citations", "summary", "answer", "text")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cache_records (
    record_id TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL,
    content_ref TEXT NOT NULL,
    source_pointer TEXT NOT NULL,
    verification TEXT NOT NULL,
    flush_state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

_COLUMNS = (
    "record_id",
    "memory_type",
    "content_ref",
    "source_pointer",
    "verification",
    "flush_state",
    "created_at",
    "updated_at",
)


class CacheStore:
    """SQLite-backed cache with the single table from the design note."""

    def __init__(self, path: Path | str) -> None:
        self._conn = sqlite3.connect(str(path))
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def get(self, record_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            f"SELECT {', '.join(_COLUMNS)} FROM cache_records WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        return _row_to_record(row) if row else None

    def find_by_pointer(self, pointer_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            f"SELECT {', '.join(_COLUMNS)} FROM cache_records"
            " WHERE json_extract(source_pointer, '$.pointer_id') = ?",
            (pointer_id,),
        ).fetchone()
        return _row_to_record(row) if row else None

    def pending(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            f"SELECT {', '.join(_COLUMNS)} FROM cache_records WHERE flush_state = 'pending'"
            " ORDER BY created_at, record_id"
        ).fetchall()
        return [_row_to_record(row) for row in rows]

    def search(self, query: str, memory_type: str | None = None) -> list[dict[str, Any]]:
        pattern = f"%{query}%"
        sql = (
            f"SELECT {', '.join(_COLUMNS)} FROM cache_records"
            " WHERE (content_ref LIKE ? OR source_pointer LIKE ?)"
        )
        params: list[Any] = [pattern, pattern]
        if memory_type is not None:
            sql += " AND memory_type = ?"
            params.append(memory_type)
        sql += " ORDER BY created_at, record_id"
        rows = self._conn.execute(sql, params).fetchall()
        return [_row_to_record(row) for row in rows]

    def upsert(self, record: dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO cache_records"
            f" ({', '.join(_COLUMNS)}) VALUES ({', '.join('?' for _ in _COLUMNS)})",
            (
                record["record_id"],
                record["memory_type"],
                record["content_ref"],
                json.dumps(record["source_pointer"], sort_keys=True, separators=(",", ":")),
                record["verification"],
                record["flush_state"],
                record["created_at"],
                record["updated_at"],
            ),
        )
        self._conn.commit()


def cache_write(
    store: CacheStore,
    entry: dict[str, Any],
    *,
    timestamp: str,
    routing: dict[str, tuple[str, ...]] | None = None,
) -> dict[str, Any]:
    """Land a record in the cache: stamp pointer, verification, flush state."""
    routing = DEFAULT_ROUTING if routing is None else routing

    forbidden = [field for field in FORBIDDEN_FIELDS if field in entry]
    if forbidden:
        raise ValueError(f"cache entry contains forbidden content fields: {forbidden}")

    memory_type = entry.get("memory_type")
    if memory_type not in routing:
        raise ValueError(f"unroutable memory_type: {memory_type!r}")

    content_ref = entry.get("content_ref")
    if not content_ref:
        raise ValueError("cache entry requires a content_ref pointer")

    pointer = {field: entry["source_pointer"][field] for field in POINTER_FIELDS if entry.get("source_pointer", {}).get(field)}

    record = {
        "memory_type": memory_type,
        "content_ref": content_ref,
        "source_pointer": pointer,
        "verification": normalize_verification_state(entry.get("verification")),
        "flush_state": "pending",
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    record["record_id"] = _record_id(record)
    store.upsert(record)
    return record


def cache_read(
    store: CacheStore,
    *,
    record_id: str | None = None,
    pointer_id: str | None = None,
    fallback: Callable[[], dict[str, Any]] | None = None,
    timestamp: str | None = None,
    routing: dict[str, tuple[str, ...]] | None = None,
) -> dict[str, Any] | None:
    """Cache hit returns the stored record; miss falls through and re-caches."""
    hit: dict[str, Any] | None = None
    if record_id is not None:
        hit = store.get(record_id)
    elif pointer_id is not None:
        hit = store.find_by_pointer(pointer_id)
    else:
        raise ValueError("cache_read requires record_id or pointer_id")

    if hit is not None:
        return hit
    if fallback is None:
        return None
    if timestamp is None:
        raise ValueError("fallback re-cache requires a timestamp")

    fetched = fallback()
    if fetched is None:
        return None
    return cache_write(store, fetched, timestamp=timestamp, routing=routing)


def cache_search(
    store: CacheStore,
    query: str,
    *,
    memory_type: str | None = None,
) -> list[dict[str, Any]]:
    """Search cached records only, per the design note's MVP boundary."""
    return store.search(query, memory_type=memory_type)


def flush_pending(
    store: CacheStore,
    backends: dict[str, Callable[[dict[str, Any]], dict[str, Any]]],
    *,
    timestamp: str,
    routing: dict[str, tuple[str, ...]] | None = None,
) -> list[dict[str, Any]]:
    """Flush pending records to their routed backends.

    All targets succeed -> flushed (mirrored when routed to more than one).
    Any target fails -> failed, verification downgraded from the error.
    """
    routing = DEFAULT_ROUTING if routing is None else routing
    updated = []
    for record in store.pending():
        targets = routing.get(record["memory_type"], ())
        outcomes = []
        for backend_id in targets:
            handler = backends.get(backend_id)
            if handler is None:
                outcomes.append(
                    {
                        "status": "error",
                        "error": {
                            "code": "BACKEND_UNAVAILABLE",
                            "category": "backend_unavailable",
                            "message": "No flush handler registered for backend.",
                        },
                    }
                )
            else:
                outcomes.append(handler(record))

        failures = [item for item in outcomes if item.get("status") != "ok"]
        if not targets:
            record["flush_state"] = "failed"
            record["verification"] = "unknown"
        elif failures:
            record["flush_state"] = "failed"
            record["verification"] = state_from_error(failures[0].get("error", {}))
        else:
            record["flush_state"] = "mirrored" if len(targets) > 1 else "flushed"
        record["updated_at"] = timestamp
        store.upsert(record)
        updated.append(record)
    return updated


def _row_to_record(row: tuple[Any, ...]) -> dict[str, Any]:
    record = dict(zip(_COLUMNS, row))
    record["source_pointer"] = json.loads(record["source_pointer"])
    return record


def _record_id(record: dict[str, Any]) -> str:
    stable = {
        "memory_type": record["memory_type"],
        "content_ref": record["content_ref"],
        "source_pointer": record["source_pointer"],
        "created_at": record["created_at"],
    }
    digest = hashlib.sha256(json.dumps(stable, sort_keys=True).encode("utf-8")).hexdigest()
    return f"cache_{digest[:16]}"
