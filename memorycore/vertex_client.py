"""Live Vertex AI Memory Bank client boundary (EN-038).

The EN-037 adapter normalizes Memory-Bank-shaped output; this module is the
gated boundary that produces it for real. Zero new dependencies, per the
repo's spine: authentication rides the allowlisted ``gcloud auth
print-access-token`` subprocess (the ADR-0003 CLI-boundary pattern — no
google-cloud SDK import), transport is stdlib urllib against the v1 REST
API, and every call is scoped to one configured Agent Engine instance.

Configuration (nothing is remote unless the operator says so twice —
the backend must be enabled AND an engine must be configured):

- ``MEMORYCORE_VERTEX_ENGINE`` env var, or ``backends.vertex_memory_bank
  .engine`` in the operator config: the full reasoning-engine resource
  name, ``projects/{n}/locations/{loc}/reasoningEngines/{id}``.
- ``MEMORYCORE_VERTEX_SCOPE_USER`` (default ``operator``): the user_id
  scope stamped on writes and retrievals. Scope is Memory Bank's
  immutable exact-match isolation boundary.
- ``MEMORYCORE_GCLOUD_BIN`` (default ``gcloud``), ``MEMORYCORE_VERTEX_
  TIMEOUT_SECONDS`` (default 30).

Content-sparse discipline: access tokens live in process memory for the
duration of a call and are never logged or persisted; error surfaces carry
HTTP status codes and bounded server messages, never facts.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any

DEFAULT_GCLOUD_BIN = "gcloud"
DEFAULT_TIMEOUT_SECONDS = 30.0
_ENGINE_RE = re.compile(r"^projects/[^/]+/locations/(?P<location>[^/]+)/reasoningEngines/[^/]+$")


class VertexClientError(Exception):
    def __init__(self, message: str, *, code: str = "VERTEX_CLIENT_ERROR") -> None:
        super().__init__(message)
        self.code = code


def engine_name(config: dict[str, Any] | None = None) -> str | None:
    """Configured engine resource name: env var beats operator config."""
    env = os.environ.get("MEMORYCORE_VERTEX_ENGINE")
    if env:
        return env
    if config:
        return config.get("backends", {}).get("vertex_memory_bank", {}).get("engine")
    return None


def vertex_scope() -> dict[str, str]:
    return {"user_id": os.environ.get("MEMORYCORE_VERTEX_SCOPE_USER", "operator")}


def _timeout() -> float:
    return float(os.environ.get("MEMORYCORE_VERTEX_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))


def _access_token() -> str:
    gcloud_bin = os.environ.get("MEMORYCORE_GCLOUD_BIN", DEFAULT_GCLOUD_BIN)
    try:
        completed = subprocess.run(
            [gcloud_bin, "auth", "print-access-token"],
            capture_output=True,
            text=True,
            timeout=_timeout(),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VertexClientError(f"gcloud token acquisition failed: {type(exc).__name__}") from exc
    if completed.returncode != 0 or not completed.stdout.strip():
        raise VertexClientError(
            "gcloud auth print-access-token failed; is gcloud authenticated on this host?"
        )
    return completed.stdout.strip()


def _endpoint(engine: str) -> str:
    match = _ENGINE_RE.match(engine)
    if not match:
        raise VertexClientError(
            "MEMORYCORE_VERTEX_ENGINE must be a full resource name: "
            "projects/{n}/locations/{loc}/reasoningEngines/{id}"
        )
    return f"https://{match.group('location')}-aiplatform.googleapis.com/v1"


def _api(method: str, url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        method=method,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers={
            "Authorization": f"Bearer {_access_token()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=_timeout()) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = json.loads(exc.read().decode("utf-8")).get("error", {}).get("message", "")[:160]
        except (ValueError, OSError):
            pass
        if exc.code == 404:
            raise VertexClientError("memory bank resource not found", code="VERTEX_NOT_FOUND") from exc
        raise VertexClientError(f"Memory Bank API HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise VertexClientError(f"Memory Bank API unreachable: {type(exc).__name__}") from exc


def _await_operation(operation: dict[str, Any], *, base: str) -> dict[str, Any]:
    """Poll a long-running operation to completion; return its response."""
    deadline = time.monotonic() + _timeout()
    while not operation.get("done"):
        if time.monotonic() > deadline:
            raise VertexClientError("Memory Bank operation did not complete in time")
        time.sleep(1.0)
        operation = _api("GET", f"{base}/{operation['name']}")
    if "error" in operation:
        raise VertexClientError(
            f"Memory Bank operation failed: {operation['error'].get('message', 'unknown')[:160]}"
        )
    return operation.get("response", {})


def live_create_memory(fact: str, *, engine: str, scope: dict[str, str] | None = None) -> dict[str, Any]:
    """CreateMemory: an explicit fact, scoped. Returns the created Memory."""
    base = _endpoint(engine)
    operation = _api(
        "POST",
        f"{base}/{engine}/memories",
        {"fact": fact, "scope": scope or vertex_scope()},
    )
    return _await_operation(operation, base=base)


def live_get_memory(memory_name: str, *, engine: str) -> dict[str, Any] | None:
    """GetMemory read-back; None when the resource is gone (missing)."""
    base = _endpoint(engine)
    try:
        return _api("GET", f"{base}/{memory_name}")
    except VertexClientError as exc:
        if exc.code == "VERTEX_NOT_FOUND":
            return None
        raise


def live_retrieve_memories(
    query: str,
    *,
    engine: str,
    top_k: int = 10,
    scope: dict[str, str] | None = None,
) -> dict[str, Any]:
    """RetrieveMemories by similarity within scope. Returns the raw response
    (``retrievedMemories``) for the EN-037 normalizer."""
    base = _endpoint(engine)
    return _api(
        "POST",
        f"{base}/{engine}/memories:retrieve",
        {
            "scope": scope or vertex_scope(),
            "similaritySearchParams": {"searchQuery": query, "topK": top_k},
        },
    )
