"""Attributed multi-backend recall for the MemoryCore MVP (EN-021).

One query fans out to every lane that can answer — the cache's pointer
index, JSONL content, and the live QMD index when live-local mode is
configured — and the results merge WITH attribution: every item names its
backend and source lane, carries its verification state, and duplicates
found by multiple lanes collapse into one entry that lists its
corroborating lanes (the first slice of cross-backend identity, IDEA-017;
identity is exact-pointer equality for now, normalization comes later).

Lane honesty is the contract's spine: a lane that cannot run appears in
the response saying so (fixture mode, operator-disabled, no adapter,
backend error) — never silently missing. Snippets are response-only; the
cache and audit stay content-sparse.
"""

from __future__ import annotations

import os
import time
from typing import Any

from memorycore.cache_router import CacheStore
from memorycore.jsonl_adapter import jsonl_search, store_pointer
from memorycore.operator_config import backend_enabled

MERGE_CONTRACT_VERSION = 1


def fanout_search(
    query: str,
    *,
    store: CacheStore,
    config: dict[str, Any],
    mode: str,
    jsonl_store_path,
    limit: int = 10,
) -> dict[str, Any]:
    lanes: list[dict[str, Any]] = []
    merged: dict[str, dict[str, Any]] = {}

    def add_result(lane: str, backend_id: str, pointer: dict[str, Any], **fields: Any) -> None:
        key = pointer.get("pointer_id") or f"{backend_id}:{len(merged)}"
        if key in merged:
            entry = merged[key]
            if lane not in entry["corroborated_by"]:
                entry["corroborated_by"].append(lane)
            for k, v in fields.items():
                entry.setdefault(k, v)
        else:
            merged[key] = {
                "identity_key": key,
                "backend_id": backend_id,
                "pointer": pointer,
                "corroborated_by": [lane],
                "verification_state": fields.pop("verification_state", "unknown"),
                **fields,
            }

    def run_lane(lane_id: str, backend_id: str, runner) -> None:
        started = time.monotonic()
        try:
            count = runner()
            lanes.append({"lane": lane_id, "backend_id": backend_id, "status": "ok",
                          "count": count, "latency_ms": round((time.monotonic() - started) * 1000, 1)})
        except LaneSkipped as skip:
            lanes.append({"lane": lane_id, "backend_id": backend_id, "status": skip.status, "reason": str(skip)})
        except Exception as exc:  # noqa: BLE001 - lane failures must stay honest, not fatal
            lanes.append({"lane": lane_id, "backend_id": backend_id, "status": "error",
                          "reason": str(exc)[:120]})

    # Lane: cache pointer/id index (always available).
    def cache_lane() -> int:
        rows = [r for r in store.search(query) if query.lower() in
                (r["record_id"] + " " + r["content_ref"] + " " + r["memory_type"]).lower()]
        for r in rows[:limit]:
            add_result("cache", r["source_pointer"].get("backend_id") or "unrouted", r["source_pointer"],
                       record_id=r["record_id"], memory_type=r["memory_type"],
                       verification_state=r["verification"], flush_state=r["flush_state"])
        return len(rows[:limit])

    run_lane("cache", "cache", cache_lane)

    # Lane: JSONL content (zero-dependency, always available unless disabled).
    def jsonl_lane() -> int:
        if not backend_enabled(config, "jsonl_store"):
            raise LaneSkipped("disabled by operator", status="disabled")
        hits = jsonl_search(jsonl_store_path, query, limit=limit)
        for hit in hits:
            pointer = store_pointer(hit["memory_id"])
            record = store.find_by_pointer(pointer["pointer_id"])
            add_result("jsonl_content", "jsonl_store", pointer,
                       record_id=record["record_id"] if record else None,
                       memory_type="local",
                       verification_state=record["verification"] if record else "unknown",
                       snippet=hit.get("content", "")[:160])
        return len(hits)

    run_lane("jsonl_content", "jsonl_store", jsonl_lane)

    # Lane: live QMD index (live-local mode with a configured collection only).
    def qmd_lane() -> int:
        if not backend_enabled(config, "qmd"):
            raise LaneSkipped("disabled by operator", status="disabled")
        if mode != "live-local":
            raise LaneSkipped("fixture mode: live index search not run", status="skipped")
        collection = os.environ.get("MEMORYCORE_QMD_COLLECTION")
        if not collection:
            raise LaneSkipped("MEMORYCORE_QMD_COLLECTION not set", status="skipped")
        from memorycore.qmd_adapter import live_local_qmd_search

        result = live_local_qmd_search(
            {"request_id": "req_fanout_qmd", "query": query, "limit": limit},
            collection=collection,
            qmd_bin=os.environ.get("MEMORYCORE_QMD_BIN", "qmd"),
            timeout_seconds=float(os.environ.get("MEMORYCORE_QMD_TIMEOUT_SECONDS", "10")),
        )
        if result["status"] != "ok":
            raise LaneSkipped(result.get("error", {}).get("message", "qmd search failed"), status="error")
        for item in result["results"]:
            add_result("qmd_index", "qmd", item.get("pointer", {}),
                       verification_state=item.get("verification_state", "unknown"),
                       relevance=item.get("score"),
                       snippet=(item.get("snippet") or "")[:160])
        return len(result["results"])

    run_lane("qmd_index", "qmd", qmd_lane)

    # Lanes that cannot answer on this surface say so explicitly.
    for backend_id, reason in (
        ("lossless_claw", "no host bridge on this surface (ADR-0006 callback is write-side)"),
        ("gbrain", "live search not wired yet (EN-035 next inch)"),
    ):
        status = "disabled" if not backend_enabled(config, backend_id) else "unavailable"
        lanes.append({"lane": f"{backend_id}_search", "backend_id": backend_id,
                      "status": status,
                      "reason": "disabled by operator" if status == "disabled" else reason})

    results = list(merged.values())
    results.sort(key=lambda r: (-len(r["corroborated_by"]), r["identity_key"]))
    return {
        "merge_contract_version": MERGE_CONTRACT_VERSION,
        "query": query,
        "lanes": lanes,
        "results": results[:limit],
        "total_before_limit": len(results),
    }


class LaneSkipped(Exception):
    def __init__(self, reason: str, *, status: str = "skipped") -> None:
        super().__init__(reason)
        self.status = status
