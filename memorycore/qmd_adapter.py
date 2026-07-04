"""QMD adapter contract for the MemoryCore MVP.

This module normalizes static fixture-shaped QMD output and provides an
explicit live-local subprocess boundary for local-only validation. It does not
import QMD, Burrow, OpenClaw, or any live local index.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any


BACKEND_ID = "qmd"
DEFAULT_QMD_BIN = "qmd"
DEFAULT_TIMEOUT_SECONDS = 10.0


def qmd_health(request_id: str, status: str = "unknown") -> dict[str, Any]:
    return {
        "request_id": request_id,
        "operation": "health",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": [
            {
                "backend_id": BACKEND_ID,
                "pointer": {"backend_id": BACKEND_ID, "pointer_id": "qmd:health"},
                "snippet": f"QMD fixture adapter health is {status}.",
                "verification_state": "unknown",
            }
        ],
        "verification_state": "unknown",
    }


def normalize_qmd_search(request: dict[str, Any], qmd_output: dict[str, Any]) -> dict[str, Any]:
    if "error" in qmd_output:
        return _error_result(request, "search", qmd_output["error"])

    items = []
    for rank, item in enumerate(qmd_output.get("results", []), start=1):
        path = item["path"]
        items.append(
            {
                "backend_id": BACKEND_ID,
                "pointer": {
                    "backend_id": BACKEND_ID,
                    "pointer_id": path,
                    "source_uri": path,
                },
                "snippet": item.get("snippet", ""),
                "score": item.get("score"),
                "rank": rank,
                "recall_mode": "qmd_fixture",
                "verification_state": "unknown",
            }
        )

    return {
        "request_id": request["request_id"],
        "operation": "search",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": items,
        "verification_state": "unknown",
    }


def normalize_qmd_get(request: dict[str, Any], qmd_output: dict[str, Any]) -> dict[str, Any]:
    if "error" in qmd_output:
        return _error_result(request, "get", qmd_output["error"])

    path = qmd_output["path"]
    return {
        "request_id": request["request_id"],
        "operation": "get",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": [
            {
                "backend_id": BACKEND_ID,
                "pointer": {
                    "backend_id": BACKEND_ID,
                    "pointer_id": path,
                    "source_uri": path,
                },
                "content": qmd_output["content"],
                "verification_state": "unknown",
            }
        ],
        "verification_state": "unknown",
    }


def live_local_qmd_status(
    request_id: str,
    *,
    qmd_bin: str = DEFAULT_QMD_BIN,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Return local QMD status through the explicit live-local mode."""

    request = {"request_id": request_id}
    completed = _run_qmd([qmd_bin, "status"], timeout_seconds=timeout_seconds)
    if completed["status"] == "error":
        return _error_result(request, "health", completed["error"])

    snippet = _first_line(completed.get("stdout", "")) or "QMD status completed."
    return {
        "request_id": request_id,
        "operation": "health",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": [
            {
                "backend_id": BACKEND_ID,
                "pointer": {"backend_id": BACKEND_ID, "pointer_id": "qmd:status", "source_uri": "qmd:status"},
                "snippet": snippet,
                "recall_mode": "qmd_live_local",
                "verification_state": "unknown",
            }
        ],
        "verification_state": "unknown",
    }


