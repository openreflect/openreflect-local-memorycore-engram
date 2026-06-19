# MemoryCore MVP Eval Plan

Date: 2026-06-17
Status: Draft

## Purpose

This document breaks the MVP into programmatic work items and evals an
implementation agent can develop against.

The goal is not to create a large governance layer. The goal is to make each
MVP capability testable before the next layer depends on it.

## Eval Principles

- Every programmatic item gets at least one deterministic eval.
- Real backend evals are required before the MVP can be called functional.
- Mock evals are allowed only for fast contract checks or unavailable backends.
- No eval should require private source content in the public repo.
- Failures must be structured enough to show whether the issue is contract,
  routing, backend, verification, or client-surface behavior.

## Shared Eval Fixtures

### Public Fixture Corpus

Purpose:

- Provide stable QMD-searchable files without using private memory.

Suggested shape:

- `fixtures/corpus/project-alpha.md`
- `fixtures/corpus/runbook-memorycore.md`
- `fixtures/corpus/transcript-note.md`

Required content:

- one unique phrase for exact lexical recall,
- one conceptually related phrase for semantic recall if available,
- stable headings for get-by-pointer evals,
- no private names, paths, account ids, or transcript exports.

### Mock Backend Fixtures

Purpose:

- Test registry, routing, errors, and verification states without depending on
  QMD or Lossless-Claw availability.

Suggested shape:

- healthy mock backend,
- unhealthy mock backend,
- backend that supports search/get but not verify,
- backend that returns missing pointer,
- backend that returns stale pointer.

### LCM Fixture Strategy

Purpose:

- Test the Lossless-Claw adapter without committing private transcript content.

Preferred approach:

- Use synthetic test conversation data if the local LCM tool path supports an
  isolated test store.
- Otherwise use a mock LCM adapter for contract tests and one local-only
  integration eval that is excluded from public fixtures.

Public repo requirement:

- Do not commit private conversation exports.
- Do not make public eval success depend on a private conversation id.

## Eval Matrix

### EVAL-001: Request Schema Contract

Agent task:

- Define the normalized request schema and result schema.

Programmatic item:

- Request normalization.
- Shared request/result contracts.

Eval type:

- Unit.
- Schema validation.

Fixtures:

- valid search request,
- valid get request,
- valid verify request,
- invalid operation,
- missing query,
- unsupported backend hint.

Pass criteria:

- Valid inputs normalize into one internal request shape.
- Invalid inputs return structured validation errors.
- CLI-shaped and MCP-shaped inputs normalize equivalently.

Failure meaning:

- Downstream routing cannot be trusted until the request contract is stable.

### EVAL-002: Backend Registry Contract

Agent task:

- Implement backend registration, capability declaration, and health reporting.

Programmatic item:

- Backend registry.
- Capability model.

Eval type:

- Unit.
- Contract.

Fixtures:

- QMD backend definition.
- Lossless-Claw backend definition.
- healthy mock backend.
- unavailable mock backend.

Pass criteria:

- Registry lists all registered backends.
- Each backend declares supported operations.
- Health status is returned per backend.
- Duplicate backend ids are rejected.

Failure meaning:

- MemoryCore cannot make routing decisions safely.

### EVAL-003: Structured Error Model

Agent task:

- Implement standard errors for validation, unsupported operation, missing
  backend, backend unavailable, pointer missing, verification unsupported, and
  unknown failure.

Programmatic item:

- Shared error model.

Eval type:

- Unit.
- Contract.

Fixtures:

- unsupported operation request,
- missing backend request,
- unhealthy backend request,
- missing pointer response,
- backend exception.

Pass criteria:

- Every failure returns machine-readable `code`, human-readable `message`, and
  stable `category`.
- No known failure path returns a successful empty result.

Failure meaning:

- Operators and agents will misread system failure as memory absence.

### EVAL-004: Deterministic Router

Agent task:

- Implement explicit backend routing and simple auto-selection.

Programmatic item:

- Router.

Eval type:

- Unit.
- Integration with mock backends.

Fixtures:

- file/corpus search request,
- transcript/continuity search request,
- explicit QMD request,
- explicit Lossless-Claw request,
- unsupported operation pair.

Pass criteria:

- File/corpus recall routes to QMD.
- Transcript/continuity recall routes to Lossless-Claw.
- Explicit backend selection is honored when supported.
- Unsupported operation/backend combinations fail clearly.

Failure meaning:

- The control plane is acting as a random proxy instead of a policy layer.

### EVAL-005: QMD Adapter Contract

Current public-safe scaffold:

- Static QMD-shaped fixtures live under `fixtures/qmd/`.
- `memorycore/qmd_adapter.py` normalizes mocked QMD search, get, missing
  pointer, and health output into the shared result/error contract.
