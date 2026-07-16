# Agent Context

Status: active build map, updated 2026-07-02.

This file is the first-load map for agents working on MemoryCore.

## Load Order

0. `docs/REGISTER.md` — QTrellis product register; open before discussing
   any item, name an ID in every product-code commit
1. `SPEC.md`
2. `tasks/plan.md`
3. `tasks/todo.md`
4. `docs/MVP_EVAL_PLAN.md`
5. `docs/LIVE_BACKEND_BOUNDARIES.md`
6. `docs/API_CONTRACT.md`
7. `docs/THREAT_MODEL.md`
8. `docs/CACHING_MEMORY_ROUTER.md`
9. `docs/CACHE_API_OPENCLAW.md`

## Current Verification Command

```bash
python3 -m memorycore.cli eval --public-safe
```

## Working Rules

- Keep public artifacts fixture-only and content-sparse unless a task explicitly
  says otherwise.
- Do not run EVAL-012 until the hard stop in
  `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md` is lifted and recorded.
- Treat QMD and Lossless-Claw live paths as local-only until their boundaries
  have executable tests.
- Prefer small vertical slices with an eval before expanding scope.

## Key Runtime Modules

- `memorycore/registry_router.py` owns backend selection and normalized routing.
- `memorycore/cache_router.py` owns the caching memory layer: SQLite
  `cache_records` store, `cache_write` / `cache_read` / `cache_search`
  verbs, and `flush_pending` routing by memory type
  (see `docs/CACHING_MEMORY_ROUTER.md`).
- `memorycore/qmd_adapter.py` normalizes QMD-shaped fixture responses and
  holds the live-local shell-out mode (not yet wired into request execution).
- `memorycore/lcm_adapter.py` normalizes Lossless-Claw-shaped fixture
  responses and holds the host-injected bridge boundary.
- `memorycore/provenance_ledger.py` records pointer/provenance metadata.
- `memorycore/verification_state.py` owns the verification vocabulary
  (`verified` / `stale` / `missing` / `unsupported` / `unknown`).
- `memorycore/audit_log.py` records content-sparse audit events.
- `memorycore/mcp_surface.py` exposes MCP-shaped local calls, including the
  cache tools `memorycore_remember` / `memorycore_recall` /
  `memorycore_cache_search` / `memorycore_flush`
  (see `docs/CACHE_API_OPENCLAW.md`).
- `memorycore/mcp_server.py` binds the surface to FastMCP; cache path via
  `MEMORYCORE_CACHE_DB`, audit path via `MEMORYCORE_MCP_AUDIT_LOG`.
- `memorycore/cli.py` exposes the current operator surface.
- `memorycore/eval.py` runs the consolidated public-safe eval suite.

## Cache Layer Facts

- Cache DB default: `.memorycore/cache.sqlite3` (gitignored), override with
  `MEMORYCORE_CACHE_DB`.
- Cache records are content-sparse: pointers and bounded fields only.
  `cache_write` rejects `snippet` / `content` / `citations` / `summary` /
  `answer` / `text`.
- Routing by memory type: `file_corpus` -> `qmd`,
  `transcript` -> `lossless_claw`, `local` -> `jsonl_store` (EN-020:
  zero-dependency JSONL backend, `MEMORYCORE_JSONL_STORE`, write-through
  and hash-based verify work in every mode). Multi-target routing marks
  records `mirrored`.
- Flush is currently fixture-only: handlers acknowledge without delivering.
  Results disclose `flush_mode: "fixture-only"`. Do not remove that
  disclosure until real gated write adapters exist.
- Cache tools accept `client: "openclaw"` so OpenClaw calls are attributed
  in audit records.

## Current Build Frontier

Ordered critical path to a functional caching memory layer between
OpenClaw, QMD, and LCM. Fixture-first versions of all items are buildable
now; only live OpenClaw invocation waits on the EVAL-012 hard stop.

1. Live read wiring: SCAFFOLDED for QMD. `MEMORYCORE_BACKEND_MODE=live-local`
   routes QMD search/get through the live-local subprocess adapter
   (`MEMORYCORE_QMD_BIN`, `MEMORYCORE_QMD_COLLECTION`); fixture stays the
   default; LCM reports unavailable in live-local mode because no host
   bridge exists on the CLI/MCP surface (open design question: bridge over
   MCP). Validated by `scripts/validate_mvp_live_mode.py` with a stub qmd
   binary and proven against the real index. The LCM callback transport
   (ADR-0006, EN-019) is BUILT fixture-first: transcript remembers cache
   the record `awaiting_delivery` and return a `delivery` instruction;
   `memorycore_confirm_delivery` closes the loop (delivered -> flushed
   with the reported pointer, verification stays unknown until describe;
   failed -> failed). Validated with a simulated executor in
   `scripts/validate_mvp_callback_delivery.py`. Remaining: the OpenClaw-
   side executor plugin and describe-based verify, both gated behind
   EVAL-012 for live exercise.
2. Real verification: DONE for QMD (EN-018). `memorycore_verify` with
   `record_id` in live-local mode proves against source state: disk gone ->
   `missing` (even while the index lags), disk differs from stored content
   hash or indexed body -> `stale`, agreement -> `verified`, backend down ->
   `unknown`. Verdicts update the cached stamp. Cache gained a
   `content_hash` column (auto-migrated). Fixture-mode record verification
   honestly returns `unsupported`. Proven on the real index 2026-07-05.
   Remaining: LCM `describe`-based verify (transport decided, ADR-0006),
   automatic re-verification policy (verify-on-read / TTL, IDEA-002).
3. Content-in-transit: DONE for QMD (ADR-0005 transient write-through).
   `memorycore_remember` accepts `content`; live-local mode materializes
   it into the dedicated `memorycore-writes` collection
   (`~/.memorycore/corpus`, config: `MEMORYCORE_QMD_WRITE_COLLECTION`,
   `MEMORYCORE_CORPUS_DIR`, `MEMORYCORE_QMD_TIMEOUT_SECONDS`), indexes,
   and earns `verified` via qmd:// read-back. Proven against the real
   local QMD index 2026-07-04. Remaining: the LCM half via the callback
   transport (ADR-0006): delivery instruction in the remember response,
   OpenClaw-side `engine.ingest`, and a delivery-confirmation tool.
4. Gated writes: write-intent request contract (PersistenceIntent shape),
   QMD import/reindex adapter (allowlisted CLI, isolated collection), LCM
   ingest bridge, real flush mode flag replacing fixture handlers, and
   content-sparse write audit records.
5. Operational gaps: flush retry / dead-letter for `failed` records;
   unique request ids per call (audit collision); idempotency policy for
   repeated remembers; enable SQLite WAL mode; real backend registry
   config to replace the `basic.json` fixture; packaging so OpenClaw can
   launch the MCP server without a checkout.

Explicitly deferred: reasoning/indexing engines, git-native provenance
engine, mirroring policies, operator UI.

