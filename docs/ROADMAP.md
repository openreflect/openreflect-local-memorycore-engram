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

### Out-Of-The-Box Integrations And Endpoints

MemoryCore should ship with useful integration surfaces rather than expecting
every client or agent system to build a custom adapter.

These integrations fall into two categories:

1. Clients and runtimes that call MemoryCore.
2. Memory substrates that MemoryCore can route to, mirror, split, index, back
   up, migrate, or verify.

Candidate client/runtime integrations:

- OpenClaw.
- Hermes.
- Pi-Agent.
- Codex.
- ChatGPT.
- Claude Desktop.
- MCP clients.
- REST API clients.
- OpenAI plugins/apps.
- Claude plugins/apps.
- Miniapps.

Candidate protocol and storage endpoints:

- REST API.
- MCP.
- Embeddings/vector-store style APIs, including Pinecone-like interfaces.
- Filesystem-style mounts, eventually including NFS and CIFS.
- Object stores such as S3.

The v0.1 surface should stay narrow enough to prove the control-plane model.
MCP and CLI are likely first because agent clients can use them immediately.
REST and Pinecone-style APIs are strategically important because they let
existing memory-aware tools treat MemoryCore as a familiar backend without
learning the internal adapter model.

OpenAI and Claude plugins/apps could be a major adoption lane because they make
MemoryCore available inside model-native workflows instead of only local agent
runtimes.

### Nontraditional Memory Substrates

MemoryCore should eventually abstract nontraditional memory formats and work
surfaces as memory substrates.

Examples:

- Notion.
- Excel and spreadsheets.
- Google Drive.
- Docs and document stores.
- Browser-captured pages.
- Object stores.
- Filesystem shares.

The key idea is not to flatten all of these into one database. The key idea is
to normalize how they are addressed, indexed, verified, routed, backed up, and
migrated.

This expands MemoryCore from "memory backend router" to "memory fabric." A
spreadsheet cell, Notion block, Google Drive document, S3 object, QMD document,
LCM transcript message, and Honcho observation are not the same kind of memory,
but MemoryCore can still give them common control-plane treatment:

- stable identity,
- provenance pointer,
- capability description,
- privacy class,
- freshness/staleness check,
- route policy,
- optional mirror/split policy,
- backup/migration policy.

This is later than v0.1, but it is central to the larger product shape.

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
- Initial OpenClaw integration path.

Explicitly out of scope:

- Owned messages, summaries, observations, embeddings, or context packets.
- Replacement memory database.
- Reasoning engine.
- Agent framework or sandbox.
- Broad model/browser/email/tool routing.
- Broad third-party SaaS substrates such as Notion, Drive, and spreadsheets.

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
- Start adding selected runtime integrations beyond OpenClaw if the control
  plane boundary is stable.

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
- Which endpoint comes first after MCP/CLI: REST, Pinecone-style API, ChatGPT,
  Claude Desktop, or OpenAI/Claude plugin/app packaging?
- Which nontraditional substrate should be the first proof case: Notion,
  Google Drive, Excel/spreadsheets, filesystem mount, or S3?
