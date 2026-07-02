# MCP Handoff

Status: fixture-only contract with a real MCP server entrypoint.

MemoryCore currently exposes MCP-shaped local functions in
`memorycore/mcp_surface.py`. `memorycore/mcp_server.py` wraps that contract in
the Python MCP SDK's `FastMCP` server so an MCP-capable client can launch the
same four MVP tools. The server remains fixture-only and does not call live QMD,
Lossless-Claw, Burrow, or OpenClaw.

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

### Cache tools

`memorycore_remember`, `memorycore_recall`, `memorycore_cache_search`, and
`memorycore_flush` expose the caching memory router
(docs/CACHING_MEMORY_ROUTER.md) on this surface. Their argument and result
contract, OpenClaw client-surface handling, and fixture-only flush boundary
are documented in docs/CACHE_API_OPENCLAW.md and validated by
`scripts/validate_mvp_cache_api.py`.

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

The canonical local Python function contract remains:

```python
call_tool("memorycore_search", {"query": "alpha-river-contract-fixture"})
```

The real MCP server entrypoint is:

```bash
python3 -m memorycore.mcp_server --transport stdio
```

Use `--check` to validate import and tool registration without starting a
server:

```bash
python3 -m memorycore.mcp_server --check
```

Supported launch transports are `stdio`, `sse`, and `streamable-http`. `stdio`
is the default and is the assumed local agent launch mode for the MVP. The
entrypoint delegates all tool behavior to `memorycore.mcp_surface.call_tool`;
by default, audit behavior follows the existing MCP surface default. Set
`MEMORYCORE_MCP_AUDIT_LOG` to route server audit records to an explicit path
without changing tool arguments. Server-wrapper validation lives in:

```bash
python3 scripts/validate_mcp_server_entrypoint.py
```

FastMCP may expose an SDK-generated input schema with Pydantic metadata such as
argument titles. `memorycore.mcp_surface.TOOL_DEFINITIONS` remains the canonical
descriptor contract checked by `scripts/validate_mvp_mcp_surface.py`.

The server wrapper now handles:

- binding the four MVP tools into `mcp.server.fastmcp.FastMCP`
- launching via a module entrypoint
- reporting dependency status with `--check`
- serializing surface exceptions into content-sparse structured tool errors

A production MCP runtime handoff still needs to:

- translate MCP request ids, session ids, and cancellation semantics into
  MemoryCore request metadata
- decide where configured audit/provenance paths come from
- define startup health behavior for fixture-only, local-only, and future live
  backend modes
- add an operator-safe packaging and install path
- run a real MCP client compatibility smoke once packaging and launch policy are
  settled
