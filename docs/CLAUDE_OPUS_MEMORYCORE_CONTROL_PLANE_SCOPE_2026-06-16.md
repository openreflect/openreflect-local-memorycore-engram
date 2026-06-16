# Claude Opus MemoryCore Control-Plane Scope Assessment

Date: 2026-06-16
Project: OpenReflect Local MemoryCore / Engram
Status: Associate assessment
Reviewer lane: Claude Code associate, `claude-opus-4-8`
Source basis:

- `docs/MEMORYCORE_SOFTWARE_SPEC.md`
- `docs/CLAUDE_OPUS_MEMORYCORE_FEASIBILITY_ASSESSMENT_2026-06-16.md`
- `docs/PRD.md`
- `docs/ARCHITECTURE.md`
- `research/memory-virtualization-write-adapter-research-2026-06-15.md`
- `research/memory-stack-feature-spec-2026-06-15.md`

## Core Question

Mitchell asked whether "control plane" means only a switch/router, or whether
the initial release should have a greater feature set.

Opus's answer: **greater than a switch, strictly less than a replacement
memory store.**

MemoryCore v0.1 should own routing decisions, capability negotiation,
provenance pointers, verification state, and request/result audit. It should
not own backend memory content.

## Feasibility Verdict

The control-plane architecture is technically feasible if v0.1 is narrowed to
QMD + Lossless-Claw adapters, pointer-only provenance, request auditing, and
verification.

The current spec is not coherent as written because its top-level positioning
now says routing/control plane, while the storage model still defines
replacement-store tables for messages, summaries, observations, embeddings,
reasoning jobs, and context packets.

Opus's blocking judgment:

> The content tables in the current spec are the bug, not the feature.

Keeping the replacement-store design would force MemoryCore to reimplement QMD,
Lossless-Claw, and Honcho write physics while breaking the very provenance
model it is supposed to protect.

## Control Plane Scope

MemoryCore is not merely a dumb switch.

A switch forwards. A control plane decides, tracks capability and topology,
enforces policy, and records provenance and audit state.

The dividing line for v0.1 is:

```text
MemoryCore owns pointers and decisions, not memory content.
```

### Must Own In v0.1

- Backend registry and capability probing.
- Intent normalization for `search`, `get`, and `verify`.
- Routing policies: `specific_backend`, `auto`, and fanout for search.
- Provenance pointer ledger.
- Verification contract: `current`, `stale`, or `unsupported`.
- Request/result audit trail.
- Graceful degradation when a backend is down.
- QMD and Lossless-Claw read adapters.

### Should Own In v0.1

- Logical identity mapping across backends.
- Cross-backend doctor/status command.
- One gated Lossless-Claw write path through the native LCM engine, if writes
  are approved for MVP.
- Optional bounded snippet cache, capped and treated as disposable shadow text,
  if Mitchell explicitly approves.

### Defer

- Owned content tables.
- Reasoning engine.
- Summary generation and summary DAG.
- Context packet assembly.
- Honcho and gbrain adapters.
- Model, browser, email, agent, and coding-task lanes.
- Operator UI.
- MemoryCore-authored git commits.

## Proposed v0.1 Feature Set

Ship:

- Adapter registry and capability probing.
- QMD adapter: `status`, `search`, `get`, `verify`.
- Lossless-Claw adapter: `status`, `search`, `get`, `verify`.
- Provenance pointer ledger.
- Verification contract.
- Request/result audit log.
- Routing with graceful degradation.
- CLI commands: `register`, `status`, `search`, `get`, `verify`, `doctor`.
- Thin MCP tools: `memory_search`, `memory_get`, `memory_verify`,
  `memory_status`.
- Public-safe validation inherited from the current PRD.

Do not ship:

- MemoryCore-owned document/message/summary/observation storage.
- Reasoning or observation extraction.
- Summary DAG generation.
- Context packet synthesis.
- Honcho or gbrain adapters.
- Model/browser/email/agent/coding lanes.
- HTTP API, unless needed later.
- Operator UI.
- MemoryCore-created git commits.

