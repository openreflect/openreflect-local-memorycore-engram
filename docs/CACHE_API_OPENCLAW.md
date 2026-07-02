# Cache API: OpenClaw Perspective

Status: fixture-only contract, 2026-07-02. Live OpenClaw invocation remains
gated behind the EVAL-012 hard stop; this document defines the surface
OpenClaw will call once that gate lifts.

## What OpenClaw gets

Four MCP tools over the caching memory router
(docs/CACHING_MEMORY_ROUTER.md). OpenClaw remembers things during a session,
recalls them later, searches what it has remembered, and lets MemoryCore
flush records onward to the right backend by memory type.

```text
OpenClaw session
    |
    | memorycore_remember      "keep this, it matters"
    | memorycore_recall        "give me back what I kept"
    | memorycore_cache_search  "what do I have about X?"
    | memorycore_flush         "push pending records to backends"
    v
MCP server (stdio) -> cache router -> local SQLite cache
                                   -> flush by memory type (fixture-only)
```

All four tools accept `client: "openclaw"`, which is carried into the
canonical request `client_surface` and every audit record, so OpenClaw
activity is distinguishable from other MCP callers after the fact.

## Tools

### `memorycore_remember`

Arguments:

- `memory_type` required enum: `file_corpus`, `transcript`
- `content_ref` required string — a pointer to content, never content itself
- `pointer_id` optional string, defaults to `content_ref`
- `summary_id` optional string (transcript records)
- `verification` optional enum, default `unknown`
- `client` optional enum: `mcp`, `openclaw`

Behavior: the record lands in the cache `pending`, stamped with a provenance
pointer routed by memory type (`file_corpus` -> `qmd`,
`transcript` -> `lossless_claw`). Returns the stamped record including its
stable `record_id`.

Raw content arguments (`snippet`, `content`, `text`, ...) are rejected at
the argument-validation layer. OpenClaw stores pointers, not prose.

### `memorycore_recall`

Arguments: `record_id` or `pointer_id` (one required), `client`.

Behavior: cache hit returns the record with its stored verification state.
A miss returns a structured `CACHE_MISS` error with
`verification_state: "missing"` — never a fabricated hit.

### `memorycore_cache_search`

Arguments: `query` required, `memory_type` optional filter, `limit` 1-50
(default 5), `client`.

Behavior: searches cached records only. It never queries live backends;
use `memorycore_search` for fixture-backend search.

### `memorycore_flush`

Arguments: `client` only.

Behavior: flushes every `pending` record to its routed backend targets.
Results carry the updated `flush_state` (`flushed`, `mirrored`, `failed`).
The result includes `flush_mode: "fixture-only"` until real gated write
adapters replace the fixture acknowledgments — flushes currently prove the
contract, not delivery.

## Result contract

All tools return the normalized result shape shared with the CLI and the
existing MCP tools: `request_id`, `operation` (`cache_write`, `cache_read`,
`cache_search`, `cache_flush`), `status`, `results[]` with per-item
`backend_id` / `pointer` / `verification_state`, a result-level
`verification_state`, and an `audit_id`.

Cache items add `record_id`, `memory_type`, `content_ref`, and
`flush_state`.

## Audit and provenance

Every cache call appends a content-sparse audit record through the shared
audit builder, including the `client_surface` (`openclaw` when OpenClaw
identifies itself). Audit records never contain snippets, content,
citations, summaries, answers, or transcript text.

## Boundaries

- Fixture-only: no live QMD, Lossless-Claw, Burrow, or OpenClaw calls.
- The EVAL-012 hard stop governs when OpenClaw may actually connect; this
  surface exists so that connection is a configuration step, not new code.
- Cache location: `MEMORYCORE_CACHE_DB` env var, defaulting to
  `.memorycore/cache.sqlite3` (gitignored). Audit path follows the existing
  `MEMORYCORE_MCP_AUDIT_LOG` behavior.

## Validation

```bash
python3 scripts/validate_mvp_cache_api.py   # MEMORYCORE_CACHE_API_OK
```

Wired into the public-safe runner as `MEMORYCORE_CACHE_API`.

## Expected OpenClaw call sequence

```text
memorycore_remember  {memory_type, content_ref, client: "openclaw"}
memorycore_flush     {client: "openclaw"}
... session ends, later session begins ...
memorycore_cache_search {query, client: "openclaw"}
memorycore_recall    {record_id, client: "openclaw"}
memorycore_verify    {pointer_id}   # freshness check via existing tool
```
