"""CLI developer surface for the MemoryCore MVP.

The CLI operates on public-safe fixture data by default. Setting
``MEMORYCORE_BACKEND_MODE=live-local`` routes QMD reads through the explicit
live-local subprocess adapter (``MEMORYCORE_QMD_BIN`` and
``MEMORYCORE_QMD_COLLECTION`` configure it) and reports Lossless-Claw as
unavailable until a host bridge path exists for this surface. It never calls
Burrow or OpenClaw.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from memorycore.audit_log import append_record, build_audit_record, read_recent
from memorycore.eval import run_public_safe_eval
from memorycore.lcm_adapter import normalize_lcm_get, normalize_lcm_search
from memorycore.qmd_adapter import (
    DEFAULT_QMD_BIN,
    live_local_qmd_get,
    live_local_qmd_search,
    live_local_qmd_verify,
    normalize_qmd_get,
    normalize_qmd_search,
)
from memorycore.registry_router import BackendRegistry, route_request
from memorycore.verification_state import normalize_verify_result


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
DEFAULT_AUDIT_LOG = ROOT / ".memorycore" / "audit.jsonl"

BACKEND_MODES = ("fixture", "live-local")


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "audit":
            return _emit(read_recent(Path(args.audit_log), limit=args.limit), args.json)
        if args.command == "eval":
            if not args.public_safe:
                raise ValueError("only --public-safe eval mode is currently supported")
            result = run_public_safe_eval()
            return _emit(result, args.json, ok=result["status"] == "ok")
        if args.command == "viewer":
            from memorycore.viewer import serve_viewer, write_viewer

            cache_db = Path(os.environ.get("MEMORYCORE_CACHE_DB", ROOT / ".memorycore" / "cache.sqlite3"))
            if args.serve:
                serve_viewer(cache_db, Path(args.audit_log), port=args.port, host=args.host)
                return 0
            output = write_viewer(cache_db, Path(args.audit_log), Path(args.output))
            return _emit({"status": "ok", "viewer": str(output)}, args.json)

        request = _request_from_args(args)
        result = _execute_request(request)

        if args.command in {"search", "get", "verify"}:
            record = build_audit_record(request, result, timestamp=_timestamp())
            append_record(Path(args.audit_log), record)
            result = {**result, "audit_id": record["audit_id"]}

        return _emit(result, args.json, ok=result.get("status") != "error")
    except (KeyError, TypeError, ValueError, FileNotFoundError) as exc:
        error = {
            "status": "error",
            "error": {
                "code": "CLI_ERROR",
                "category": "client_surface",
                "message": str(exc),
            },
        }
        _emit(error, getattr(args, "json", True), ok=False)
        return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="memorycore")
    parser.add_argument("--json", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--audit-log", default=str(DEFAULT_AUDIT_LOG))
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-backends")
    subparsers.add_parser("health")

    search = subparsers.add_parser("search")
    search.add_argument("query")
    search.add_argument("--backend", choices=["qmd", "lossless_claw", "mock_healthy"])
    search.add_argument("--intent", default="file_corpus_recall", choices=["file_corpus_recall", "transcript_continuity_recall"])
    search.add_argument("--limit", type=int, default=5)

    get = subparsers.add_parser("get")
    get.add_argument("pointer_id")
    get.add_argument("--backend", default="qmd", choices=["qmd", "lossless_claw", "mock_healthy"])

    verify = subparsers.add_parser("verify")
    verify.add_argument("pointer_id")
    verify.add_argument("--backend", default="mock_healthy", choices=["qmd", "lossless_claw", "mock_healthy"])
    verify.add_argument("--state", default="verified", choices=["verified", "stale", "missing", "unsupported", "unknown"])

    audit = subparsers.add_parser("audit")
    audit.add_argument("--limit", type=int, default=10)

    eval_parser = subparsers.add_parser("eval")
    eval_parser.add_argument("--public-safe", action="store_true", required=True)

    viewer = subparsers.add_parser("viewer")
    viewer.add_argument("--output", default=str(ROOT / ".memorycore" / "viewer.html"))
    viewer.add_argument("--serve", action="store_true")
    viewer.add_argument("--port", type=int, default=8787)
    viewer.add_argument("--host", default="127.0.0.1")

    return parser


def _request_from_args(args: argparse.Namespace) -> dict[str, Any]:
    base = {
        "request_id": f"req_cli_{args.command}",
        "client_surface": "cli",
        "operation": _operation(args.command),
    }

    if args.command in {"list-backends", "health"}:
        return {**base, "operation": "health", "intent": "backend_health"}
    if args.command == "search":
        if args.limit < 1 or args.limit > 50:
            raise ValueError("search --limit must be between 1 and 50")
        return {
            **base,
            "intent": args.intent,
            "query": args.query,
            "limit": args.limit,
            **({"backend_hint": args.backend} if args.backend else {}),
        }
    if args.command == "get":
        return {
            **base,
            "intent": "source_get",
            "pointer": {"backend_id": args.backend, "pointer_id": args.pointer_id, "source_uri": args.pointer_id},
        }
    if args.command == "verify":
        return {
            **base,
            "intent": "source_verify",
            "pointer": {"backend_id": args.backend, "pointer_id": args.pointer_id, "source_uri": args.pointer_id},
            "verification_state": args.state,
        }

    raise ValueError(f"unsupported command: {args.command}")


def _operation(command: str) -> str:
    if command == "list-backends":
        return "health"
    return command


def operator_config_path() -> Path:
    override = os.environ.get("MEMORYCORE_CONFIG")
    return Path(override).expanduser() if override else ROOT / ".memorycore" / "config.json"


def resolve_backend_mode() -> str:
    """Precedence: explicit env var > operator config file > fixture default."""
    mode = os.environ.get("MEMORYCORE_BACKEND_MODE")
    if mode is None:
        from memorycore.operator_config import load_config

        mode = load_config(operator_config_path()).get("mode", "fixture")
    if mode not in BACKEND_MODES:
        raise ValueError(f"unsupported backend mode: {mode}")
    return mode


def _qmd_live_config() -> dict[str, Any]:
    return {
        "qmd_bin": os.environ.get("MEMORYCORE_QMD_BIN", DEFAULT_QMD_BIN),
        "collection": os.environ.get("MEMORYCORE_QMD_COLLECTION"),
    }


def _registry_for_mode(mode: str) -> BackendRegistry:
    data = _load_json(FIXTURES / "backend-registry" / "basic.json")
    if mode == "fixture":
        return BackendRegistry.from_dict(data)

    for backend in data["backends"]:
        if backend["backend_id"] == "qmd":
            config = _qmd_live_config()
            if shutil.which(config["qmd_bin"]) is None:
                backend["health"] = "unavailable"
                backend["error"] = {
                    "code": "BACKEND_UNAVAILABLE",
                    "category": "backend_unavailable",
                    "message": "QMD CLI is not available in live-local mode.",
                }
            elif not config["collection"]:
                backend["health"] = "unavailable"
                backend["error"] = {
                    "code": "BACKEND_UNAVAILABLE",
                    "category": "backend_unavailable",
                    "message": "MEMORYCORE_QMD_COLLECTION is not set for live-local mode.",
                }
            else:
                backend["health"] = "healthy"
                if "verify" not in backend["capabilities"]:
                    backend["capabilities"] = [*backend["capabilities"], "verify"]
                if "source_verify" not in backend.get("default_intents", []):
                    backend["default_intents"] = [*backend.get("default_intents", []), "source_verify"]
        elif backend["backend_id"] == "lossless_claw":
            backend["health"] = "unavailable"
            backend["error"] = {
                "code": "BACKEND_UNAVAILABLE",
                "category": "backend_unavailable",
                "message": "LCM host bridge is not configured for this surface in live-local mode.",
            }
    return BackendRegistry.from_dict(data)


def _execute_request(request: dict[str, Any]) -> dict[str, Any]:
    mode = resolve_backend_mode()
    registry = _registry_for_mode(mode)
    routed = route_request(request, registry)
    if routed["status"] == "error" or request["operation"] == "health":
        return routed

    backend_id = routed["selected_backend"]
    operation = request["operation"]

    if mode == "live-local" and backend_id == "qmd":
        config = _qmd_live_config()
        timeout = float(os.environ.get("MEMORYCORE_QMD_TIMEOUT_SECONDS", "10"))
        if operation == "search":
            return live_local_qmd_search(request, collection=config["collection"], qmd_bin=config["qmd_bin"], timeout_seconds=timeout)
        if operation == "get":
            return live_local_qmd_get(request, qmd_bin=config["qmd_bin"], timeout_seconds=timeout)
        if operation == "verify":
            return live_local_qmd_verify(request, qmd_bin=config["qmd_bin"], timeout_seconds=timeout)

    if backend_id == "qmd" and operation == "search":
        return normalize_qmd_search(request, _load_json(FIXTURES / "qmd" / "search-results.json"))
    if backend_id == "qmd" and operation == "get":
        return normalize_qmd_get(request, _load_json(FIXTURES / "qmd" / "get-result.json"))
    if backend_id == "lossless_claw" and operation == "search":
        return normalize_lcm_search(request, _load_json(FIXTURES / "lcm" / "grep-results.json"))
    if backend_id == "lossless_claw" and operation == "get":
        return normalize_lcm_get(request, _load_json(FIXTURES / "lcm" / "expand-query-result.json"))
    if operation == "verify":
        return normalize_verify_result(request, backend_id, {"verification_state": request.get("verification_state", "unknown")})

    return {
        **routed,
        "results": [
            {
                "backend_id": backend_id,
                "pointer": {"backend_id": backend_id, "pointer_id": "mock:fixture"},
                "snippet": "Mock fixture route completed.",
                "verification_state": "unknown",
            }
        ],
        "verification_state": "unknown",
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _emit(value: Any, as_json: bool, *, ok: bool = True) -> int:
    if as_json:
        print(json.dumps(value, indent=2, sort_keys=True))
    else:
        print(value)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