- `scripts/validate_mvp_qmd_adapter.py` verifies that the adapter preserves
  pointers, snippets, content, ranking, and non-overclaiming verification
  states without calling a live QMD index.

Agent task:

- Implement QMD adapter methods: `search`, `get`, `verify`, `health`.

Programmatic item:

- QMD adapter.

Eval type:

- Adapter unit with mock QMD output.
- Local integration with fixture corpus when QMD is available.

Fixtures:

- QMD JSON search result fixture.
- QMD get result fixture.
- public fixture corpus indexed in a test collection if supported.

Pass criteria:

- Search returns normalized results with backend id, pointer, snippet, score or
  rank when available, and verification state.
- Get resolves a pointer to source content or source metadata.
- Verify reports `verified`, `missing`, `unsupported`, or `unknown`.
- QMD command/API failures become structured backend errors.

Failure meaning:

- MemoryCore cannot prove local corpus recall through a real backend.

Live boundary:

- See `docs/LIVE_BACKEND_BOUNDARIES.md`.
- The first live QMD path should be a local-only adapter mode over the `qmd`
  CLI, keeping public evals fixture-only and preserving the shared result
  contract.

### EVAL-006: Lossless-Claw Adapter Contract

Current public-safe scaffold:

- Static Lossless-Claw-shaped fixtures live under `fixtures/lcm/`.
- `memorycore/lcm_adapter.py` normalizes mocked grep/search, expand/get,
  missing pointer, unavailable tool, and health output into the shared
  result/error contract.
- `scripts/validate_mvp_lcm_adapter.py` verifies that the adapter preserves
  summary/message/conversation pointers, snippets, citations, recall mode, and
  non-overclaiming verification states without calling live lossless-claw tools
  or a transcript store.

Agent task:

- Implement Lossless-Claw adapter methods: `search`, `get`, `verify`, `health`.

Programmatic item:

- Lossless-Claw adapter.

Eval type:

- Adapter unit with mocked LCM tool output.
- Local-only integration against synthetic or configured LCM test data.

Fixtures:

- LCM grep-style result fixture.
- LCM expand-query result fixture.
- missing summary/message pointer fixture.
- unavailable LCM tool fixture.

Pass criteria:

- Search returns normalized results with backend id, pointer or summary id,
  snippet/summary text when available, recall mode, and verification state.
- Get resolves an LCM pointer when supported.
- Verify does not overclaim if LCM cannot prove freshness.
- Missing or unavailable LCM paths produce structured errors.

Failure meaning:

- MemoryCore cannot prove transcript continuity routing and must remain QMD-only.

Live boundary:

- See `docs/LIVE_BACKEND_BOUNDARIES.md`.
- The first live Lossless-Claw path should use host-injected tool functions, not
  public package imports or committed transcript data.

### EVAL-007: Provenance Pointer Ledger

Current public-safe scaffold:

- `memorycore/provenance_ledger.py` creates JSONL ledger records from
  normalized QMD/LCM result metadata.
- Ledger records keep request id, backend id, operation, pointer, verification
  state, timestamp, result index, status, and structured error code/category
  when applicable.
- `scripts/validate_mvp_provenance_ledger.py` verifies QMD result pointers, LCM
  summary pointers, missing-pointer error records, no snippet/content storage,
  JSONL append, and read-back by ledger id using only temporary public-safe
  data.

Agent task:

- Implement persistent provenance pointer records.

Programmatic item:

- Provenance ledger.

Eval type:

- Unit.
- Persistence.

Fixtures:

- QMD normalized result.
- LCM normalized result.
- missing pointer result.

Pass criteria:

- Each routed result can create a ledger record with request id, backend id,
  operation, pointer, verification state, and timestamp.
- Ledger records do not store raw private content by default.
- Ledger records can be read back by id.

Failure meaning:

- MemoryCore is returning useful answers but not preserving inspectable
  provenance.

### EVAL-008: Verification State Contract

Current public-safe scaffold:

- `memorycore/verification_state.py` defines the shared verification-state
  vocabulary and normalization helpers.
- `scripts/validate_mvp_verification_state.py` checks verified, stale, missing,
  unsupported, and unknown states against static QMD/LCM/mock fixtures.
- The scaffold explicitly keeps missing pointers, unsupported verification, and
  backend timeouts from returning `verified`.

Agent task:

- Implement common verification behavior across adapters.

Programmatic item:

- Verification contract.

Eval type:

- Unit.
- Adapter integration.

Fixtures:

- verified pointer,
- stale pointer,
- missing pointer,
- backend with no verification support,
- backend timeout.

Pass criteria:

- Verification states are limited to `verified`, `stale`, `missing`,
  `unsupported`, and `unknown`.
