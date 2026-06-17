"""Static backend registry and router contracts for the MemoryCore MVP.

This module deliberately stops at deterministic contract behavior. It does not
import or call QMD, Lossless-Claw, Burrow, OpenClaw, or any live backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


INTENT_OPERATIONS = {
    "file_corpus_recall": "search",
    "transcript_continuity_recall": "search",
    "source_get": "get",
    "source_verify": "verify",
    "backend_health": "health",
}


@dataclass(frozen=True)
class Backend:
    backend_id: str
    display_name: str
    health: str
    capabilities: frozenset[str]
    default_intents: frozenset[str]
    error: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Backend":
        return cls(
            backend_id=data["backend_id"],
            display_name=data["display_name"],
            health=data["health"],
            capabilities=frozenset(data["capabilities"]),
            default_intents=frozenset(data.get("default_intents", [])),
            error=data.get("error"),
        )

    def to_health_result(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "backend_id": self.backend_id,
            "display_name": self.display_name,
            "health": self.health,
            "capabilities": sorted(self.capabilities),
            "default_intents": sorted(self.default_intents),
        }
        if self.error:
            result["error"] = self.error
        return result


class BackendRegistry:
    def __init__(self, backends: list[Backend]) -> None:
        seen: set[str] = set()
        by_id: dict[str, Backend] = {}
        for backend in backends:
            if backend.backend_id in seen:
                raise ValueError(f"duplicate backend_id: {backend.backend_id}")
            seen.add(backend.backend_id)
            by_id[backend.backend_id] = backend
        self._by_id = by_id

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackendRegistry":
        return cls([Backend.from_dict(item) for item in data["backends"]])

    def get(self, backend_id: str) -> Backend | None:
        return self._by_id.get(backend_id)

    def list_health(self) -> list[dict[str, Any]]:
        return [backend.to_health_result() for backend in self._by_id.values()]

    def candidates(self, operation: str, intent: str | None) -> list[Backend]:
        return [
            backend
            for backend in self._by_id.values()
            if operation in backend.capabilities and (intent is None or intent in backend.default_intents)
        ]


def make_error(code: str, category: str, message: str, **details: Any) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "category": category, "message": message}
    if details:
        error["details"] = details
    return error


def route_request(request: dict[str, Any], registry: BackendRegistry) -> dict[str, Any]:
    operation = request.get("operation")
    intent = request.get("intent")

    if operation == "health":
        return {
            "request_id": request["request_id"],
            "operation": operation,
            "status": "ok",
            "results": registry.list_health(),
        }

    requested_backend = request.get("backend_hint") or request.get("pointer", {}).get("backend_id")
    if requested_backend:
        return _route_explicit(request, registry, requested_backend)

    if intent in INTENT_OPERATIONS and INTENT_OPERATIONS[intent] != operation:
        return _error_result(
            request,
            make_error(
                "UNSUPPORTED_OPERATION",
                "unsupported_operation",
                "Request intent does not match operation.",
                intent=intent,
                operation=operation,
                expected_operation=INTENT_OPERATIONS[intent],
            ),
        )

    candidates = registry.candidates(operation, intent)
    healthy = [backend for backend in candidates if backend.health != "unavailable"]
    if not healthy:
        return _error_result(
            request,
            make_error(
                "MISSING_BACKEND",
                "missing_backend",
                "No available backend supports the requested operation and intent.",
                intent=intent,
                operation=operation,
            ),
        )

    backend = healthy[0]
    return _ok_route(request, backend)


def _route_explicit(request: dict[str, Any], registry: BackendRegistry, backend_id: str) -> dict[str, Any]:
    backend = registry.get(backend_id)
    if backend is None:
        return _error_result(
            request,
            make_error("MISSING_BACKEND", "missing_backend", "Requested backend is not registered.", backend_id=backend_id),
        )

    operation = request["operation"]
    if backend.health == "unavailable":
        return _error_result(
            request,
            backend.error
            or make_error("BACKEND_UNAVAILABLE", "backend_unavailable", "Requested backend is unavailable.", backend_id=backend_id),
        )

    if operation not in backend.capabilities:
        category = "verification_unsupported" if operation == "verify" else "unsupported_operation"
        code = "VERIFICATION_UNSUPPORTED" if operation == "verify" else "UNSUPPORTED_OPERATION"
        error = make_error(
            code,
            category,
            "Requested backend does not support the requested operation.",
            backend_id=backend_id,
            operation=operation,
        )
        if category == "verification_unsupported":
            error["verification_state"] = "unsupported"
        return _error_result(request, error)

    return _ok_route(request, backend)


def _ok_route(request: dict[str, Any], backend: Backend) -> dict[str, Any]:
    return {
        "request_id": request["request_id"],
        "operation": request["operation"],
        "status": "ok",
        "selected_backend": backend.backend_id,
        "results": [],
    }


def _error_result(request: dict[str, Any], error: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_id": request["request_id"],
        "operation": request["operation"],
        "status": "error",
        "results": [],
        "error": error,
    }