def live_local_qmd_search(
    request: dict[str, Any],
    *,
    collection: str,
    qmd_bin: str = DEFAULT_QMD_BIN,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Search local QMD through an explicit collection-scoped subprocess call."""

    command = [
        qmd_bin,
        "search",
        "--json",
        "-n",
        str(request.get("limit", 5)),
        "-c",
        collection,
        request["query"],
    ]
    completed = _run_qmd(command, timeout_seconds=timeout_seconds)
    if completed["status"] == "error":
        return _error_result(request, "search", completed["error"])

    parsed = _parse_json_output(request, "search", completed["stdout"])
    if parsed["status"] == "error":
        return parsed

    return _normalize_live_search(request, parsed["value"])


def live_local_qmd_get(
    request: dict[str, Any],
    *,
    qmd_bin: str = DEFAULT_QMD_BIN,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    line_limit: int = 80,
) -> dict[str, Any]:
    """Get a local QMD pointer through explicit live-local mode."""

    pointer_id = request.get("pointer", {}).get("pointer_id")
    if not pointer_id:
        return _error_result(
            request,
            "get",
            {
                "code": "POINTER_MISSING",
                "category": "pointer_missing",
                "message": "QMD pointer_id is required.",
                "verification_state": "missing",
                "details": {"backend_id": BACKEND_ID},
            },
        )

    command = [qmd_bin, "multi-get", pointer_id, "-l", str(line_limit), "--json"]
    completed = _run_qmd(command, timeout_seconds=timeout_seconds)
    if completed["status"] == "error":
        return _error_result(request, "get", completed["error"])

    parsed = _parse_json_output(request, "get", completed["stdout"])
    if parsed["status"] == "error":
        return parsed

    return _normalize_live_get(request, parsed["value"], pointer_id)


def live_local_qmd_write(
    request: dict[str, Any],
    *,
    content: str,
    corpus_dir: str,
    collection: str,
    memory_id: str,
    frontmatter: dict[str, Any],
    qmd_bin: str = DEFAULT_QMD_BIN,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Materialize content into the dedicated write collection (ADR-0005).

    Writes a markdown file with provenance frontmatter, reindexes through the
    allowlisted CLI, and reads the file back to earn the verified stamp.
    Content is never persisted anywhere except the backend-owned corpus file.
    """

    from pathlib import Path

    directory = Path(corpus_dir).expanduser()
    filename = f"{memory_id}.md"
    file_path = directory / filename
    pointer_id = f"qmd://{collection}/{filename}"

    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    body = "\n".join(lines) + "\n\n" + content.rstrip() + "\n"

    try:
        directory.mkdir(parents=True, exist_ok=True)
        file_path.write_text(body, encoding="utf-8")
    except OSError as exc:
        return _error_result(
            request,
            "cache_write",
            {
                "code": "QMD_WRITE_FAILED",
                "category": "backend_error",
                "message": "Could not materialize memory file in the write collection.",
                "verification_state": "unknown",
                "details": {"backend_id": BACKEND_ID, "exception_type": exc.__class__.__name__},
            },
        )

    updated = _run_qmd([qmd_bin, "update"], timeout_seconds=timeout_seconds)
    if updated["status"] == "error":
        return _error_result(request, "cache_write", updated["error"])

    read_back = _run_qmd([qmd_bin, "multi-get", pointer_id, "--json"], timeout_seconds=timeout_seconds)
    verification = "unknown"
    if read_back["status"] == "ok":
        try:
            rows = json.loads(read_back.get("stdout", ""))
        except json.JSONDecodeError:
            rows = None
        if isinstance(rows, list) and rows:
            verification = "verified"

    return {
        "request_id": request["request_id"],
        "operation": "cache_write",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": [
            {
                "backend_id": BACKEND_ID,
                "pointer": {
                    "backend_id": BACKEND_ID,
                    "pointer_id": pointer_id,
                    "source_uri": str(file_path),
                },
                "recall_mode": "qmd_live_local",
                "verification_state": verification,
            }
        ],
        "verification_state": verification,
    }


def _normalize_live_search(request: dict[str, Any], qmd_output: Any) -> dict[str, Any]:
    rows = _result_rows(qmd_output)
    items = []
    for rank, item in enumerate(rows, start=1):
        pointer_id = _item_pointer(item)
        if not pointer_id:
            continue
        result = {
            "backend_id": BACKEND_ID,
            "pointer": {
                "backend_id": BACKEND_ID,
                "pointer_id": pointer_id,
                "source_uri": pointer_id,
            },
            "snippet": _item_text(item, ("snippet", "text", "content", "preview")),
            "rank": rank,
            "recall_mode": "qmd_live_local",
            "verification_state": "unknown",
        }
        score = _item_score(item)
        if score is not None:
            result["score"] = score
        items.append(result)

    return {
        "request_id": request["request_id"],
        "operation": "search",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": items,
        "verification_state": "unknown",
    }


