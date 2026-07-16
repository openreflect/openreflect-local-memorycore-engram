"""JSONL local file backend for the MemoryCore MVP (EN-020).

A zero-dependency, append-only memory backend: one JSON line per memory in a
local store file. The store is backend-owned content (like a QMD corpus
directory) and must live outside public artifacts; the default path is under
the gitignored .memorycore directory, overridable with MEMORYCORE_JSONL_STORE.

Verification is proof-based and deterministic in every mode: a memory is
verified when its line exists and its content hashes match; a content
mismatch is stale; an absent line or store is missing; an unreadable store
is unknown. This backend never needs a subprocess or a live runtime.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


BACKEND_ID = "jsonl_store"
STORE_NAME = "memorycore"


def store_pointer(memory_id: str) -> dict[str, Any]:
    return {
        "backend_id": BACKEND_ID,
        "pointer_id": f"jsonl://{STORE_NAME}/{memory_id}",
        "source_uri": f"jsonl://{STORE_NAME}/{memory_id}",
    }


def jsonl_write(store_path: Path, *, memory_id: str, content: str, memory_type: str, client_surface: str, timestamp: str) -> dict[str, Any]:
    """Append one memory line and read it back to earn the verified stamp."""
    record = {
        "memory_id": memory_id,
        "memory_type": memory_type,
        "content": content,
        "content_hash": _hash(content),
        "client_surface": client_surface,
        "created_at": timestamp,
    }
    store_path.parent.mkdir(parents=True, exist_ok=True)
    with store_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")

    read_back = jsonl_get(store_path, memory_id)
    verification = "verified" if read_back is not None and _hash(read_back.get("content", "")) == record["content_hash"] else "unknown"
    return {"pointer": store_pointer(memory_id), "content_hash": record["content_hash"], "verification_state": verification}


def jsonl_get(store_path: Path, memory_id: str) -> dict[str, Any] | None:
    """Return the last line for a memory id, or None."""
    if not store_path.exists():
        return None
    found = None
    with store_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("memory_id") == memory_id:
                found = record
    return found


def jsonl_search(store_path: Path, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """Substring search over stored content; newest line per id wins."""
    if not store_path.exists():
        return []
    latest: dict[str, dict[str, Any]] = {}
    with store_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("memory_id"):
                latest[record["memory_id"]] = record
    matches = [record for record in latest.values() if query.lower() in record.get("content", "").lower()]
    matches.sort(key=lambda record: (record.get("created_at", ""), record.get("memory_id", "")))
    return matches[:limit]


def jsonl_verify(store_path: Path, memory_id: str, *, expected_hash: str | None = None) -> str:
    """Backend-proof verification per EN-018 semantics, no subprocess needed."""
    try:
        record = jsonl_get(store_path, memory_id)
    except OSError:
        return "unknown"
    if record is None:
        return "missing"
    stored_content_hash = _hash(record.get("content", ""))
    if stored_content_hash != record.get("content_hash"):
        return "stale"
    if expected_hash and stored_content_hash != expected_hash:
        return "stale"
    return "verified"


def memory_id_from_pointer(pointer_id: str) -> str:
    return pointer_id.rsplit("/", 1)[-1]


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
