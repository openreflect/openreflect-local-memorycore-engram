"""gbrain adapter contract for the MemoryCore MVP (EN-035).

gbrain (github.com/garrytan/gbrain) is a page-level knowledge brain with
schema packs, capture write-through, timelines, and ingest logs. Its single
sanctioned write entrance is `gbrain capture`, which reports the page slug,
status, and content hash — a natural fit for MemoryCore's pointer + hash
receipt model.

This module is fixture-first: it normalizes gbrain-shaped capture and page
output into the shared result contract. The live subprocess boundary
(allowlisted `gbrain` CLI calls, per the ADR-0003 pattern) lands when a
local gbrain install is configured; until then live-local requests degrade
honestly rather than guessing CLI flags.
"""

from __future__ import annotations

from typing import Any

BACKEND_ID = "gbrain"


def gbrain_pointer(slug: str) -> dict[str, Any]:
    return {
        "backend_id": BACKEND_ID,
        "pointer_id": f"gbrain://pages/{slug}",
        "source_uri": f"gbrain://pages/{slug}",
    }


def normalize_gbrain_capture(request: dict[str, Any], gbrain_output: dict[str, Any]) -> dict[str, Any]:
    """Normalize a gbrain capture result into the shared write contract.

    Capture reports slug, status, and contentHash. A successful capture is a
    delivery acknowledgment with a hash receipt — verification stays
    `unknown` until a read-back can prove the page against the brain, per
    the never-overclaim rule.
    """
    slug = gbrain_output.get("slug")
    if not slug or gbrain_output.get("status") not in ("created", "updated"):
        return {
            "request_id": request["request_id"],
            "operation": request.get("operation", "cache_write"),
            "status": "error",
            "results": [],
            "verification_state": "unknown",
            "error": {
                "code": "GBRAIN_CAPTURE_FAILED",
                "category": "backend_error",
                "message": "gbrain capture did not report a created or updated page.",
                "verification_state": "unknown",
                "details": {"backend_id": BACKEND_ID, "status": gbrain_output.get("status")},
            },
        }

    return {
        "request_id": request["request_id"],
        "operation": request.get("operation", "cache_write"),
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "content_hash": gbrain_output.get("contentHash", ""),
        "results": [
            {
                "backend_id": BACKEND_ID,
                "pointer": gbrain_pointer(slug),
                "recall_mode": "gbrain_capture",
                "capture_status": gbrain_output["status"],
                "verification_state": "unknown",
            }
        ],
        "verification_state": "unknown",
    }


def normalize_gbrain_page(request: dict[str, Any], gbrain_output: dict[str, Any]) -> dict[str, Any]:
    """Normalize a gbrain page read into the shared get contract."""
    slug = gbrain_output.get("slug")
    if not slug:
        return {
            "request_id": request["request_id"],
            "operation": "get",
            "status": "error",
            "results": [],
            "verification_state": "missing",
            "error": {
                "code": "POINTER_MISSING",
                "category": "pointer_missing",
                "message": "gbrain page not found.",
                "verification_state": "missing",
                "details": {"backend_id": BACKEND_ID},
            },
        }

    return {
        "request_id": request["request_id"],
        "operation": "get",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": [
            {
                "backend_id": BACKEND_ID,
                "pointer": gbrain_pointer(slug),
                "content": gbrain_output.get("content", ""),
                "content_hash": gbrain_output.get("contentHash", ""),
                "recall_mode": "gbrain_page",
                "verification_state": "unknown",
            }
        ],
        "verification_state": "unknown",
    }