- Missing pointers never return `verified`.
- Unsupported verification never returns `verified`.
- Backend timeouts return `unknown` or structured backend error.

Failure meaning:

- The product cannot make source-backed context claims safely.

### EVAL-009: Request/Result Audit

Current public-safe scaffold:

- `memorycore/audit_log.py` creates JSONL audit records from normalized
  requests and results.
- Audit records keep request id, client surface, operation, normalized intent,
  selected backend, result count, pointer ids, verification state, error
  code/category, timestamp, and status.
- `scripts/validate_mvp_audit_log.py` verifies successful QMD/LCM searches,
  unsupported verification, unavailable backend, validation error, JSONL append,
  recent read-back, and no snippet/content/citation storage using only static
  public-safe fixtures.

Agent task:

- Implement audit records for successful and failed requests.

Programmatic item:

- Audit log.

Eval type:

- Unit.
- Persistence.

Fixtures:

- successful QMD search,
- successful LCM search,
- unsupported operation,
- backend unavailable,
- validation error.

Pass criteria:

- Every routed request creates an audit record.
- Failed requests create audit records when the request reaches routing.
- Records include request id, client surface, operation, normalized intent,
  selected backend when any, result count, pointer ids, verification state,
  error state, and timestamp.
- Raw private content is not stored by default.

Failure meaning:

- Routing decisions cannot be debugged or inspected after the fact.

### EVAL-010: CLI Developer Surface

Current public-safe scaffold:

- `memorycore/cli.py` provides a fixture-only CLI with JSON output for
  `list-backends`, `health`, `search`, `get`, `verify`, and recent `audit`
  records.
- The CLI writes request/result audit records to a configurable JSONL path for
  routed `search`, `get`, and `verify` operations.
- `scripts/validate_mvp_cli.py` invokes the CLI against static QMD, LCM, mock
  backend, and temporary audit fixtures only; it does not call live QMD,
  Lossless-Claw, Burrow, OpenClaw, or the public-safe eval runner.

Agent task:

- Implement CLI commands for MVP operations.

Programmatic item:

- CLI.

Eval type:

- Command integration.
- Golden-path smoke.

Required commands:

- list backends,
- health,
- search,
- get,
- verify,
- show recent audit records.

Fixtures:

- mock backend test mode,
- QMD fixture corpus when available.

Pass criteria:

- CLI can run search -> get -> verify -> audit using mock fixtures.
- CLI can run QMD search against the fixture corpus when QMD is available.
- CLI exits nonzero on structured failures.
- CLI supports JSON output for agent use.

Failure meaning:

- Developers cannot operate or debug the MVP without a higher-level client.

### EVAL-011: MCP Tool Surface

Current public-safe scaffold:

- `memorycore/mcp_surface.py` defines MCP-shaped tool descriptors and local
  contract calls for `memorycore_search`, `memorycore_get`,
  `memorycore_verify`, and `memorycore_health`.
- Static MCP request fixtures live under `fixtures/mcp/`.
- `scripts/validate_mvp_mcp_surface.py` checks the MCP-shaped surface against
  static QMD, LCM, mock backend, and temporary audit fixtures only; it does not
  start an MCP server or call live QMD, Lossless-Claw, Burrow, OpenClaw, or the
  public-safe eval runner.

Agent task:

- Implement MCP tools for MVP operations.

Programmatic item:

- MCP server/tool surface.

Eval type:

- Tool contract.
- MCP smoke.

Required tools:

- `memorycore_search`
- `memorycore_get`
- `memorycore_verify`
- `memorycore_health`

Fixtures:

- MCP request fixtures mirroring CLI requests.
- mock backend test mode.

Pass criteria:

- MCP tools return the same normalized result shape as CLI JSON.
- MCP search/get/verify/health work against mock fixtures.
- Tool failures return structured errors.

Failure meaning:

- Agent clients cannot use MemoryCore without bespoke glue.

### EVAL-012: OpenClaw Integration Smoke

Current prep scaffold:

- `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md` defines the fixture-only smoke
  boundary, preconditions, required observations, and stop conditions.
- The smoke plan includes a pre-execution checklist and run-note template so
  approval, caller path, backend mode, entrypoint, audit file, cleanup, and
  stop-condition reviewer are explicit before execution.
- The plan is documentation only and has not been executed while the current
  OpenClaw/Burrow integration hard stop remains active.

Agent task:

- Implement the first OpenClaw integration path.

Programmatic item:

- OpenClaw plugin or runtime integration.

Eval type:

- Local integration smoke.

Fixtures:

- mock backend test mode.
- QMD fixture corpus when available.

Pass criteria:

