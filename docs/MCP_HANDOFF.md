# MCP Handoff

Status: fixture-only contract handoff.

MemoryCore currently exposes MCP-shaped local functions in
`memorycore/mcp_surface.py`. It does not start an MCP server, register with an
agent runtime, or call live QMD, Lossless-Claw, Burrow, or OpenClaw.

## Tools

### `memorycore_search`

Arguments:

- `query` string, required
- `backend` optional enum: `qmd`, `lossless_claw`, `mock_healthy`
- `intent` optional enum: `file_corpus_recall`,
  `transcript_continuity_recall`
- `limit` optional integer, 1 to 50, default 5

Maps to canonical request fields:

- `operation: "search"`
- `client_surface: "mcp"`
- `backend` to `backend_hint`

### `memorycore_get`

Arguments:

- `pointer_id` string, required
- `backend` optional enum: `qmd`, `lossless_claw`, `mock_healthy`, default `qmd`

Maps to canonical request fields:

- `operation: "get"`
- `client_surface: "mcp"`
- `pointer.backend_id`
- `pointer.pointer_id`
- `pointer.source_uri`

### `memorycore_verify`

Arguments:

- `pointer_id` string, required
- `backend` optional enum: `qmd`, `lossless_claw`, `mock_healthy`, default
  `mock_healthy`
- `state` optional enum: `verified`, `stale`, `missing`, `unsupported`,
  `unknown`, default `verified`

Maps to canonical request fields:

- `operation: "verify"`
- `client_surface: "mcp"`
- `pointer.backend_id`
- `pointer.pointer_id`
- `pointer.source_uri`
- `verification_state`

### `memorycore_health`

Arguments: none.

Maps to canonical request fields:

- `operation: "health"`
- `client_surface: "mcp"`
- `intent: "backend_health"`

## Result Equivalence

`scripts/validate_mvp_mcp_surface.py` compares MCP-shaped calls against
equivalent CLI invocations. Results must match after removing these
transport-wrapper fields:

- `request_id`
- `audit_id`

All other returned fields are normalized core result fields and must remain
equivalent across CLI and MCP:

- `operation`
- `status`
- `selected_backend`
- `results`
- `verification_state`
- `error`

## Audit And Provenance

MCP search/get/verify calls append audit records through the same audit builder
used by the CLI. Audit records are content-sparse and include pointer ids,
backend ids, operation, normalized intent, status, verification state, and error
category/code. They must not persist private snippets, content, citations,
summaries, answers, or transcript text by default.

The current MCP surface does not append provenance ledger records directly. It
returns normalized result pointers that downstream provenance code can record
through the shared provenance ledger contract.

## Transport Wrapper Differences

The current wrapper is a local Python function contract:

```python
call_tool("memorycore_search", {"query": "alpha-river-contract-fixture"})
```

A real MCP server entrypoint still needs to:

- bind `TOOL_DEFINITIONS` into the selected MCP Python server library
- translate MCP request ids, session ids, and cancellation semantics into
  MemoryCore request metadata
- serialize exceptions into structured, content-sparse MCP tool errors
- decide where configured audit/provenance paths come from
- define startup health behavior for fixture-only, local-only, and future live
  backend modes
- add an operator-safe packaging and launch path

Until that exists, `memorycore/mcp_surface.py` is the handoff contract, not the
runtime server.
