# Agent Context

Status: active build map, updated 2026-07-02.

This file is the first-load map for agents working on MemoryCore.

## Load Order

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
  `transcript` -> `lossless_claw`. Multi-target routing marks records
  `mirrored`.
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
   binary. Remaining: run against real QMD locally, decide the LCM bridge
   transport.
2. Real verification: `memorycore_verify` currently echoes the caller's
   asserted state. Implement backend-proof verify (QMD `get` resolves ->
   `verified`; LCM `describe` confirms -> `verified`) per
   `docs/LIVE_BACKEND_BOUNDARIES.md`, plus a re-verification policy so
   cached `verified` stamps can degrade (verify-on-read or TTL).
3. Content-in-transit design: the cache is pointer-only, so `remember`
   cannot yet carry new content. Design the flush leg that materializes
   content into a backend (file into a dedicated QMD collection; message
   into LCM `engine.ingest` via new host-bridge functions
   `lcm_ingest` / `lcm_ingest_batch`) and returns a pointer to the cache.
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