- OpenClaw can call MemoryCore search or verify.
- The response includes backend id, pointer, verification state, and audit id.
- Failure states are visible to the OpenClaw caller.

Failure meaning:

- MemoryCore remains a library/tool, not a usable OpenClaw runtime component.

### EVAL-013: End-To-End Golden Path

Agent task:

- Assemble the complete MVP loop across implemented surfaces.

Programmatic item:

- MVP integration.

Eval type:

- End-to-end.

Fixtures:

- public fixture corpus,
- mock LCM or synthetic local LCM test data,
- mock backend failure case.

Pass criteria:

- CLI can search QMD, get a pointer, verify it, and show audit.
- MCP can perform the same search/get/verify/health loop.
- OpenClaw can perform at least search or verify through the integration path.
- One successful and one failed request are both inspectable in audit.
- No private content is required for public evals.

Failure meaning:

- Individual pieces may work, but the MVP is not yet functional.

## Suggested Agent Work Packets

### Packet A: Contracts And Fixtures

Owns:

- request/result schemas,
- error model,
- fixture corpus,
- mock backend fixtures.

Primary evals:

- EVAL-001,
- EVAL-003.

Exit criteria:

- Other agents can develop against stable contracts without needing real QMD or
  LCM.

### Packet B: Registry And Router

Owns:

- backend registry,
- capability model,
- deterministic routing.

Primary evals:

- EVAL-002,
- EVAL-004.

Exit criteria:

- Mock backends can be registered, selected, rejected, and health-checked.

### Packet C: QMD Path

Owns:

- QMD adapter,
- QMD fixture integration,
- QMD verification behavior.

Primary evals:

- EVAL-005,
- QMD portion of EVAL-013.

Exit criteria:

- A real or fixture-indexed file can be searched, returned, verified, and
  ledgered.

### Packet D: Lossless-Claw Path

Owns:

- LCM adapter,
- LCM mock fixtures,
- optional local-only synthetic LCM integration.

Primary evals:

- EVAL-006,
- LCM portion of EVAL-013.

Exit criteria:

- LCM search/get/verify behavior is contract-complete even when verification is
  unsupported or local-only.

### Packet E: Provenance And Audit

Owns:

- provenance ledger,
- verification state persistence,
- audit log.

Primary evals:

- EVAL-007,
- EVAL-008,
- EVAL-009.

Exit criteria:

- Every route can leave inspectable provenance and audit records without raw
  private content storage.

### Packet F: CLI

Owns:

- local CLI surface,
- JSON output,
- command smoke tests.

Primary evals:

- EVAL-010.

Exit criteria:

- A developer can run the MVP loop locally from shell commands.

### Packet G: MCP Surface

Owns:

- MCP server/tools,
- MCP contract tests.

Primary evals:

- EVAL-011.

Exit criteria:

- Agent clients can call the MVP operations through MCP with the same result
  shape as CLI JSON.

### Packet H: OpenClaw Integration

Owns:

- first OpenClaw integration path,
- integration smoke test.

Primary evals:

- EVAL-012.

Exit criteria:

- OpenClaw can perform at least search or verify and see provenance-backed
  structured output.

### Packet I: End-To-End Assembly

Owns:

- final MVP golden path,
- cross-surface consistency,
- public-safe eval runner.

Primary evals:

- EVAL-013.

Exit criteria:

- CLI, MCP, and OpenClaw prove the same minimal functional loop.

## Eval Order

Recommended build/eval order:

1. Contracts and fixtures.
2. Registry and router.
3. QMD adapter.
4. Provenance ledger and verification contract.
5. Audit log.
6. CLI.
7. Lossless-Claw adapter.
8. MCP tools.
9. OpenClaw integration.
10. End-to-end golden path.

Reason:

- QMD is the fastest real backend to prove source-backed recall.
- LCM is essential for the thesis, but its public-safe eval path needs more
  care.
- CLI should exist before MCP/OpenClaw so failures are easy to isolate.

## Minimum MVP Eval Command

The final implementation should provide one command that runs the public-safe
eval suite:

```bash
memorycore eval --public-safe
```

The command should report:

- passed eval ids,
- failed eval ids,
- skipped local-only eval ids,
- backend availability,
- fixture corpus status,
- audit/provenance record count created during the run.

## Non-MVP Eval Backlog

Do not build these before the MVP loop passes:

- Hermes plugin evals.
- Codex plugin evals.
- ChatGPT/Claude app evals.
- REST and Pinecone-style compatibility evals.
- Notion, Drive, Excel, S3, NFS, CIFS, or filesystem substrate evals.
- Backup/migration mutation evals.
- Mirroring/splitting policy evals.
- Insight plugin evals.
- Context visualization evals.
- Token/cost diagnostic evals.
