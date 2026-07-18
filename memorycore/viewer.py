"""Local provenance viewer for the MemoryCore MVP (EN-024).

Generates a single self-contained HTML dashboard — the "memory receipts"
surface — from the local cache DB and audit log. Local-first and
content-sparse: it renders record ids, pointers, hashes, verification and
flush states, and audit metadata. It never reads backend content stores.

Usage: python3 -m memorycore.cli viewer [--output PATH]
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from memorycore.audit_log import append_record, build_audit_record, read_recent
from memorycore.operator_config import (
    INSTALLED_ADAPTERS,
    apply_config_change,
    describe_backends,
    effective_routing,
    load_config,
)

VERIFICATION_ORDER = ("verified", "stale", "missing", "unsupported", "unknown")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def collect_viewer_data(cache_db: Path, audit_log: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    if cache_db.exists():
        conn = sqlite3.connect(str(cache_db))
        try:
            rows = conn.execute(
                "SELECT record_id, memory_type, content_ref, source_pointer, verification,"
                " flush_state, created_at, updated_at, content_hash FROM cache_records"
                " ORDER BY updated_at DESC, record_id"
            ).fetchall()
        finally:
            conn.close()
        for row in rows:
            records.append(
                {
                    "record_id": row[0],
                    "memory_type": row[1],
                    "content_ref": row[2],
                    "source_pointer": json.loads(row[3]),
                    "verification": row[4],
                    "flush_state": row[5],
                    "created_at": row[6],
                    "updated_at": row[7],
                    "content_hash": row[8] or "",
                }
            )

    audit = read_recent(audit_log, limit=500) if audit_log.exists() else []
    audit = list(reversed(audit))  # newest first

    verification_counts = {state: 0 for state in VERIFICATION_ORDER}
    backend_counts: dict[str, int] = {}
    for record in records:
        verification_counts[record["verification"]] = verification_counts.get(record["verification"], 0) + 1
        backend = record["source_pointer"].get("backend_id") or "unrouted"
        backend_counts[backend] = backend_counts.get(backend, 0) + 1

    import os

    from memorycore.cli import operator_config_path, resolve_backend_mode

    config_path = operator_config_path()
    config = load_config(config_path)
    env_mode = os.environ.get("MEMORYCORE_BACKEND_MODE")

    return {
        "generated_at": _now(),
        "cache_db": str(cache_db),
        "audit_log": str(audit_log),
        "records": records,
        "audit": audit,
        "verification_counts": verification_counts,
        "backend_counts": backend_counts,
        "control": {
            "mode": resolve_backend_mode(),
            "mode_source": "env" if env_mode else "config",
            "backends": describe_backends(config),
            "routing": config.get("routing", {}),
            "routing_effective": {k: list(v) for k, v in effective_routing(config).items()},
            "reserved_classes": ["peer_reasoning", "knowledge_brain", "provenance_fabric"],
            "classes": list(__import__("memorycore.operator_config", fromlist=["BACKEND_CLASSES"]).BACKEND_CLASSES),
            "class_info": __import__("memorycore.operator_config", fromlist=["CLASS_INFO"]).CLASS_INFO,
            "memory_type_info": __import__("memorycore.operator_config", fromlist=["MEMORY_TYPE_INFO"]).MEMORY_TYPE_INFO,
            "config_path": str(config_path),
        },
    }


def handle_control(
    action: str,
    payload: dict[str, Any],
    *,
    cache_db: Path,
    audit_log: Path,
    config_path: Path,
) -> dict[str, Any]:
    """Execute one audited operator control action. Returns a JSON-able result.

    Every action leaves a receipt: config changes via apply_config_change,
    cache actions via a content-sparse operator_ui audit record.
    """
    from memorycore.cache_router import CacheStore, flush_pending
    from memorycore.mcp_surface import FIXTURE_FLUSH_BACKENDS, _verify_cached_record

    if action == "backend":
        backend_id = str(payload.get("backend_id", ""))
        enabled = bool(payload.get("enabled"))
        config = load_config(config_path)
        if backend_id not in config["backends"]:
            return {"status": "error", "message": f"unknown backend: {backend_id}"}

        def mutate(cfg: dict[str, Any]) -> None:
            cfg["backends"][backend_id]["enabled"] = enabled

        apply_config_change(
            config_path, audit_log, action="backend_toggle",
            detail={"backend_id": backend_id, "enabled": enabled}, mutate=mutate,
        )
        return {"status": "ok", "message": f"{backend_id} {'enabled' if enabled else 'disabled'}"}

    if action == "routing":
        memory_type = str(payload.get("memory_type", ""))
        targets = [str(b) for b in payload.get("backends", [])]
        config = load_config(config_path)
        if memory_type not in config["routing"]:
            return {"status": "error", "message": f"unknown memory type: {memory_type}"}
        unknown = [b for b in targets if b not in config["backends"]]
        if unknown:
            return {"status": "error", "message": f"undeclared backends: {', '.join(unknown)}"}

        def mutate(cfg: dict[str, Any]) -> None:
            cfg["routing"][memory_type] = targets

        apply_config_change(
            config_path, audit_log, action="routing_change",
            detail={"memory_type": memory_type, "targets": targets}, mutate=mutate,
        )
        return {"status": "ok", "message": f"{memory_type} -> {', '.join(targets) or '(none)'}"}

    if action == "mode":
        mode = str(payload.get("mode", ""))
        if mode not in ("fixture", "live-local"):
            return {"status": "error", "message": f"unsupported mode: {mode}"}
        import os

        def mutate(cfg: dict[str, Any]) -> None:
            cfg["mode"] = mode

        apply_config_change(config_path, audit_log, action="mode_change", detail={"mode": mode}, mutate=mutate)
        pinned = os.environ.get("MEMORYCORE_BACKEND_MODE")
        note = f" (env override {pinned} still wins)" if pinned else ""
        return {"status": "ok", "message": f"mode set to {mode}{note}"}

    if action == "flush":
        routing = effective_routing(load_config(config_path))
        store = CacheStore(cache_db)
        try:
            flushed = flush_pending(store, FIXTURE_FLUSH_BACKENDS, timestamp=_now(), routing=routing)
        finally:
            store.close()
        record = build_audit_record(
            {"request_id": "req_operator_ui_flush", "client_surface": "operator_ui", "operation": "cache_flush"},
            {"status": "ok", "results": []},
            timestamp=_now(),
        )
        record["config_change"] = {"action": "flush", "processed": len(flushed)}
        append_record(audit_log, record)
        return {"status": "ok", "message": f"flushed {len(flushed)} pending record(s) (fixture-only handlers)"}

    if action == "verify_all":
        store = CacheStore(cache_db)
        try:
            record_ids = [r["record_id"] for r in store.search("", memory_type=None)]
        finally:
            store.close()
        outcomes: dict[str, int] = {}
        for record_id in record_ids:
            result = _verify_cached_record({"record_id": record_id, "client": "operator_ui"}, cache_db)
            state = result.get("verification_state", "unknown")
            outcomes[state] = outcomes.get(state, 0) + 1
        record = build_audit_record(
            {"request_id": "req_operator_ui_verify_all", "client_surface": "operator_ui", "operation": "verify"},
            {"status": "ok", "results": []},
            timestamp=_now(),
        )
        record["config_change"] = {"action": "verify_all", "checked": len(record_ids), **outcomes}
        append_record(audit_log, record)
        summary = ", ".join(f"{k}: {v}" for k, v in sorted(outcomes.items())) or "nothing to verify"
        return {"status": "ok", "message": f"re-verified {len(record_ids)} record(s) — {summary}"}

    if action == "forget":
        record_id = str(payload.get("record_id", ""))
        store = CacheStore(cache_db)
        try:
            record = store.get(record_id)
            if record is None:
                return {"status": "error", "message": f"no such record: {record_id}"}
            store.delete(record_id)
        finally:
            store.close()
        audit = build_audit_record(
            {"request_id": "req_operator_ui_forget", "client_surface": "operator_ui", "operation": "cache_forget"},
            {"status": "ok", "results": [{"pointer": record["source_pointer"], "verification_state": record["verification"]}]},
            timestamp=_now(),
        )
        audit["config_change"] = {"action": "forget", "record_id": record_id}
        append_record(audit_log, audit)
        return {
            "status": "ok",
            "message": f"forgot {record_id} (cache row removed; backend content and audit receipts remain)",
        }

    if action == "reveal":
        import hashlib

        from memorycore.jsonl_adapter import jsonl_get, memory_id_from_pointer
        from memorycore.mcp_surface import _jsonl_store_path

        record_id = str(payload.get("record_id", ""))
        store = CacheStore(cache_db)
        try:
            record = store.get(record_id)
        finally:
            store.close()
        if record is None:
            return {"status": "error", "message": f"no such record: {record_id}"}

        backend_id = record["source_pointer"].get("backend_id")
        content: str | None = None
        note = ""
        if backend_id == "jsonl_store":
            line = jsonl_get(_jsonl_store_path(), memory_id_from_pointer(record["source_pointer"].get("pointer_id", "")))
            if line is None:
                return {"status": "error", "message": "content not found in jsonl store (missing)"}
            content = line.get("content", "")
        elif backend_id == "qmd":
            source_uri = record["source_pointer"].get("source_uri", "")
            source = Path(source_uri).expanduser() if source_uri and not source_uri.startswith("qmd://") else None
            if source is None or not source.exists():
                return {"status": "error", "message": "source file not found on disk (missing or fixture pointer)"}
            content = source.read_text(encoding="utf-8")
            note = "hash covers the full materialized file (frontmatter + content)"
        else:
            return {"status": "error", "message": f"reveal not supported for backend {backend_id} yet"}

        computed = hashlib.sha256(content.encode("utf-8")).hexdigest()
        stored = record.get("content_hash") or ""
        hash_match = (computed == stored) if stored else None

        audit = build_audit_record(
            {"request_id": "req_operator_ui_reveal", "client_surface": "operator_ui", "operation": "content_access"},
            {"status": "ok", "results": [{"pointer": record["source_pointer"], "verification_state": record["verification"]}]},
            timestamp=_now(),
        )
        audit["config_change"] = {"action": "reveal", "record_id": record_id, "hash_match": hash_match}
        append_record(audit_log, audit)
        return {
            "status": "ok",
            "record_id": record_id,
            "backend_id": backend_id,
            "content": content,
            "stored_hash": stored,
            "computed_hash": computed,
            "hash_match": hash_match,
            "note": note,
        }

    if action == "declare":
        import re

        from memorycore.operator_config import BACKEND_CLASSES

        backend_id = str(payload.get("backend_id", "")).strip()
        display_name = str(payload.get("display_name", "")).strip() or backend_id
        backend_class = str(payload.get("class", "")).strip()
        if not re.fullmatch(r"[a-z][a-z0-9_]{1,31}", backend_id):
            return {"status": "error", "message": "backend id must be a lowercase slug (a-z, 0-9, _)"}
        if backend_class not in BACKEND_CLASSES:
            return {"status": "error", "message": f"class must be one of: {', '.join(BACKEND_CLASSES)}"}
        config = load_config(config_path)
        if backend_id in config["backends"]:
            return {"status": "error", "message": f"backend already declared: {backend_id}"}

        def mutate(cfg: dict[str, Any]) -> None:
            cfg["backends"][backend_id] = {"enabled": False, "class": backend_class, "display_name": display_name}

        apply_config_change(
            config_path, audit_log, action="declare_backend",
            detail={"backend_id": backend_id, "class": backend_class}, mutate=mutate,
        )
        return {"status": "ok", "message": f"declared {backend_id} ({backend_class}) — starts disabled"}

    if action == "pack":
        import hashlib as _hashlib
        import json as _json

        record_id = str(payload.get("record_id", ""))
        store = CacheStore(cache_db)
        try:
            record = store.get(record_id)
        finally:
            store.close()
        if record is None:
            return {"status": "error", "message": f"no such record: {record_id}"}
        related = [
            entry for entry in (read_recent(audit_log, limit=500) if audit_log.exists() else [])
            if record["content_ref"] in entry.get("pointer_ids", [])
            or record["source_pointer"].get("pointer_id") in entry.get("pointer_ids", [])
        ]
        body = {"record": record, "related_audit": related, "generated_at": _now(), "content_sparse": True}
        integrity = _hashlib.sha256(_json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        lines = [
            "# Engram evidence pack",
            f"Generated {body['generated_at']} — content-sparse (pointers and hashes only).",
            "",
            f"Record `{record['record_id']}` — {record['memory_type']} via {record['source_pointer'].get('backend_id')}",
            f"Pointer: `{record['content_ref']}`",
            f"Content hash: `{record.get('content_hash') or '(none)'}`",
            f"State: {record['verification']} / {record['flush_state']}",
            f"Created {record['created_at']} · updated {record['updated_at']}",
            "",
            f"## Audit entries ({len(related)})",
            *[f"- {e['timestamp']} {e['operation']} {e['verification_state']} `{e['audit_id']}`" for e in related],
            "",
            f"Pack integrity: sha256 `{integrity}`",
        ]
        audit = build_audit_record(
            {"request_id": "req_operator_ui_pack", "client_surface": "operator_ui", "operation": "pack_export"},
            {"status": "ok", "results": [{"pointer": record["source_pointer"], "verification_state": record["verification"]}]},
            timestamp=_now(),
        )
        audit["config_change"] = {"action": "pack_export", "record_id": record_id, "audit_entries": len(related)}
        append_record(audit_log, audit)
        return {"status": "ok", "pack": body, "integrity": integrity, "human_readable": "\n".join(lines)}

    if action == "reset_config":
        from memorycore.operator_config import DEFAULT_CONFIG, INSTALLED_ADAPTERS

        preserved: list[str] = []

        def mutate(cfg: dict[str, Any]) -> None:
            for backend_id, entry in cfg["backends"].items():
                entry["enabled"] = backend_id in INSTALLED_ADAPTERS
                if backend_id not in INSTALLED_ADAPTERS:
                    preserved.append(backend_id)
            cfg["routing"] = {k: list(v) for k, v in DEFAULT_CONFIG["routing"].items()}
            cfg["mode"] = DEFAULT_CONFIG["mode"]

        apply_config_change(
            config_path, audit_log, action="config_reset",
            detail={"preserved_declared": preserved}, mutate=mutate,
        )
        note = f"; declared future backends preserved disabled: {', '.join(preserved)}" if preserved else ""
        return {"status": "ok", "message": f"config reset to defaults (mode fixture, installed backends enabled, default routing){note}"}

    return {"status": "error", "message": f"unknown control action: {action}"}


def content_search_matches(cache_db: Path, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
    """GAP-010: content matches for the table search, live server only.

    Snippets are response-only (never persisted); pointers link matches back
    to cache records so the table can merge them with attribution.
    """
    from memorycore.cache_router import CacheStore
    from memorycore.jsonl_adapter import jsonl_search, store_pointer
    from memorycore.mcp_surface import _jsonl_store_path

    if not query or len(query) < 3:
        return []
    matches = []
    store = CacheStore(cache_db)
    try:
        for hit in jsonl_search(_jsonl_store_path(), query, limit=limit):
            pointer = store_pointer(hit["memory_id"])
            record = store.find_by_pointer(pointer["pointer_id"])
            matches.append(
                {
                    "record_id": record["record_id"] if record else None,
                    "pointer_id": pointer["pointer_id"],
                    "snippet": hit.get("content", "")[:160],
                }
            )
    finally:
        store.close()
    return matches


def render_html(data: dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True).replace("</", "<\\/")
    return _TEMPLATE.replace("__ENGRAM_DATA__", payload)


def write_viewer(cache_db: Path, audit_log: Path, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(collect_viewer_data(cache_db, audit_log)), encoding="utf-8")
    return output


def serve_viewer(cache_db: Path, audit_log: Path, *, port: int = 8787, host: str = "127.0.0.1") -> None:
    """Serve the dashboard live, regenerated per request.

    Loopback-only by default: the receipts surface is a local operator
    console, never a network service. Binding another host (e.g. 0.0.0.0
    for a local browser-automation container) is a deliberate operator
    choice via --host; control actions stay gated by the custom header
    either way. GET / renders fresh HTML; the page polls GET /data.json
    every few seconds so state changes appear live.
    """
    import http.server
    import json as _json

    from memorycore.cli import operator_config_path

    config_path = operator_config_path()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - http.server API
            route = self.path.split("?")[0]
            if route == "/data.json":
                body = _json.dumps(collect_viewer_data(cache_db, audit_log)).encode("utf-8")
                ctype = "application/json"
            elif route == "/content-search.json":
                if self.headers.get("X-MemoryCore-Control") != "1":
                    self._respond(403, b'{"error":"forbidden"}', "application/json")
                    return
                from urllib.parse import parse_qs, urlparse

                query = parse_qs(urlparse(self.path).query).get("q", [""])[0]
                body = _json.dumps({"matches": content_search_matches(cache_db, query)}).encode("utf-8")
                ctype = "application/json"
            else:
                body = render_html(collect_viewer_data(cache_db, audit_log)).encode("utf-8")
                ctype = "text/html; charset=utf-8"
            self._respond(200, body, ctype)

        def do_POST(self) -> None:  # noqa: N802 - http.server API
            # Same-origin fetches set this header; cross-origin pages cannot
            # without a CORS preflight we never approve. Loopback + header is
            # the control surface's whole trust model.
            if self.path.split("?")[0] != "/control" or self.headers.get("X-MemoryCore-Control") != "1":
                self._respond(403, b'{"status":"error","message":"forbidden"}', "application/json")
                return
            length = int(self.headers.get("Content-Length", "0"))
            try:
                payload = _json.loads(self.rfile.read(length) or b"{}")
                result = handle_control(
                    str(payload.get("action", "")), payload,
                    cache_db=cache_db, audit_log=audit_log, config_path=config_path,
                )
            except (ValueError, KeyError) as exc:
                result = {"status": "error", "message": str(exc)}
            self._respond(200, _json.dumps(result).encode("utf-8"), "application/json")

        def _respond(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: Any) -> None:  # quiet by default
            pass

    server = http.server.ThreadingHTTPServer((host, port), Handler)
    print(f"Engram receipts live at http://{host}:{port} (Ctrl-C to stop)")
    server.serve_forever()


_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Engram — Memory Receipts</title>
<style>
  :root {
    color-scheme: light;
    --page: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e;
    --muted: #898781; --grid: #e1e0d9; --baseline: #c3c2b7;
    --ring: rgba(11,11,11,0.10);
    --good: #0ca30c; --warning: #fab219; --serious: #ec835a; --critical: #d03b3b;
    --s1: #2a78d6; --s2: #008300; --s3: #e87ba4; --s4: #eda100;
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) {
      color-scheme: dark;
      --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7;
      --muted: #898781; --grid: #2c2c2a; --baseline: #383835;
      --ring: rgba(255,255,255,0.10);
      --s1: #3987e5; --s2: #008300; --s3: #d55181; --s4: #c98500;
    }
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7;
    --muted: #898781; --grid: #2c2c2a; --baseline: #383835;
    --ring: rgba(255,255,255,0.10);
    --s1: #3987e5; --s2: #008300; --s3: #d55181; --s4: #c98500;
  }
  * { box-sizing: border-box; margin: 0; }
  body {
    background: var(--page); color: var(--ink);
    font: 14px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
    padding: 28px clamp(16px, 4vw, 48px) 64px;
  }
  header { margin-bottom: 24px; }
  header h1 { font-size: 22px; font-weight: 650; letter-spacing: -0.01em; }
  header .sub { color: var(--ink-2); margin-top: 4px; font-size: 13px; }
  header .sub code { color: var(--muted); font-size: 12px; }
  .theme-toggle {
    float: right; background: var(--surface); color: var(--ink-2);
    border: 1px solid var(--ring); border-radius: 8px; padding: 6px 12px;
    cursor: pointer; font: inherit; font-size: 13px;
  }
  .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 20px; }
  .tile {
    background: var(--surface); border: 1px solid var(--ring); border-radius: 12px;
    padding: 14px 16px;
  }
  .tile .label { color: var(--ink-2); font-size: 12px; display: flex; align-items: center; gap: 6px; }
  .tile .value { font-size: 28px; font-weight: 650; margin-top: 2px; }
  .dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; flex: none; }
  section { background: var(--surface); border: 1px solid var(--ring); border-radius: 12px; padding: 18px 20px; margin-bottom: 16px; }
  section h2 { font-size: 14px; font-weight: 650; margin-bottom: 12px; color: var(--ink); }
  .stackbar { display: flex; height: 26px; border-radius: 4px; overflow: hidden; gap: 2px; background: var(--page); }
  .stackbar .seg { min-width: 3px; transition: opacity .15s; }
  .stackbar .seg:hover { opacity: .82; }
  .legend { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 10px; font-size: 12.5px; color: var(--ink-2); }
  .legend .item { display: flex; align-items: center; gap: 6px; }
  .badge {
    display: inline-flex; align-items: center; gap: 5px; padding: 2px 9px 2px 7px;
    border-radius: 999px; font-size: 12px; font-weight: 600; border: 1px solid var(--ring);
    color: var(--ink); background: var(--page); white-space: nowrap;
  }
  .badge .ic { font-size: 11px; }
  .bars .row { display: grid; grid-template-columns: 130px 1fr 44px; align-items: center; gap: 10px; margin: 7px 0; }
  .bars .name { font-size: 13px; color: var(--ink-2); display: flex; gap: 7px; align-items: center; }
  .bars .track { height: 18px; background: var(--page); border-radius: 4px; }
  .bars .fill { height: 100%; border-radius: 4px 4px 4px 4px; min-width: 2px; }
  .bars .n { font-variant-numeric: tabular-nums; color: var(--ink-2); font-size: 13px; text-align: right; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; color: var(--muted); font-weight: 600; font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; padding: 6px 10px; border-bottom: 1px solid var(--grid); }
  td { padding: 8px 10px; border-bottom: 1px solid var(--grid); vertical-align: top; font-variant-numeric: tabular-nums; }
  tr.mem { cursor: pointer; }
  tr.mem:hover td { background: color-mix(in srgb, var(--ink) 4%, transparent); }
  code, .mono { font-family: ui-monospace, "Cascadia Mono", Menlo, monospace; font-size: 12px; }
  .ptr { color: var(--ink-2); max-width: 340px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: inline-block; vertical-align: bottom; }
  tr.detail td { background: color-mix(in srgb, var(--ink) 3%, transparent); padding: 14px 16px; }
  .detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }
  .detail-grid h3 { font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); margin-bottom: 6px; }
  .detail-grid pre { background: var(--page); border: 1px solid var(--ring); border-radius: 8px; padding: 10px 12px; font-size: 11.5px; overflow-x: auto; color: var(--ink-2); }
  .audit-row { display: grid; grid-template-columns: 158px 90px 110px 1fr 150px; gap: 10px; padding: 7px 4px; border-bottom: 1px solid var(--grid); font-size: 12.5px; align-items: baseline; }
  .audit-row .t { color: var(--muted); font-variant-numeric: tabular-nums; }
  .audit-row:last-child { border-bottom: none; }
  .empty { color: var(--muted); font-style: italic; padding: 12px 4px; }
  footer { color: var(--muted); font-size: 12px; margin-top: 24px; }
  .filters { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; align-items: center; }
  .filters input[type=text], .filters select, .declare input, .declare select {
    font: inherit; font-size: 12.5px; padding: 5px 10px; border: 1px solid var(--ring);
    border-radius: 8px; background: var(--page); color: var(--ink);
  }
  .filters .count { font-size: 12px; color: var(--muted); margin-left: auto; }
  .trend-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }
  .trend-grid h3 { font-size: 12px; color: var(--ink-2); font-weight: 600; margin-bottom: 6px; }
  .trend-grid svg { display: block; width: 100%; height: 72px; }
  .hashcmp { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin: 8px 0; font-size: 12px; }
  .revealpane pre.content { max-height: 260px; overflow: auto; white-space: pre-wrap; }
  .cfg-row { display: grid; grid-template-columns: 158px 130px 1fr; gap: 10px; padding: 6px 4px; border-bottom: 1px solid var(--grid); font-size: 12.5px; }
  .cfg-row:last-child { border-bottom: none; }
  .declare { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 10px; }
  .ctl-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; }
  .bk-card { border: 1px solid var(--ring); border-radius: 10px; padding: 12px 14px; background: var(--page); }
  .bk-card.future { border-style: dashed; opacity: .75; }
  .bk-card .top { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
  .bk-card .name { font-weight: 650; font-size: 13.5px; flex: 1; }
  .bk-card .cls { font-size: 10.5px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }
  .bk-card .caps { font-size: 11.5px; color: var(--muted); margin: 4px 0 10px; }
  .bk-card .desc { font-size: 11.5px; color: var(--ink-2); margin: 6px 0 2px; line-height: 1.45; }
  .bk-card a.doc { font-size: 11.5px; color: var(--s1); text-decoration: none; }
  .bk-card a.doc:hover { text-decoration: underline; }
  [data-help] { cursor: help; }
  .reserved-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 10px; margin-top: 10px; }
  .toggle {
    font: inherit; font-size: 12px; font-weight: 600; padding: 4px 12px; border-radius: 999px;
    border: 1px solid var(--ring); cursor: pointer; background: var(--surface); color: var(--ink);
  }
  .toggle.on { border-color: var(--good); color: var(--good); }
  .toggle.off { color: var(--muted); }
  .toggle:disabled { opacity: .45; cursor: not-allowed; }
  .seg { display: inline-flex; border: 1px solid var(--ring); border-radius: 8px; overflow: hidden; }
  .seg button { font: inherit; font-size: 12.5px; padding: 5px 14px; border: none; background: var(--page); color: var(--ink-2); cursor: pointer; }
  .seg button.active { background: var(--surface); color: var(--ink); font-weight: 650; }
  .seg button:disabled { cursor: not-allowed; opacity: .55; }
  .matrix td, .matrix th { text-align: center; }
  .matrix td:first-child, .matrix th:first-child { text-align: left; }
  .matrix input[type=checkbox] { width: 15px; height: 15px; accent-color: var(--s1); cursor: pointer; }
  .matrix input[type=checkbox]:disabled { cursor: not-allowed; }
  .ctl-actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
  .btn {
    font: inherit; font-size: 13px; font-weight: 600; padding: 7px 16px; border-radius: 8px;
    border: 1px solid var(--ring); background: var(--page); color: var(--ink); cursor: pointer;
  }
  .btn:hover { background: color-mix(in srgb, var(--ink) 6%, var(--page)); }
  .btn:disabled { opacity: .45; cursor: not-allowed; }
  .btn.danger { color: var(--critical); }
  .ctl-note { font-size: 12px; color: var(--muted); margin-top: 10px; }
  .reserved { font-size: 12px; color: var(--muted); margin-top: 12px; font-style: italic; }
  #toast {
    position: fixed; bottom: 22px; left: 50%; transform: translateX(-50%); z-index: 20;
    background: var(--surface); color: var(--ink); border: 1px solid var(--ring); border-radius: 10px;
    padding: 9px 16px; font-size: 13px; box-shadow: 0 6px 24px rgba(0,0,0,.22); opacity: 0;
    transition: opacity .2s; pointer-events: none; max-width: 80vw;
  }
  #tip {
    position: fixed; pointer-events: none; background: var(--surface); color: var(--ink);
    border: 1px solid var(--ring); border-radius: 8px; padding: 6px 10px; font-size: 12.5px;
    box-shadow: 0 4px 16px rgba(0,0,0,.18); opacity: 0; transition: opacity .1s; z-index: 10;
  }
</style>
</head>
<body>
<div id="tip"></div>
<header>
  <button class="theme-toggle" onclick="toggleTheme()">◐ theme</button>
  <h1>Engram — Memory Receipts</h1>
  <div class="sub">Every memory, its provenance pointer, and whether it can still be trusted.
    <span id="gen"></span></div>
</header>
<div class="tiles" id="tiles"></div>
<section id="controlplane" style="display:none">
  <h2 data-help="Live, audited controls over the memory layer: enable or disable backends, edit routing, switch modes. Every change writes a receipt.">Control plane <span style="color:var(--muted);font-weight:400">— every change leaves a receipt in the audit trail</span></h2>
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;flex-wrap:wrap">
    <span style="font-size:12.5px;color:var(--ink-2)">Backend mode</span>
    <span class="seg" id="modeseg"></span>
    <span id="modenote" style="font-size:12px;color:var(--muted)"></span>
  </div>
  <div class="ctl-grid" id="bkcards"></div>
  <div class="reserved" id="reserved"></div>
  <h2 style="margin-top:18px" data-help="Which backends each memory type flushes to. Check two boxes on one row to mirror a type into two systems at once.">Routing matrix <span style="color:var(--muted);font-weight:400">— pointer flush targets; two checks on one row = mirroring</span></h2>
  <div style="overflow-x:auto"><table class="matrix" id="matrix"></table></div>
  <div class="ctl-note">Content write-through targets are fixed per type (local → JSONL, file_corpus → QMD, transcript → callback delivery); the matrix governs where pointer records flush.</div>
  <div class="ctl-actions" style="margin-top:14px">
    <button class="btn" id="btn-flush">Flush pending</button>
    <button class="btn" id="btn-verify">Re-verify all stamps</button>
    <button class="btn" id="btn-reset" data-help="Escape hatch for half-applied changes: restores mode, backend enablement, and routing to installed defaults. Declared future backends are preserved (disabled). Audited like every control.">Reset to defaults</button>
  </div>
  <div class="declare" id="declare"></div>
  <h2 style="margin-top:18px" data-help="The settings' own audit trail: every toggle, routing edit, mode switch, reveal, and export, attributed and timestamped.">Configuration history <span style="color:var(--muted);font-weight:400">— who changed what, when</span></h2>
  <div id="cfghistory"></div>
</section>
<section>
  <h2 data-help="How the memory layer is being used over time, from record timestamps and the audit trail.">Activity</h2>
  <div class="trend-grid">
    <div><h3 id="trend-mem-h">Memories over time</h3><div id="trend-mem"></div></div>
    <div><h3 id="trend-audit-h">Audit events per day</h3><div id="trend-audit"></div></div>
  </div>
</section>
<div id="toast"></div>
<section>
  <h2 data-help="Trust at a glance: verified = proven against source; stale = source changed since; missing = source gone; unknown = not yet provable. Never asserted, always checked.">Verification states</h2>
  <div class="stackbar" id="stackbar"></div>
  <div class="legend" id="vlegend"></div>
</section>
<section>
  <h2 data-help="Where memories physically live. Each backend is a different memory technology behind one contract.">Memories by backend</h2>
  <div class="bars" id="backendbars"></div>
</section>
<section>
  <h2 data-help="Every memory the cache knows: its pointer, hash, verification stamp, and delivery state. Click a row for the full receipt.">Memory records <span style="color:var(--muted);font-weight:400">— click a row for its receipt</span></h2>
  <div class="filters">
    <input type="text" id="mf-text" placeholder="search ids, pointers — and content when live…" oninput="memSearchInput()">
    <select id="mf-state" onchange="renderAll()"></select>
    <select id="mf-backend" onchange="renderAll()"></select>
    <select id="mf-type" onchange="renderAll()"></select>
    <span class="count" id="mf-count"></span>
  </div>
  <table id="memtable">
    <thead><tr><th>Record</th><th>Type</th><th>Backend</th><th>Pointer</th><th>Verification</th><th>Delivery</th><th>Updated</th></tr></thead>
    <tbody></tbody>
  </table>
</section>
<section>
  <h2 data-help="Receipts for every operation — searches, writes, verifications, reveals, config changes. Content-sparse: pointers and hashes, never memory content.">Audit trail <span style="color:var(--muted);font-weight:400">— newest first, content-sparse by contract</span></h2>
  <div class="filters">
    <input type="text" id="af-text" placeholder="search audit…" oninput="renderAll()">
    <select id="af-op" onchange="renderAll()"></select>
    <select id="af-client" onchange="renderAll()"></select>
    <select id="af-backend" onchange="renderAll()"></select>
    <span class="count" id="af-count"></span>
  </div>
  <div id="audit"></div>
</section>
<footer id="foot"></footer>
<script>
let DATA = __ENGRAM_DATA__;
const V = {
  verified:   { color: "var(--good)",     ic: "✓", label: "verified" },
  stale:      { color: "var(--warning)",  ic: "⚠", label: "stale" },
  missing:    { color: "var(--serious)",  ic: "✕", label: "missing" },
  unsupported:{ color: "var(--critical)", ic: "⊘", label: "unsupported" },
  unknown:    { color: "var(--muted)",    ic: "?", label: "unknown" },
};
const BACKEND_SLOT = { qmd: "var(--s1)", lossless_claw: "var(--s2)", jsonl_store: "var(--s3)", gbrain: "var(--s4)" };
const backendColor = b => BACKEND_SLOT[b] || "var(--muted)";
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const badge = state => { const v = V[state] || V.unknown;
  return `<span class="badge"><span class="ic" style="color:${v.color}">${v.ic}</span>${v.label}</span>`; };

const tip = document.getElementById("tip");
function showTip(e, html) { tip.innerHTML = html; tip.style.opacity = 1;
  tip.style.left = Math.min(e.clientX + 14, innerWidth - 220) + "px"; tip.style.top = (e.clientY + 14) + "px"; }
function hideTip() { tip.style.opacity = 0; }

let records = [];
let openRecordId = null;
const revealCache = {};
function renderAll() {
document.getElementById("gen").textContent = "Generated " + DATA.generated_at + (LIVE ? " · live" : " · snapshot");
document.getElementById("foot").textContent =
  `cache: ${DATA.cache_db} · audit: ${DATA.audit_log} · local-first, content-sparse — pointers and hashes only, never memory content`;

const vc = DATA.verification_counts; records = DATA.records; const total = records.length;
const STATE_HELP = {
  verified: "Proven against the source: the content exists and its hash matches the receipt. Earned by a real check, never asserted.",
  stale: "The source changed after this memory was recorded — its content no longer matches the stored hash. The memory may be outdated.",
  missing: "The source is gone: the file or record this memory points to no longer exists. The pointer is honest about it.",
  unsupported: "This backend cannot prove freshness for this record (yet). MemoryCore says so rather than guessing.",
  unknown: "Not yet provable — the backend was unreachable or no check has run. Never presented as verified.",
};
const tiles = [
  { label: "memories", value: total, dot: null, help: "Every memory record the cache knows about, across all backends." },
  { label: "verified", value: vc.verified || 0, dot: "var(--good)", help: STATE_HELP.verified },
  { label: "stale", value: vc.stale || 0, dot: "var(--warning)", help: STATE_HELP.stale },
  { label: "missing", value: vc.missing || 0, dot: "var(--serious)", help: STATE_HELP.missing },
  { label: "unknown", value: (vc.unknown || 0) + (vc.unsupported || 0), dot: "var(--muted)", help: STATE_HELP.unknown + " Includes unsupported." },
  { label: "audit events", value: DATA.audit.length, dot: null, help: "Receipts in the trail: one per operation — searches, writes, verifications, reveals, config changes." },
];
document.getElementById("tiles").innerHTML = tiles.map(t =>
  `<div class="tile" data-help="${esc(t.help)}"><div class="label">${t.dot ? `<span class="dot" style="background:${t.dot}"></span>` : ""}${t.label}</div>
   <div class="value">${t.value}</div></div>`).join("");

const sb = document.getElementById("stackbar");
const order = ["verified","stale","missing","unsupported","unknown"];
sb.innerHTML = total === 0 ? '<div class="empty">no memories yet</div>' :
  order.filter(s => vc[s]).map(s =>
    `<div class="seg" data-s="${s}" style="flex:${vc[s]};background:${V[s].color}"></div>`).join("");
sb.querySelectorAll(".seg").forEach(el => {
  el.onmousemove = e => { const s = el.dataset.s;
    showTip(e, `${V[s].ic} <b>${V[s].label}</b> — ${vc[s]} of ${total} (${Math.round(100*vc[s]/total)}%)`); };
  el.onmouseleave = hideTip;
});
document.getElementById("vlegend").innerHTML = order.map(s =>
  `<span class="item" data-help="${esc(STATE_HELP[s])}"><span class="dot" style="background:${V[s].color}"></span>${V[s].ic} ${s} · ${vc[s] || 0}</span>`).join("");

const bc = DATA.backend_counts, maxB = Math.max(1, ...Object.values(bc));
document.getElementById("backendbars").innerHTML = Object.keys(bc).length === 0 ?
  '<div class="empty">no routed memories yet</div>' :
  Object.entries(bc).sort((a,b) => b[1]-a[1]).map(([b, n]) =>
    `<div class="row"><span class="name"><span class="dot" style="background:${backendColor(b)}"></span>${esc(b)}</span>
     <div class="track"><div class="fill" data-b="${esc(b)}" data-n="${n}" style="width:${Math.round(100*n/maxB)}%;background:${backendColor(b)}"></div></div>
     <span class="n">${n}</span></div>`).join("");
document.querySelectorAll(".fill").forEach(el => {
  el.onmousemove = e => showTip(e, `<b>${el.dataset.b}</b> — ${el.dataset.n} memor${el.dataset.n==1?"y":"ies"}`);
  el.onmouseleave = hideTip;
});

syncSelect("mf-state", "all states", records.map(r => r.verification));
syncSelect("mf-backend", "all backends", records.map(r => r.source_pointer.backend_id || "unrouted"));
syncSelect("mf-type", "all types", records.map(r => r.memory_type));
const mfText = (document.getElementById("mf-text").value || "").toLowerCase();
const mfState = document.getElementById("mf-state").value;
const mfBackend = document.getElementById("mf-backend").value;
const mfType = document.getElementById("mf-type").value;
const visible = records.map((r, i) => [r, i]).filter(([r]) => {
  const b = r.source_pointer.backend_id || "unrouted";
  if (mfState && r.verification !== mfState) return false;
  if (mfBackend && b !== mfBackend) return false;
  if (mfType && r.memory_type !== mfType) return false;
  if (mfText) {
    const idMatch = (r.record_id + " " + r.content_ref + " " + r.memory_type).toLowerCase().includes(mfText);
    if (!idMatch && !contentMatches[r.record_id]) return false;
  }
  return true;
});
document.getElementById("mf-count").textContent = `${visible.length} of ${records.length}`;
const emptyMsg = !mfText ? "no records match the filters" :
  LIVE ? "no matches across ids, pointers, or memory content" :
  "no id/pointer matches — content search requires the live console";
const tbody = document.querySelector("#memtable tbody");
tbody.innerHTML = records.length === 0 ? '<tr><td colspan="7" class="empty">cache is empty</td></tr>' :
  visible.length === 0 ? `<tr><td colspan="7" class="empty">${emptyMsg}</td></tr>` :
  visible.map(([r, i]) => {
    const b = r.source_pointer.backend_id || "unrouted";
    const cm = contentMatches[r.record_id];
    return `<tr class="mem" data-i="${i}"${cm ? ` title="content match: ${esc(cm)}"` : ""}>
      <td class="mono">${esc(r.record_id.slice(0, 18))}…${cm ? ' <span class="badge" style="font-size:10px;padding:1px 7px">content</span>' : ""}</td>
      <td>${esc(r.memory_type)}</td>
      <td><span class="dot" style="background:${backendColor(b)}"></span> ${esc(b)}</td>
      <td><span class="ptr mono" title="${esc(r.content_ref)}">${esc(r.content_ref)}</span></td>
      <td>${badge(r.verification)}</td>
      <td>${esc(r.flush_state)}</td>
      <td>${esc((r.updated_at || "").replace("T", " ").replace("Z", ""))}</td></tr>`;
  }).join("");

syncSelect("af-op", "all operations", DATA.audit.map(a => a.operation));
syncSelect("af-client", "all clients", DATA.audit.map(a => a.client_surface));
syncSelect("af-backend", "all backends", DATA.audit.map(a => a.selected_backend || "—"));
const afText = (document.getElementById("af-text").value || "").toLowerCase();
const afOp = document.getElementById("af-op").value;
const afClient = document.getElementById("af-client").value;
const afBackend = document.getElementById("af-backend").value;
const auditVisible = DATA.audit.filter(a => {
  if (afOp && a.operation !== afOp) return false;
  if (afClient && a.client_surface !== afClient) return false;
  if (afBackend && (a.selected_backend || "—") !== afBackend) return false;
  if (afText && !JSON.stringify(a).toLowerCase().includes(afText)) return false;
  return true;
});
document.getElementById("af-count").textContent = `${auditVisible.length} of ${DATA.audit.length}`;
document.getElementById("audit").innerHTML = DATA.audit.length === 0 ?
  '<div class="empty">no audit events</div>' :
  auditVisible.length === 0 ? '<div class="empty">no events match the filters</div>' :
  auditVisible.slice(0, 200).map(a => `<div class="audit-row">
    <span class="t mono">${esc((a.timestamp || "").replace("T", " ").replace("Z", ""))}</span>
    <span>${esc(a.operation)}</span>
    <span><span class="dot" style="background:${backendColor(a.selected_backend)}"></span> ${esc(a.selected_backend || "—")}</span>
    <span>${badge(a.verification_state)} ${a.status === "error" ? `<span class="badge"><span class="ic" style="color:var(--critical)">⊘</span>${esc((a.error_state||{}).code || "error")}</span>` : ""}</span>
    <span class="mono" style="color:var(--muted)">${esc(a.audit_id)}</span>
  </div>`).join("");

renderControl();
renderTrends();
document.querySelectorAll("tr.detail").forEach(d => d.remove());
restoreOpenDetail();
bindHelp();
}

function bindHelp() {
  document.querySelectorAll("[data-help]").forEach(el => {
    if (el._helpBound) return;
    el._helpBound = true;
    el.addEventListener("mousemove", e => showTip(e, esc(el.dataset.help)));
    el.addEventListener("mouseleave", hideTip);
  });
}

function syncSelect(id, allLabel, values) {
  const el = document.getElementById(id);
  const current = el.value;
  const opts = [...new Set(values)].sort();
  el.innerHTML = `<option value="">${allLabel}</option>` +
    opts.map(v => `<option value="${esc(v)}"${v === current ? " selected" : ""}>${esc(v)}</option>`).join("");
}

function sparkSvg(points, kind) {
  if (points.length === 0) return '<div class="empty">no data</div>';
  const W = 320, H = 72, pad = 4;
  const max = Math.max(...points.map(p => p.v), 1);
  const step = (W - pad * 2) / Math.max(points.length, 1);
  let marks = "";
  if (kind === "bars") {
    marks = points.map((p, i) => {
      const h = Math.max(2, (H - pad * 2) * p.v / max);
      return `<rect x="${(pad + i * step + 1).toFixed(1)}" y="${(H - pad - h).toFixed(1)}" width="${Math.max(2, step - 2).toFixed(1)}" height="${h.toFixed(1)}" rx="2" fill="var(--s1)" data-k="${esc(p.k)}" data-v="${p.v}"/>`;
    }).join("");
  } else {
    const xy = points.map((p, i) => `${(pad + i * step + step / 2).toFixed(1)},${(H - pad - (H - pad * 2) * p.v / max).toFixed(1)}`);
    const last = xy[xy.length - 1].split(",");
    marks = `<polyline points="${xy.join(" ")}" fill="none" stroke="var(--s1)" stroke-width="2" stroke-linejoin="round"/>` +
      `<circle cx="${last[0]}" cy="${last[1]}" r="3.5" fill="var(--s1)"/>`;
  }
  return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
    <line x1="${pad}" y1="${H - pad}" x2="${W - pad}" y2="${H - pad}" stroke="var(--baseline)" stroke-width="1"/>
    ${marks}</svg>`;
}

function byDay(timestamps) {
  const days = {};
  timestamps.forEach(t => { const d = (t || "").slice(0, 10); if (d) days[d] = (days[d] || 0) + 1; });
  return Object.keys(days).sort().map(k => ({ k, v: days[k] }));
}

function renderTrends() {
  const created = DATA.records.map(r => r.created_at).sort();
  let total = 0;
  const cumulative = byDay(created).map(p => ({ k: p.k, v: (total += p.v) }));
  document.getElementById("trend-mem").innerHTML = sparkSvg(cumulative, "line");
  document.getElementById("trend-mem-h").textContent = `Memories over time — ${DATA.records.length} total`;
  const perDay = byDay(DATA.audit.map(a => a.timestamp));
  document.getElementById("trend-audit").innerHTML = sparkSvg(perDay, "bars");
  document.getElementById("trend-audit-h").textContent = `Audit events per day — ${DATA.audit.length} in window`;
  document.querySelectorAll("#trend-audit rect").forEach(el => {
    el.onmousemove = e => showTip(e, `<b>${el.dataset.k}</b> — ${el.dataset.v} event(s)`);
    el.onmouseleave = hideTip;
  });
}

function renderControl() {
  const c = DATA.control;
  const sec = document.getElementById("controlplane");
  if (!c) { sec.style.display = "none"; return; }
  sec.style.display = "";

  const envPinned = c.mode_source === "env";
  const MODE_HELP = {
    fixture: "Safe default: reads answer from synthetic fixture data; no live backend commands run. Contract behavior only.",
    "live-local": "Real mode: QMD reads/writes/verification run against the actual local index. Still local-only — nothing leaves this machine.",
  };
  document.getElementById("modeseg").innerHTML = ["fixture", "live-local"].map(m =>
    `<button class="${m === c.mode ? "active" : ""}" ${(!LIVE || envPinned) ? "disabled" : ""}
      data-help="${esc(MODE_HELP[m])}" onclick="control('mode',{mode:'${m}'})">${m}</button>`).join("");
  document.getElementById("modenote").textContent =
    envPinned ? "pinned by MEMORYCORE_BACKEND_MODE env" : (LIVE ? "" : "controls require the live server");

  document.getElementById("bkcards").innerHTML = c.backends.map(b => `
    <div class="bk-card ${b.adapter_installed ? "" : "future"}">
      <div class="top">
        <span class="dot" style="background:${b.enabled && b.adapter_installed ? backendColor(b.backend_id) : "var(--muted)"}"></span>
        <span class="name">${esc(b.display_name)}</span>
        <span class="cls" data-help="${esc(c.class_info[b.class] || b.class)}">${esc(b.class)}</span>
      </div>
      <div class="desc">${esc(b.description || "")}</div>
      <div class="caps">${b.adapter_installed
        ? `verify: ${esc(String(b.capabilities.verify))} · content search: ${b.capabilities.content_search ? "yes" : "no"}`
        : "declared — no adapter installed"}</div>
      <div style="display:flex;align-items:center;gap:10px">
        <button class="toggle ${b.enabled ? "on" : "off"}" ${!LIVE ? "disabled" : ""}
          data-help="${b.enabled ? "Disable: writes to this backend fail with an honest BACKEND_DISABLED error. The toggle itself is receipted." : "Enable this backend for routing and writes. The toggle itself is receipted."}"
          onclick="control('backend',{backend_id:'${esc(b.backend_id)}',enabled:${!b.enabled}})">
          ${b.enabled ? "enabled" : "disabled"}</button>
        ${b.url ? `<a class="doc" href="${esc(b.url)}" target="_blank" rel="noopener">docs ↗</a>` : ""}
      </div>
    </div>`).join("");

  document.getElementById("reserved").innerHTML =
    `<div style="font-style:normal">Reserved for future memory systems — declare an entry below to populate:</div>
     <div class="reserved-grid">${c.reserved_classes.map(cls => `
       <div class="bk-card future"><div class="top"><span class="dot" style="background:var(--muted)"></span>
         <span class="name" style="font-weight:600">${esc(cls)}</span></div>
         <div class="desc">${esc((c.class_info[cls] || "").replace("Reserved: ", ""))}</div></div>`).join("")}</div>`;

  // Preserve in-progress form input across live re-renders.
  const decPrev = {
    id: document.getElementById("dec-id")?.value || "",
    name: document.getElementById("dec-name")?.value || "",
    cls: document.getElementById("dec-class")?.value || "",
  };
  document.getElementById("declare").innerHTML = `
    <input type="text" id="dec-id" placeholder="backend id (slug)" ${!LIVE ? "disabled" : ""}>
    <input type="text" id="dec-name" placeholder="display name" ${!LIVE ? "disabled" : ""}>
    <select id="dec-class" ${!LIVE ? "disabled" : ""}>${(c.classes || []).map(x => `<option>${esc(x)}</option>`).join("")}</select>
    <button class="btn" ${!LIVE ? "disabled" : ""} onclick="declareBackend()">Declare backend</button>`;
  document.getElementById("dec-id").value = decPrev.id;
  document.getElementById("dec-name").value = decPrev.name;
  if (decPrev.cls) document.getElementById("dec-class").value = decPrev.cls;

  const cfgEvents = DATA.audit.filter(a => a.config_change).slice(0, 30);
  document.getElementById("cfghistory").innerHTML = cfgEvents.length === 0 ?
    '<div class="empty">no configuration changes yet</div>' :
    cfgEvents.map(a => {
      const ch = a.config_change, detail = Object.entries(ch).filter(([k]) => k !== "action")
        .map(([k, v]) => `${k}=${Array.isArray(v) ? v.join("+") : v}`).join(" · ");
      return `<div class="cfg-row">
        <span class="t mono" style="color:var(--muted)">${esc((a.timestamp || "").replace("T", " ").replace("Z", ""))}</span>
        <span style="font-weight:600">${esc(ch.action)}</span>
        <span style="color:var(--ink-2)">${esc(detail)}</span></div>`;
    }).join("");

  const backends = c.backends;
  const types = Object.keys(c.routing);
  document.getElementById("matrix").innerHTML =
    `<tr><th data-help="Each memory type is a kind of remembering with its own natural home.">memory type</th>${backends.map(b => `<th data-help="${esc(b.description || b.backend_id)}">${esc(b.backend_id)}</th>`).join("")}</tr>` +
    types.map(t => `<tr><td class="mono" data-help="${esc(c.memory_type_info[t] || t)}">${esc(t)}</td>${backends.map(b => {
      const checked = (c.routing[t] || []).includes(b.backend_id);
      return `<td><input type="checkbox" ${checked ? "checked" : ""} ${(!LIVE || !b.enabled) ? "disabled" : ""}
        onchange="routeChange('${esc(t)}')" data-t="${esc(t)}" data-b="${esc(b.backend_id)}"></td>`;
    }).join("")}</tr>`).join("");
}

function routeChange(t) {
  const targets = [...document.querySelectorAll(`.matrix input[data-t="${t}"]`)]
    .filter(cb => cb.checked).map(cb => cb.dataset.b);
  control("routing", { memory_type: t, backends: targets });
}

function toast(msg, ok) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.style.borderColor = ok === true ? "var(--good)" : ok === false ? "var(--critical)" : "var(--muted)";
  el.style.opacity = 1;
  clearTimeout(el._t);
  if (ok !== null) el._t = setTimeout(() => { el.style.opacity = 0; }, 3500);
}

async function control(action, payload) {
  toast(action.replace(/_/g, " ") + "…", null);
  try {
    const res = await fetch("control", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-MemoryCore-Control": "1" },
      body: JSON.stringify({ action, ...payload }),
    });
    const out = await res.json();
    toast(out.message || out.status, out.status === "ok");
    await poll();
  } catch (e) { toast("control failed: " + e, false); }
}

let LIVE = false;
renderAll();
async function poll() {
  try {
    const res = await fetch("data.json", { cache: "no-store" });
    if (!res.ok) return;
    const fresh = await res.json();
    if (JSON.stringify(fresh) !== JSON.stringify(DATA)) { DATA = fresh; renderAll(); }
    if (!LIVE) { LIVE = true; renderAll(); }
  } catch (e) { /* static snapshot (file or artifact) — polling unavailable */ }
}
poll(); setInterval(poll, 4000);

function buildDetailRow(r) {
  const related = DATA.audit.filter(a => (a.pointer_ids || []).some(p =>
    p === r.content_ref || p === r.source_pointer.pointer_id));
  const d = document.createElement("tr");
  d.className = "detail";
  d.innerHTML = `<td colspan="7"><div class="detail-grid">
    <div><h3>Provenance pointer</h3><pre>${esc(JSON.stringify(r.source_pointer, null, 1))}</pre></div>
    <div><h3>Receipt</h3><pre>record   ${esc(r.record_id)}
hash     ${esc(r.content_hash ? r.content_hash.slice(0, 28) + "…" : "(none — pre-hash record)")}
created  ${esc(r.created_at)}
updated  ${esc(r.updated_at)}
state    ${esc(r.verification)} / ${esc(r.flush_state)}</pre></div>
    <div><h3>Audit entries for this pointer (${related.length})</h3><pre>${related.length ?
      esc(related.map(a => `${a.timestamp}  ${a.operation}  ${a.verification_state}  ${a.audit_id}`).join("\n")) :
      "none recorded"}</pre>
      <div style="display:flex;gap:8px;margin-top:8px;flex-wrap:wrap">
        <button class="btn" ${!LIVE ? "disabled" : ""} onclick="reveal('${esc(r.record_id)}', this)">Reveal content</button>
        <button class="btn" ${!LIVE ? "disabled" : ""} onclick="exportPack('${esc(r.record_id)}')">Export evidence pack</button>
        <button class="btn danger" ${!LIVE ? "disabled" : ""}
          onclick="control('forget',{record_id:'${esc(r.record_id)}'})">Forget</button>
      </div>
      <div class="revealpane"></div></div>
  </div></td>`;
  if (revealCache[r.record_id]) d.querySelector(".revealpane").innerHTML = revealCache[r.record_id];
  return d;
}

function restoreOpenDetail() {
  if (!openRecordId) return;
  const idx = records.findIndex(r => r.record_id === openRecordId);
  const row = document.querySelector(`#memtable tr.mem[data-i="${idx}"]`);
  if (idx < 0 || !row) { openRecordId = null; return; }
  row.after(buildDetailRow(records[idx]));
}

const tbody2 = document.querySelector("#memtable tbody");
tbody2.addEventListener("click", e => {
  const row = e.target.closest("tr.mem"); if (!row) return;
  const r = records[+row.dataset.i];
  const closing = openRecordId === r.record_id;
  document.querySelectorAll("tr.detail").forEach(d => d.remove());
  openRecordId = closing ? null : r.record_id;
  if (!closing) row.after(buildDetailRow(r));
});

async function controlRaw(action, payload) {
  const res = await fetch("control", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-MemoryCore-Control": "1" },
    body: JSON.stringify({ action, ...payload }),
  });
  return res.json();
}

async function reveal(recordId, btn) {
  const pane = btn.closest("td").querySelector(".revealpane");
  pane.innerHTML = '<div class="empty">fetching from backend store…</div>';
  try {
    const out = await controlRaw("reveal", { record_id: recordId });
    if (out.status !== "ok") { pane.innerHTML = `<div class="empty">${esc(out.message)}</div>`; toast(out.message, false); return; }
    const match = out.hash_match;
    const verdict = match === true
      ? `<span class="badge"><span class="ic" style="color:var(--good)">✓</span>hash verified live</span>`
      : match === false
        ? `<span class="badge"><span class="ic" style="color:var(--critical)">✕</span>HASH MISMATCH — content differs from receipt</span>`
        : `<span class="badge"><span class="ic" style="color:var(--muted)">?</span>no stored hash to compare</span>`;
    pane.innerHTML = `
      <div class="hashcmp">${verdict}
        <span class="mono" style="color:var(--muted)">stored ${esc((out.stored_hash || "—").slice(0, 20))}… · computed ${esc(out.computed_hash.slice(0, 20))}…</span>
        ${out.note ? `<span style="color:var(--muted)">${esc(out.note)}</span>` : ""}</div>
      <pre class="content">${esc(out.content)}</pre>
      <div style="font-size:11.5px;color:var(--muted);margin-top:4px">read receipted as content_access — content shown live, never stored in this page</div>`;
    revealCache[recordId] = pane.innerHTML;
    toast("content revealed — read receipted", true);
    poll();
  } catch (e) { pane.innerHTML = ""; toast("reveal failed: " + e, false); }
}

async function exportPack(recordId) {
  toast("exporting evidence pack…", null);
  try {
    const out = await controlRaw("pack", { record_id: recordId });
    if (out.status !== "ok") { toast(out.message, false); return; }
    const blob = new Blob([JSON.stringify(out, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `engram-pack-${recordId}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
    toast(`evidence pack exported — integrity ${out.integrity.slice(0, 16)}…`, true);
    poll();
  } catch (e) { toast("export failed: " + e, false); }
}

async function declareBackend() {
  const id = document.getElementById("dec-id").value.trim();
  const name = document.getElementById("dec-name").value.trim();
  const cls = document.getElementById("dec-class").value;
  if (!id) { toast("backend id required", false); return; }
  const out = await controlRaw("declare", { backend_id: id, display_name: name, class: cls });
  toast(out.message || out.status, out.status === "ok");
  if (out.status === "ok") ["dec-id", "dec-name"].forEach(x => { document.getElementById(x).value = ""; });
  poll();
}

document.getElementById("btn-flush").onclick = () => control("flush", {});
document.getElementById("btn-verify").onclick = () => control("verify_all", {});
document.getElementById("btn-reset").onclick = () => {
  if (confirm("Reset mode, backend enablement, and routing to installed defaults? Declared future backends are preserved (disabled). This action is audited."))
    control("reset_config", {});
};

let contentMatches = {};
let contentTimer = null;
function memSearchInput() {
  renderAll();
  clearTimeout(contentTimer);
  const q = document.getElementById("mf-text").value.trim();
  if (!LIVE || q.length < 3) { if (Object.keys(contentMatches).length) { contentMatches = {}; renderAll(); } return; }
  contentTimer = setTimeout(async () => {
    try {
      const res = await fetch("content-search.json?q=" + encodeURIComponent(q),
        { headers: { "X-MemoryCore-Control": "1" }, cache: "no-store" });
      const out = await res.json();
      contentMatches = {};
      (out.matches || []).forEach(m => { if (m.record_id) contentMatches[m.record_id] = m.snippet; });
      renderAll();
    } catch (e) { /* static snapshot: content search unavailable */ }
  }, 250);
}

function toggleTheme() {
  const root = document.documentElement;
  const dark = root.dataset.theme === "dark" || (!root.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
  root.dataset.theme = dark ? "light" : "dark";
}
</script>
</body>
</html>
"""