def _normalize_live_get(request: dict[str, Any], qmd_output: Any, pointer_id: str) -> dict[str, Any]:
    if isinstance(qmd_output, list) and qmd_output and isinstance(qmd_output[0], dict):
        path = _item_pointer(qmd_output[0]) or pointer_id
        content = _item_text(qmd_output[0], ("content", "text", "body", "markdown"))
    elif isinstance(qmd_output, dict):
        path = _item_pointer(qmd_output) or pointer_id
        content = _item_text(qmd_output, ("content", "text", "body", "markdown"))
    else:
        path = pointer_id
        content = str(qmd_output)

    return {
        "request_id": request["request_id"],
        "operation": "get",
        "status": "ok",
        "selected_backend": BACKEND_ID,
        "results": [
            {
                "backend_id": BACKEND_ID,
                "pointer": {
                    "backend_id": BACKEND_ID,
                    "pointer_id": path,
                    "source_uri": path,
                },
                "content": content,
                "recall_mode": "qmd_live_local",
                "verification_state": "verified",
            }
        ],
        "verification_state": "verified",
    }


def _run_qmd(command: list[str], *, timeout_seconds: float) -> dict[str, Any]:
    binary = command[0]
    if shutil.which(binary) is None:
        return {"status": "error", "error": _qmd_error("backend_unavailable", "QMD CLI is not available.", command)}

    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": _qmd_error("backend_timeout", "QMD command timed out.", command)}

    if completed.returncode != 0:
        return {"status": "error", "error": _stderr_error(completed.stderr or completed.stdout, completed.returncode, command)}

    return {"status": "ok", "stdout": completed.stdout, "stderr": completed.stderr}


def _parse_json_output(request: dict[str, Any], operation: str, stdout: str) -> dict[str, Any]:
    try:
        return {"status": "ok", "value": json.loads(stdout)}
    except json.JSONDecodeError:
        return _error_result(
            request,
            operation,
            {
                "code": "QMD_COMMAND_ERROR",
                "category": "unknown_failure",
                "message": "QMD did not return JSON output.",
                "verification_state": "unknown",
                "details": {"backend_id": BACKEND_ID},
            },
        )


def _result_rows(qmd_output: Any) -> list[dict[str, Any]]:
    if isinstance(qmd_output, list):
        return [item for item in qmd_output if isinstance(item, dict)]
    if isinstance(qmd_output, dict):
        for key in ("results", "items", "matches", "files"):
            value = qmd_output.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _item_pointer(item: dict[str, Any]) -> str | None:
    for key in ("path", "file", "uri", "source_uri", "pointer_id", "id"):
        value = item.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _item_text(item: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str):
            return value
    return ""


def _item_score(item: dict[str, Any]) -> float | None:
    value = item.get("score")
    if isinstance(value, int | float):
        return float(value)
    return None


def _stderr_error(stderr: str, returncode: int, command: list[str]) -> dict[str, Any]:
    message = _first_line(stderr) or "QMD command failed."
    lowered = message.lower()
    if "document not found" in lowered or "file not found" in lowered or "no files matched pattern" in lowered:
        return {
            "code": "POINTER_MISSING",
            "category": "pointer_missing",
            "message": message,
            "verification_state": "missing",
            "details": {"backend_id": BACKEND_ID, "returncode": returncode},
        }
    if "collection not found" in lowered:
        return _qmd_error("backend_unavailable", message, command, returncode=returncode, reason="collection_not_found")
    return _qmd_error("unknown_failure", message, command, returncode=returncode)


def _qmd_error(
    category: str,
    message: str,
    command: list[str],
    *,
    returncode: int | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    code_by_category = {
        "backend_unavailable": "BACKEND_UNAVAILABLE",
        "backend_timeout": "BACKEND_TIMEOUT",
    }
    code = code_by_category.get(category, "QMD_COMMAND_ERROR")
    details: dict[str, Any] = {
        "backend_id": BACKEND_ID,
        "command": _redacted_command(command),
    }
    if returncode is not None:
        details["returncode"] = returncode
    if reason:
        details["reason"] = reason
    return {
        "code": code,
        "category": category,
        "message": message,
        "verification_state": "unknown",
        "details": details,
    }


def _redacted_command(command: list[str]) -> list[str]:
    return [command[0], *("<arg>" for _ in command[1:])]


def _error_result(request: dict[str, Any], operation: str, error: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_id": request["request_id"],
        "operation": operation,
        "status": "error",
        "selected_backend": BACKEND_ID,
        "results": [],
        "verification_state": error.get("verification_state", "unknown"),
        "error": error,
    }


def _first_line(value: str) -> str:
    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""
