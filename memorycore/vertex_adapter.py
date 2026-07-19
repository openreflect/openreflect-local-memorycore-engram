"""Vertex AI Memory Bank adapter contract for MemoryCore (EN-037).

Vertex AI Memory Bank (Agent Engine) is Google Cloud's managed extractive
memory service: it generates user-scoped memory facts from conversations
service-side, retrieves them by similarity, and — uniquely among the
services surveyed for IDEA-023 — keeps an automatic immutable revision per
mutation with rollback. Every memory has a stable resource name
(``projects/{p}/locations/{l}/reasoningEngines/{e}/memories/{id}``), which
is exactly the pointer shape MemoryCore's receipts want.

This module is fixture-first: it normalizes Memory-Bank-shaped API output
(generateMemories, retrieveMemories, get) into the shared result contract.
The live client boundary lands when GCP credentials are configured; until
then live-local requests degrade honestly rather than guessing API calls.

Verification is hash-at-observation: the service publishes no content
hashes, so MemoryCore hashes each fact when it observes it and proves
freshness by read-back comparison. A changed fact is ``stale`` — Memory
Bank consolidation revised the memory since observation (the prior
revision remains retrievable service-side). Facts are extracted, not
quoted: results carry a ``source`` of ``generated`` or ``explicit`` so
downstream attribution never confuses the service's inference with the
user's words.
"""

from __future__ import annotations

import hashlib
from typing import Any

BACKEND_ID = "vertex_memory_bank"


def vertex_pointer(memory_name: str) -> dict[str, Any]:
    """Pointer for a Memory Bank memory. The resource name IS the stable id."""
    return {
        "backend_id": BACKEND_ID,
        "pointer_id": memory_name,
        "source_uri": memory_name,
    }


def fact_hash(fact: str) -> str:
    """Hash-at-observation: MemoryCore's own freshness anchor for a fact."""
    return hashlib.sha256(fact.encode("utf-8")).hexdigest()


def normalize_generate_result(request: dict[str, Any], vertex_output: dict[str, Any]) -> dict[str, Any]:
    """Normalize a generateMemories operation response into the write contract.

    The service extracts facts and reports each generated memory with its
    resource name and the consolidation action taken (CREATED / UPDATED /
    DELETED). Facts appear response-only; each result carries the pointer,
    the observed fact hash, and its extraction source. Verification stays
    ``unknown`` until read-back proves the fact, per the never-overclaim rule.
    """
    generated = vertex_output.get("generatedMemories") or []
    normalized = []
    for item in generated:
        memory = item.get("memory") or {}
        name = memory.get("name")
        if not name:
            continue
        normalized.append(
            {
                "backend_id": BACKEND_ID,
                "pointer": vertex_pointer(name),
                "recall_mode": "vertex_generate",
                "action": item.get("action", "CREATED"),
                "fact": memory.get("fact", ""),
                "observed_hash": fact_hash(memory.get("fact", "")),
                "source": memory.get("source", "generated"),
                "scope": memory.get("scope", {}),
                "verification_state": "unknown",
            }
        )

    if not normalized:
        return {
            "request_id": request["request_id"],
            "operation": request.get("operation", "cache_write"),
            "status": "error",
            "results": [],
            "verification_state": "unknown",
            "error": {
                "code": "VERTEX_GENERATE_EMPTY",
                "category": "backend_error",
                "message": "Memory Bank generateMemories reported no generated memories.",
                "verification_state": "unknown",
                "details": {"backend_id": BACKEND_ID},
            },
        }

    return {
        "request_id": request["request_id"],
        "operation": request.get("operation", "cache_write"),
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": normalized,
        "verification_state": "unknown",
    }


def normalize_retrieve_result(request: dict[str, Any], vertex_output: dict[str, Any]) -> dict[str, Any]:
    """Normalize a retrieveMemories response into the search contract.

    Similarity retrieval returns memories with a distance; scope-only
    retrieval returns them without one. Facts are response-only and every
    item is attributed with its pointer and extraction source.
    """
    retrieved = vertex_output.get("retrievedMemories") or []
    results = []
    for item in retrieved:
        memory = item.get("memory") or {}
        name = memory.get("name")
        if not name:
            continue
        entry = {
            "backend_id": BACKEND_ID,
            "pointer": vertex_pointer(name),
            "recall_mode": "vertex_retrieve",
            "fact": memory.get("fact", ""),
            "observed_hash": fact_hash(memory.get("fact", "")),
            "source": memory.get("source", "generated"),
            "scope": memory.get("scope", {}),
            "verification_state": "unknown",
        }
        if item.get("distance") is not None:
            entry["distance"] = item["distance"]
        results.append(entry)

    return {
        "request_id": request["request_id"],
        "operation": "search",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": results,
        "verification_state": "unknown",
    }


def vertex_verify(
    request: dict[str, Any],
    vertex_output: dict[str, Any],
    *,
    expected_hash: str | None,
) -> dict[str, Any]:
    """Prove a Memory Bank pointer by read-back (get) against an observed hash.

    missing — the resource name resolves to nothing; verified — the fact
    hashes to what was observed; stale — the fact changed, meaning Memory
    Bank consolidation created a new revision since observation (the prior
    revision is preserved service-side and could be rolled back to). With
    no expected hash the read-back proves existence only: ``unknown``.
    """
    memory = vertex_output.get("memory") or {}
    name = memory.get("name")
    if not name:
        return {
            "request_id": request["request_id"],
            "operation": "verify",
            "status": "error",
            "results": [],
            "verification_state": "missing",
            "error": {
                "code": "POINTER_MISSING",
                "category": "pointer_missing",
                "message": "Memory Bank has no memory at this resource name.",
                "verification_state": "missing",
                "details": {"backend_id": BACKEND_ID},
            },
        }

    if expected_hash is None:
        state = "unknown"
    elif fact_hash(memory.get("fact", "")) == expected_hash:
        state = "verified"
    else:
        state = "stale"

    result = {
        "backend_id": BACKEND_ID,
        "pointer": vertex_pointer(name),
        "recall_mode": "vertex_get",
        "observed_hash": fact_hash(memory.get("fact", "")),
        "verification_state": state,
    }
    if state == "stale":
        result["stale_reason"] = "fact revised by Memory Bank consolidation since observation"
    return {
        "request_id": request["request_id"],
        "operation": "verify",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": [result],
        "verification_state": state,
    }
