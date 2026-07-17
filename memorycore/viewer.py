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

    audit = read_recent(audit_log, limit=200) if audit_log.exists() else []
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

    return {"status": "error", "message": f"unknown control action: {action}"}


def render_html(data: dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True).replace("</", "<\\/")
    return _TEMPLATE.replace("__ENGRAM_DATA__", payload)


def write_viewer(cache_db: Path, audit_log: Path, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(collect_viewer_data(cache_db, audit_log)), encoding="utf-8")
    return output


def serve_viewer(cache_db: Path, audit_log: Path, *, port: int = 8787) -> None:
    """Serve the dashboard live on localhost, regenerated per request.

    Loopback-only by design: the receipts surface is a local operator
    console, never a network service. GET / renders fresh HTML; the page
    polls GET /data.json every few seconds so state changes appear live.
    """
    import http.server
    import json as _json

    from memorycore.cli import operator_config_path

    config_path = operator_config_path()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - http.server API
            if self.path.split("?")[0] == "/data.json":
                body = _json.dumps(collect_viewer_data(cache_db, audit_log)).encode("utf-8")
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

    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Engram receipts live at http://127.0.0.1:{port} (Ctrl-C to stop)")
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
    --s1: #2a78d6; --s2: #008300; --s3: #e87ba4;
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) {
      color-scheme: dark;
      --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7;
      --muted: #898781; --grid: #2c2c2a; --baseline: #383835;
      --ring: rgba(255,255,255,0.10);
      --s1: #3987e5; --s2: #008300; --s3: #d55181;
    }
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7;
    --muted: #898781; --grid: #2c2c2a; --baseline: #383835;
    --ring: rgba(255,255,255,0.10);
    --s1: #3987e5; --s2: #008300; --s3: #d55181;
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
  .ctl-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; }
  .bk-card { border: 1px solid var(--ring); border-radius: 10px; padding: 12px 14px; background: var(--page); }
  .bk-card.future { border-style: dashed; opacity: .75; }
  .bk-card .top { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
  .bk-card .name { font-weight: 650; font-size: 13.5px; flex: 1; }
  .bk-card .cls { font-size: 10.5px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }
  .bk-card .caps { font-size: 11.5px; color: var(--ink-2); margin: 6px 0 10px; }
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
  <h2>Control plane <span style="color:var(--muted);font-weight:400">— every change leaves a receipt in the audit trail</span></h2>
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;flex-wrap:wrap">
    <span style="font-size:12.5px;color:var(--ink-2)">Backend mode</span>
    <span class="seg" id="modeseg"></span>
    <span id="modenote" style="font-size:12px;color:var(--muted)"></span>
  </div>
  <div class="ctl-grid" id="bkcards"></div>
  <div class="reserved" id="reserved"></div>
  <h2 style="margin-top:18px">Routing matrix <span style="color:var(--muted);font-weight:400">— pointer flush targets; two checks on one row = mirroring</span></h2>
  <div style="overflow-x:auto"><table class="matrix" id="matrix"></table></div>
  <div class="ctl-note">Content write-through targets are fixed per type (local → JSONL, file_corpus → QMD, transcript → callback delivery); the matrix governs where pointer records flush.</div>
  <div class="ctl-actions" style="margin-top:14px">
    <button class="btn" id="btn-flush">Flush pending</button>
    <button class="btn" id="btn-verify">Re-verify all stamps</button>
  </div>
</section>
<div id="toast"></div>
<section>
  <h2>Verification states</h2>
  <div class="stackbar" id="stackbar"></div>
  <div class="legend" id="vlegend"></div>
</section>
<section>
  <h2>Memories by backend</h2>
  <div class="bars" id="backendbars"></div>
</section>
<section>
  <h2>Memory records <span style="color:var(--muted);font-weight:400">— click a row for its receipt</span></h2>
  <table id="memtable">
    <thead><tr><th>Record</th><th>Type</th><th>Backend</th><th>Pointer</th><th>Verification</th><th>Delivery</th><th>Updated</th></tr></thead>
    <tbody></tbody>
  </table>
</section>
<section>
  <h2>Audit trail <span style="color:var(--muted);font-weight:400">— newest first, content-sparse by contract</span></h2>
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
const BACKEND_SLOT = { qmd: "var(--s1)", lossless_claw: "var(--s2)", jsonl_store: "var(--s3)" };
const backendColor = b => BACKEND_SLOT[b] || "var(--muted)";
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const badge = state => { const v = V[state] || V.unknown;
  return `<span class="badge"><span class="ic" style="color:${v.color}">${v.ic}</span>${v.label}</span>`; };

const tip = document.getElementById("tip");
function showTip(e, html) { tip.innerHTML = html; tip.style.opacity = 1;
  tip.style.left = Math.min(e.clientX + 14, innerWidth - 220) + "px"; tip.style.top = (e.clientY + 14) + "px"; }
function hideTip() { tip.style.opacity = 0; }

let records = [];
function renderAll() {
document.getElementById("gen").textContent = "Generated " + DATA.generated_at + (LIVE ? " · live" : " · snapshot");
document.getElementById("foot").textContent =
  `cache: ${DATA.cache_db} · audit: ${DATA.audit_log} · local-first, content-sparse — pointers and hashes only, never memory content`;

const vc = DATA.verification_counts; records = DATA.records; const total = records.length;
const tiles = [
  { label: "memories", value: total, dot: null },
  { label: "verified", value: vc.verified || 0, dot: "var(--good)" },
  { label: "stale", value: vc.stale || 0, dot: "var(--warning)" },
  { label: "missing", value: vc.missing || 0, dot: "var(--serious)" },
  { label: "unknown", value: (vc.unknown || 0) + (vc.unsupported || 0), dot: "var(--muted)" },
  { label: "audit events", value: DATA.audit.length, dot: null },
];
document.getElementById("tiles").innerHTML = tiles.map(t =>
  `<div class="tile"><div class="label">${t.dot ? `<span class="dot" style="background:${t.dot}"></span>` : ""}${t.label}</div>
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
  `<span class="item"><span class="dot" style="background:${V[s].color}"></span>${V[s].ic} ${s} · ${vc[s] || 0}</span>`).join("");

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

const tbody = document.querySelector("#memtable tbody");
tbody.innerHTML = records.length === 0 ? '<tr><td colspan="7" class="empty">cache is empty</td></tr>' :
  records.map((r, i) => {
    const b = r.source_pointer.backend_id || "unrouted";
    return `<tr class="mem" data-i="${i}">
      <td class="mono">${esc(r.record_id.slice(0, 18))}…</td>
      <td>${esc(r.memory_type)}</td>
      <td><span class="dot" style="background:${backendColor(b)}"></span> ${esc(b)}</td>
      <td><span class="ptr mono" title="${esc(r.content_ref)}">${esc(r.content_ref)}</span></td>
      <td>${badge(r.verification)}</td>
      <td>${esc(r.flush_state)}</td>
      <td>${esc((r.updated_at || "").replace("T", " ").replace("Z", ""))}</td></tr>`;
  }).join("");

document.getElementById("audit").innerHTML = DATA.audit.length === 0 ?
  '<div class="empty">no audit events</div>' :
  DATA.audit.slice(0, 60).map(a => `<div class="audit-row">
    <span class="t mono">${esc((a.timestamp || "").replace("T", " ").replace("Z", ""))}</span>
    <span>${esc(a.operation)}</span>
    <span><span class="dot" style="background:${backendColor(a.selected_backend)}"></span> ${esc(a.selected_backend || "—")}</span>
    <span>${badge(a.verification_state)} ${a.status === "error" ? `<span class="badge"><span class="ic" style="color:var(--critical)">⊘</span>${esc((a.error_state||{}).code || "error")}</span>` : ""}</span>
    <span class="mono" style="color:var(--muted)">${esc(a.audit_id)}</span>
  </div>`).join("");

renderControl();
}

function renderControl() {
  const c = DATA.control;
  const sec = document.getElementById("controlplane");
  if (!c) { sec.style.display = "none"; return; }
  sec.style.display = "";

  const envPinned = c.mode_source === "env";
  document.getElementById("modeseg").innerHTML = ["fixture", "live-local"].map(m =>
    `<button class="${m === c.mode ? "active" : ""}" ${(!LIVE || envPinned) ? "disabled" : ""}
      onclick="control('mode',{mode:'${m}'})">${m}</button>`).join("");
  document.getElementById("modenote").textContent =
    envPinned ? "pinned by MEMORYCORE_BACKEND_MODE env" : (LIVE ? "" : "controls require the live server");

  document.getElementById("bkcards").innerHTML = c.backends.map(b => `
    <div class="bk-card ${b.adapter_installed ? "" : "future"}">
      <div class="top">
        <span class="dot" style="background:${b.enabled && b.adapter_installed ? backendColor(b.backend_id) : "var(--muted)"}"></span>
        <span class="name">${esc(b.display_name)}</span>
        <span class="cls">${esc(b.class)}</span>
      </div>
      <div class="caps">${b.adapter_installed
        ? `verify: ${esc(String(b.capabilities.verify))} · content search: ${b.capabilities.content_search ? "yes" : "no"}`
        : "declared — no adapter installed"}</div>
      <button class="toggle ${b.enabled ? "on" : "off"}" ${!LIVE ? "disabled" : ""}
        onclick="control('backend',{backend_id:'${esc(b.backend_id)}',enabled:${!b.enabled}})">
        ${b.enabled ? "enabled" : "disabled"}</button>
    </div>`).join("");

  document.getElementById("reserved").textContent =
    "Reserved for future systems: " + c.reserved_classes.join(" · ") + " — declare a backend entry to populate.";

  const backends = c.backends;
  const types = Object.keys(c.routing);
  document.getElementById("matrix").innerHTML =
    `<tr><th>memory type</th>${backends.map(b => `<th>${esc(b.backend_id)}</th>`).join("")}</tr>` +
    types.map(t => `<tr><td class="mono">${esc(t)}</td>${backends.map(b => {
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
  el.style.borderColor = ok ? "var(--good)" : "var(--critical)";
  el.style.opacity = 1;
  clearTimeout(el._t); el._t = setTimeout(() => { el.style.opacity = 0; }, 3500);
}

async function control(action, payload) {
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

const tbody2 = document.querySelector("#memtable tbody");
tbody2.addEventListener("click", e => {
  const row = e.target.closest("tr.mem"); if (!row) return;
  const open = row.nextElementSibling?.classList.contains("detail");
  document.querySelectorAll("tr.detail").forEach(d => d.remove());
  if (open) return;
  const r = records[+row.dataset.i];
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
      <button class="btn danger" style="margin-top:8px" ${!LIVE ? "disabled" : ""}
        onclick="control('forget',{record_id:'${esc(r.record_id)}'})">Forget this memory</button></div>
  </div></td>`;
  row.after(d);
});

document.getElementById("btn-flush").onclick = () => control("flush", {});
document.getElementById("btn-verify").onclick = () => control("verify_all", {});

function toggleTheme() {
  const root = document.documentElement;
  const dark = root.dataset.theme === "dark" || (!root.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
  root.dataset.theme = dark ? "light" : "dark";
}
</script>
</body>
</html>
"""
