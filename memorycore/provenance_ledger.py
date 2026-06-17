"""Public-safe provenance pointer ledger for the MemoryCore MVP.

The ledger stores request/result metadata and pointers only. It intentionally
does not persist snippets, content, citations, or private source text.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


POINTER_FIELDS = (
    "backend_id",
    "pointer_id",
    "source_uri",
    "summary_id",
    "message_id",
    "conversation_id",
)


def build_result_records(result: dict[str, Any], *, timestamp: str) -> list[dict[str, Any]]:
    records = []
    for index, item in enumerate(result.get("results", []), start=1):
        pointer = _clean_pointer(item.get("pointer", {}))
        record = {
            "request_id": result["request_id"],
            "backend_id": item.get("backend_id") or result.get("selected_backend"),
            "operation": result["operation"],
            "pointer": pointer,
            "verification_state": item.get("verification_state", result.get("verification_state", "unknown")),
            "timestamp": timestamp,
            "result_index": index,
            "status": result.get("status", "ok"),
        }
        record["ledger_id"] = _ledger_id(record)
        records.append(record)

    if not records and result.get("status") == "error":
        error = result.get("error", {})
        record = {
            "request_id": result["request_id"],
            "backend_id": result.get("selected_backend"),
            "operation": result["operation"],
            "pointer": _clean_pointer(error.get("pointer", {})),
            "verification_state": result.get("verification_state", error.get("verification_state", "unknown")),
            "timestamp": timestamp,
            "result_index": None,
            "status": "error",
            "error": {
                "code": error.get("code"),
                "category": error.get("category"),
            },
        }
        record["ledger_id"] = _ledger_id(record)
        records.append(record)

    return records


def append_records(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def read_record(path: Path, ledger_id: str) -> dict[str, Any] | None:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("ledger_id") == ledger_id:
                return record
    return None


def _clean_pointer(pointer: dict[str, Any]) -> dict[str, Any]:
    return {field: pointer[field] for field in POINTER_FIELDS if pointer.get(field)}


def _ledger_id(record: dict[str, Any]) -> str:
    stable = {
        "request_id": record["request_id"],
        "backend_id": record.get("backend_id"),
        "operation": record["operation"],
        "pointer": record.get("pointer", {}),
        "result_index": record.get("result_index"),
        "status": record.get("status"),
        "timestamp": record["timestamp"],
    }
    digest = hashlib.sha256(json.dumps(stable, sort_keys=True).encode("utf-8")).hexdigest()
    return f"prov_{digest[:16]}"
