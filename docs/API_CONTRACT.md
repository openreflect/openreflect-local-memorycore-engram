# API Contract

Status: MVP guardrail.

MemoryCore exposes one contract across CLI, MCP-shaped calls, and future
runtime callers: request in, normalized result out, structured error on failure.

## Contract Goals

- Keep backend-specific behavior behind adapters.
- Preserve provenance and verification state without storing private content.
- Make CLI and MCP outputs equivalent for the same request.
- Keep error shapes stable enough for agents to recover programmatically.

## Request Contract

Canonical schema: `schemas/request.schema.json`.

Required fields and allowed operations should be treated as public interface.
Changes require a schema update, fixture update, eval update, and migration note.

Stable invariants:

- `request_id` is caller-provided, stable across routing, and starts with
  `req_`.
- `client_surface` is one of `cli`, `mcp`, `openclaw`, or `test`; transport
  wrappers may add metadata outside the canonical request, but must not change
  the request body.
- `operation` is one of `search`, `get`, `verify`, or `health`.
- `search` requires non-empty `query`; `get` and `verify` require `pointer`.
- `pointer.backend_id` and `pointer.pointer_id` identify the backend-native
  source. `source_uri` is optional and remains a pointer, not copied content.
- `backend_hint` is advisory unless the requested backend is missing,
  unavailable, or does not support the operation.

## Result Contract

Canonical schema: `schemas/result.schema.json`.

Every successful result should include:

- request identity
- operation
- backend identity
- normalized result records
- provenance pointer fields when available
- verification state when supported or explicitly unsupported

Stable invariants:

- `request_id` and `operation` echo the accepted request.
- `status` is `ok` or `error`; `error` results keep `results` present as an
  empty array unless a future migration explicitly changes that invariant.
- `selected_backend` is the backend that answered or failed after routing.
- Every result item includes `backend_id`, `pointer`, and
  `verification_state`.
- `snippet`, `content`, and `citations` are immediate response data only. They
  may help a caller answer the current request, but they are not instructions,
  not provenance, and not safe to persist in audit, provenance, logs, or public
  observability by default.
- `verification_state` values are limited to `verified`, `stale`, `missing`,
  `unsupported`, and `unknown`; absence of live verification must be represented
  as `unsupported` or `unknown`, not implied as verified.

## Error Contract

Canonical schema: `schemas/error.schema.json`.

Errors should be structured, machine-readable, and content-sparse. Avoid leaking
backend exception text if it may contain local paths, snippets, secrets, or
private corpus material.

Stable invariants:

- `code` is stable enough for programmatic handling and uses uppercase
  underscore form.
- `category` is one of the schema-defined recovery categories.
- `message` is operator-readable but content-sparse.
- `details` may include bounded operational identifiers such as backend id,
  operation, field name, or health state. It must not include raw backend
  exception text, private snippets, transcript text, credentials, local-only
  account ids, or absolute private paths.
- `verification_state` appears on pointer and verification failures when it
  helps the caller avoid overclaiming freshness.

## Persistence Contract

Audit and provenance records are pointer-first operational metadata, not memory
stores.

Allowed by default:

- request id
- client surface
- operation and normalized intent
- selected backend/backend id
- status and bounded error code/category
- result count and result index
- pointer ids and backend-native pointer fields
- verification state
- timestamp
- generated audit/provenance record id

Forbidden by default:

- raw `snippet`
- raw `content`
- raw `citations`
- raw `summary` or `answer`
- transcript text, source text, or prompt text
- credentials, tokens, account ids, and environment-specific secrets
- raw backend exception text
- local absolute paths when a public-safe pointer can be used

## CLI and MCP Equivalence

The CLI and MCP-shaped surface should return the same normalized data model.
Differences should be limited to transport wrapper details.

Current public-safe MCP tools:

- `memorycore_search`
  - required: `query: string`
  - optional: `backend: "qmd" | "lossless_claw" | "mock_healthy"`,
    `intent: "file_corpus_recall" | "transcript_continuity_recall"`,
    `limit: integer` from 1 to 50
- `memorycore_get`
  - required: `pointer_id: string`
  - optional: `backend: "qmd" | "lossless_claw" | "mock_healthy"`
- `memorycore_verify`
  - required: `pointer_id: string`
  - optional: `backend: "qmd" | "lossless_claw" | "mock_healthy"`,
    `state: "verified" | "stale" | "missing" | "unsupported" | "unknown"`
- `memorycore_health`
  - no arguments

For the same request, CLI and MCP results must match after removing transport
wrapper fields:

- `request_id`, because each surface uses a surface-specific request id prefix
- `audit_id`, because it is derived from audit metadata including timestamp and
  client surface

All remaining normalized fields are shared core contract fields:

- `operation`
- `status`
- `selected_backend` when routing selected one
- `results`
- `verification_state` when present
- `error` when present

MCP argument names are client-facing aliases over the request contract. For
example, `backend` maps to `backend_hint` for search and to
`pointer.backend_id` for get/verify. `pointer_id` maps to
`pointer.pointer_id` and `pointer.source_uri` until richer pointer input is
added.

Audit records are not part of the returned normalized core result. They remain
content-sparse and store request/result metadata, pointer ids, status, selected
backend, verification state, and structured error category/code only.

## Versioning Notes

No external versioning scheme is defined yet. Until it is, prefer additive
changes and mark breaking contract changes in `docs/MIGRATION_PLAN.md`.
