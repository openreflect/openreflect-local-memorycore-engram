# MemoryCore MVP Scope

Date: 2026-06-17
Status: Draft

## Definition

The MemoryCore MVP is the smallest functional control plane that proves
source-backed context routing over real memory backends.

It is not a flat, broken subset of the full product. It is a narrow working
system with coherent feature boundaries:

- real backends,
- real routing decisions,
- real provenance pointers,
- real verification checks,
- real client access,
- clear failure behavior.

If a feature cannot be made functional in this slice, it stays out of the MVP
rather than shipping as decorative scaffolding.

## MVP Thesis

MemoryCore v0.1 should answer one practical question:

```text
Given a memory request, can MemoryCore select an appropriate backend, retrieve
source-backed context, explain where it came from, verify whether it is fresh,
and expose that result through an agent-usable interface?
```

The MVP succeeds if QMD, Lossless-Claw, OpenClaw, and MCP prove that loop end to
end.

## Included Capabilities

### 1. Backend Registry

Capability:

- Register known memory backends.
- Describe each backend's supported operations.
- Report backend availability and health.

MVP backends:

- QMD.
- Lossless-Claw.

Required operations:

- `search`
- `get`
- `verify`
- `health`

Acceptance test:

- A local command lists QMD and Lossless-Claw with capabilities and health
  status.
- If a backend is unavailable, MemoryCore reports that state without crashing or
  silently falling back.

Out of scope:

- Dynamic marketplace-style backend installation.
- Third-party SaaS substrate registration.
- Backend-owned maintenance workflows beyond health probing.

### 2. Request Normalization

Capability:

- Convert client input into a simple internal request shape.
- Preserve request intent, requested backend if specified, query text, and
  verification preference.

Minimum intents:

- search memory,
- get source by pointer,
- verify source freshness,
- ask for backend health.

Acceptance test:

- The same memory search can be submitted through CLI and MCP and becomes the
  same normalized request.

Out of scope:

- Natural-language planning.
- Multi-step reasoning.
- Autonomous task decomposition.

### 3. Deterministic Routing

Capability:

- Route a request to a specific backend when requested.
- Route simple auto-selection requests based on memory kind and backend
  capability.

Minimum routing rules:

- File/corpus recall routes to QMD.
- Transcript/conversation continuity recall routes to Lossless-Claw.
- Explicit backend requests override auto-selection if the backend supports the
  operation.
- Unsupported operations fail clearly.

Acceptance test:

- A QMD-style query routes to QMD.
- A transcript-continuity query routes to Lossless-Claw.
- An unsupported backend/operation pair returns a structured error.

Out of scope:

- Cost optimization.
- Fanout ranking across many backends.
- Learning-based routing.
- Complex policy language.

### 4. QMD Adapter

Capability:

- Search local indexed files.
- Return source pointers and concise snippets.
- Verify whether a returned source pointer still resolves.

Acceptance test:

- A known local document can be found through MemoryCore using QMD.
- The result includes backend id, source pointer, snippet, and verification
  state.

Out of scope:

- Reindex orchestration.
- Embedding management.
- QMD configuration mutation.

### 5. Lossless-Claw Adapter

Capability:

- Search or recall conversation continuity through the available LCM tool path.
- Return source or summary pointers where available.
- Verify whether the referenced source/summary still exists.

Acceptance test:

- A known conversation-memory query can be routed through MemoryCore to
  Lossless-Claw.
- The result includes backend id, pointer or summary reference, confidence or
  recall mode when available, and verification state.

Out of scope:

- Owning compaction.
- Replacing LCM summaries.
- MemoryCore-authored transcript storage.
- Ungated write paths.

### 6. Provenance Pointer Ledger

Capability:

- Record what backend answered a request.
- Record source pointers returned by the backend.
- Record verification state and timestamp.
- Record request/result metadata without copying private source content into a
  replacement memory store.

Acceptance test:

- After a query, an audit/provenance record exists showing request id, backend,
  operation, pointer, verification state, and timestamp.

Out of scope:

- Full content storage.
- User-profile memory.
- Derived observations.
- Long-term semantic memory owned by MemoryCore.

### 7. Verification Contract

Capability:

- Provide a consistent answer to: "Can this pointer still be resolved, and does
  the backend consider it fresh?"

Minimum states:

- `verified`
- `stale`
- `missing`
- `unsupported`
- `unknown`

Acceptance test:

- A valid pointer verifies as `verified`.
- A missing pointer returns `missing` rather than an empty successful result.
- A backend that cannot verify a pointer returns `unsupported`.

Out of scope:

- Deep claim-level truth checking.
- Cross-backend contradiction detection.
- Automated source repair.

### 8. Request/Result Audit

Capability:

- Record enough request/result metadata to debug routing and provenance.
- Avoid storing raw private content by default.

Minimum fields:

- request id,
- client surface,
- operation,
- normalized intent,
- selected backend,
- result count,
- pointer ids,
- verification state,
- error state if any,
- timestamp.

Acceptance test:

- A failed route and a successful route both produce inspectable audit records.

Out of scope:

- Analytics dashboard.
- User behavior tracking.
- Hosted telemetry.

### 9. MCP Interface

Capability:

- Expose MVP operations through MCP so agent clients can use MemoryCore without
  custom glue.

Minimum tools:

- `memorycore_search`
- `memorycore_get`
- `memorycore_verify`
- `memorycore_health`

Acceptance test:

- An MCP client can search memory, retrieve a pointer, verify it, and inspect
  backend health.

Out of scope:

- Full ChatGPT/Claude app packaging.
- Connector marketplace UX.
- Broad third-party client support.

### 10. OpenClaw Integration Path

Capability:

- Provide a first-class way for OpenClaw to call the MemoryCore MVP.
- Keep the interface thin enough that MemoryCore remains a product, not an
  OpenClaw-only internal component.

Acceptance test:

- OpenClaw can issue a MemoryCore search or verify request through the chosen
  integration path and receive a structured provenance-backed result.

Out of scope:

- Replacing OpenClaw's context engine.
- Replacing LCM.
- Routing all OpenClaw tools or models.

### 11. CLI Developer Surface

Capability:

- Provide a local operator surface for testing MVP behavior without a full app
  shell.

Minimum commands:

- list backends,
- search,
- get,
- verify,
- show audit record or recent audit records,
- health.

Acceptance test:

- A developer can run the whole MVP loop locally from the CLI.

Out of scope:

- Polished UI.
- Visualization.
- Multi-user administration.

## Explicit MVP Exclusions

The following are important product capabilities, but not MVP requirements:

- Hermes plugin path.
- Codex plugin path.
- ChatGPT or Claude app/plugin packaging.
- REST API beyond what is needed locally.
- Pinecone-style compatibility.
- Notion, Google Drive, Excel, S3, NFS, CIFS, or filesystem substrate adapters.
- Backup and migration execution.
- Mirroring and splitting policies.
- Insight plugins and derived observations.
- Context visualization.
- Cost/token diagnostics.
- Agent framework behavior.
- Sandbox or execution runtime behavior.
- MemoryCore-owned message, summary, embedding, or observation stores.

## MVP Build Cycles

### Cycle 1: Kernel Contract

Build:

- request schema,
- backend registry,
- capability model,
- health response,
- structured error model.

Done when:

- QMD and Lossless-Claw can be represented as registered backends with declared
  capabilities and health.

### Cycle 2: First Read Path

Build:

- QMD adapter,
- CLI search/get/verify,
- basic provenance pointer shape.

Done when:

- A real local file result can be found, returned, verified, and recorded.

### Cycle 3: Second Read Path

Build:

- Lossless-Claw adapter,
- transcript/continuity routing rule,
- normalized result shape across both backends.

Done when:

- QMD and Lossless-Claw both answer through the same MemoryCore request/result
  contract.

### Cycle 4: Audit And Verification Hardening

Build:

- request/result audit,
- verification state contract,
- graceful missing/stale/unsupported handling.

Done when:

- Successful and failed requests both leave useful records and never pretend an
  unverified result is verified.

### Cycle 5: Agent Surface

Build:

- MCP tools,
- OpenClaw integration path,
- smoke tests for agent-style calls.

Done when:

- OpenClaw and an MCP client can use MemoryCore for search/get/verify/health.

## MVP Success Definition

The MVP is complete when a user or agent can:

1. Ask MemoryCore for file or transcript memory.
2. Have MemoryCore select QMD or Lossless-Claw correctly.
3. Receive source-backed results with backend identity and pointers.
4. Verify those pointers through a consistent verification contract.
5. Inspect the audit trail for what happened.
6. Use the same loop from CLI, MCP, and OpenClaw.

That is minimal functional. It is not the whole product, but it is a real
product kernel.