Recommended first backend assumption:

- QMD is read/verify only.
- Lossless-Claw is read/verify, with one optional gated write path.
- Provenance is pointer-only by default.

## Required Spec Corrections

### Purpose

Replace replacement-store wording such as:

```text
MemoryCore is a singular local-first product that performs the daily memory work
currently split across QMD, Lossless-Claw, and Honcho.
```

with:

```text
MemoryCore v0.1 is a backend memory control plane. It routes, verifies, and
preserves provenance over existing memory substrates rather than replacing their
native stores.
```

### Product Modules

Replace the six owned modules with control-plane modules:

- Adapter registry.
- Policy router.
- Provenance ledger.
- Verification engine.
- Request/result audit.
- Operator/API surface.

Move indexing, transcript/context, and reasoning sections into a backend-owned
capabilities appendix.

### Storage Model

Replace the current required tables with control-plane tables only:

- `backends`
- `provenance_pointers`
- `requests`
- `result_refs`
- `identity_map`
- `verifications`
- `schema_migrations`

Move the existing `memory_records`, `messages`, `message_parts`, `summaries`,
`summary_edges`, `summary_sources`, `observations`, `observation_sources`,
`embeddings`, `index_jobs`, `reasoning_jobs`, and `context_packets` sections
into a non-normative appendix labeled backend-owned/non-MVP.

### I/O Grid

Narrow the v0.1 grid to memory, context, retrieval, and provenance lanes.

Move model routing, browser/CDP, email/calendar, agent dispatch, and coding
work orders to future scope.

Also fix taxonomy: `RecallIndex` and `SemanticIndex` are service lanes, not
normalized input event types.

## Open Decisions For Mitchell

1. Ratify v0.1 as a routing control plane, not a replacement store.
2. Decide whether v0.1 is read/verify-only or includes one gated LCM write path.
3. Decide pointer-only versus bounded disposable snippet cache.
4. Decide whether MemoryCore owns canonical peer/session/collection identity or
   defers to backend-native ids.
5. Decide whether MemoryCore creates git commits or only records backend-supplied
   pointers and hashes.
6. Decide MCP-first versus HTTP-first surface. Opus recommends MCP-first.
7. Decide implementation language. Opus recommends TypeScript/Bun because QMD,
   LCM, and gbrain are TypeScript-aligned.

## First Five Implementation Tasks

1. **Control-plane schema and migration runner**
   - Acceptance: `init` creates only the seven control-plane tables.
   - Acceptance: migrations are idempotent.
   - Acceptance: tests assert no `messages`, `summaries`, or `observations`
     tables exist in MemoryCore.

2. **Adapter interface, registry, and capability probing**
   - Acceptance: registering a stub adapter persists across restart.
   - Acceptance: `status` lists capabilities.
   - Acceptance: a failed stub reports `down`.

3. **QMD adapter**
   - Acceptance: search returns `backend_id`, `backend_ref`, provenance, score,
     and rank.
   - Acceptance: `get` fetches live content from QMD, not MemoryCore state.
   - Acceptance: `verify` returns `current` before source mutation and `stale`
     after source mutation.

4. **Routing and audit**
   - Acceptance: fanout search across QMD plus a down stub returns QMD results.
   - Acceptance: skipped/down backends are recorded in `requests`.
   - Acceptance: latency and selected backend ids are recorded.

5. **Lossless-Claw adapter**
   - Acceptance: read/search returns cited continuity references.
   - Acceptance: verify confirms current lineage.
   - Optional write acceptance: a message write routes to LCM and MemoryCore
     stores only a pointer, never the message content.

## Operational Judgment

It is a control plane, not a switch. Delete the content tables, keep the
pointer/verification/routing state, and build QMD + Lossless-Claw read/verify
first.
