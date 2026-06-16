# MemoryCore Roadmap

Date: 2026-06-16
Status: Working roadmap

This roadmap is intentionally provisional. The current architectural decision is
that MemoryCore v0.1 is a backend memory control plane: more than a switch, less
than a replacement memory store.

## Core Features

These are not yet fully mapped to releases.

### Routing

MemoryCore should route memory operations to the right backend based on intent,
capability, provenance requirements, privacy class, freshness, and backend
health.

Examples:

- Route file/corpus recall to QMD.
- Route transcript continuity recall to Lossless-Claw.
- Route derived peer/session memory to Honcho or similar insight backends.
- Route page/knowledge-base writes to a page/brain backend when available.

### Mirroring

MemoryCore may mirror selected memory operations across compatible backends when
policy allows it.

Mirroring is not default duplication. It should be explicit, policy-governed,
and provenance-aware.

Possible uses:

- Mirror durable source pointers for resilience.
- Mirror selected public-safe records into a portable store.
- Mirror audit/provenance metadata without mirroring private content.

### Splitting

MemoryCore should support splitting memory work across backends when one event
has multiple valid memory consequences.

Example:

```text
chat event
  -> Lossless-Claw for transcript continuity
  -> Honcho-style backend for later insight derivation
  -> QMD only if a durable file/report is produced and indexed
```

The split must preserve backend-native invariants and record what happened.

### Backend Selection

MemoryCore should select specific memory systems for specific types of memories.

Selection criteria may include:

- Memory kind: transcript, file, source artifact, observation, peer/session
  representation, report, external import.
- Operation: search, get, verify, append, import, derive, backup, migrate.
- Backend capabilities.
- Privacy class.
- Freshness/staleness state.
- Cost and latency.
- Source authority.

### Backend Control

MemoryCore should expose controlled backend operations without taking ownership
of backend data planes.

Candidate controls:

- Register/unregister backend.
- Health check and doctor.
- Capability probe.
- Enable/disable backend for a policy lane.
- Trigger reindex or refresh where the backend supports it.
- Trigger compaction/maintenance where the backend supports it.
- Put a backend into observe-only mode.

### Backup And Migration

Backup and migration are high-value features.

MemoryCore should eventually support safe backup and migration of memory
substrates, but this must be provenance-aware and backend-native. The control
plane should not silently copy opaque private memory blobs across trust
boundaries.

Potential feature shape:

- Export backend registry, provenance pointers, identity maps, and verification
  state.
- Export public-safe or explicitly selected memory artifacts.
- Produce migration plans before mutation.
- Verify post-migration source hashes and backend references.
- Support dry-run and rollback-friendly migration workflows.

This is a hot feature because it turns MemoryCore from a router into continuity
infrastructure without making it a replacement store.

## Release Hypotheses

### v0.1: Control Plane Foundation

Goal: prove the pointer/provenance/routing model over real backends.

Likely scope:

- Adapter registry.
- Capability probing.
- Policy router.
- QMD read/get/verify adapter.
- Lossless-Claw read/get/verify adapter.
- Optional gated Lossless-Claw write path.
- Provenance pointer ledger.
- Request/result audit.
- Basic CLI and/or MCP tools.
- Backend health and graceful degradation.

Explicitly out of scope:

- Owned messages, summaries, observations, embeddings, or context packets.
- Replacement memory database.
- Reasoning engine.
- Agent framework or sandbox.
- Broad model/browser/email/tool routing.

### v0.2: Plugin Insight Agents

Goal: add adaptive, autonomous insight mining without collapsing MemoryCore into
the insight engine itself.

Plugin insight agents should mine memory for patterns, risks, project state,
relationship/context changes, stale assumptions, and useful derived observations.

Important boundary:

```text
MemoryCore routes, records provenance, schedules/permits insight work, and
stores/verifies pointers. Insight plugins produce derived artifacts in their own
declared lanes.
```

Candidate capabilities:

- Register insight plugin.
- Declare input scopes and allowed backends.
- Run adaptive mining jobs.
- Produce derived observations with source pointers.
- Mark confidence and observation type.
- Re-verify derived claims against source pointers.
- Maintain quiet zones and privacy gates.

### Later: Visualization And Cost/Context Diagnostics

Goal: make context flow inspectable.

Possible visualizations:

- Where context came from.
- Why context was selected.
- Where compression occurred.
- What source material was omitted.
- Which backend contributed each context item.
- How routing decisions changed token load.
- Estimated token cost impact of different context strategies.
- Staleness and provenance views.

This should not be only decorative UI. The visualization should help operators
understand memory pressure, compression effects, provenance confidence, and
model-cost tradeoffs.

## Open Roadmap Questions

- Which backup/migration operations are safe for v0.1 versus v0.2?
- Should the first public-facing interface be MCP-first, CLI-first, or both?
- How much autonomous plugin work should run without explicit operator review?
- What policy language should govern mirroring and splitting?
- Which backend becomes the first source of derived insight: Honcho, gbrain, or
  a MemoryCore-native plugin lane?
