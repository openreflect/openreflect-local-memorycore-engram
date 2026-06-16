# MemoryCore PRD

Date: 2026-06-17
Status: Draft v0.2

## Product Thesis

MemoryCore is a local-first memory control plane for source-backed context. It
routes memory work across backends, preserves provenance, verifies freshness,
and exposes context shaping through app and plugin surfaces people can actually
use.

The product is not only for infrastructure power users. Power users are the
first buyers and testers because they feel memory failure sharply, but the
larger value is making context shaping available inside normal AI workflows:
chat apps, local agents, desktop assistants, and plugins.

## Target Users

Primary early users:

- AI builders running local or persistent agents.
- Operators who manage multiple memory systems and need provenance they can
  inspect.
- Researchers and technical founders comparing memory substrates.
- OpenReflect and Empathos developers building source-backed context systems.

Important expansion users:

- Knowledge workers who use ChatGPT, Claude, or similar chat interfaces and need
  better continuity than project folders or ad hoc saved chats.
- Teams that need private, portable working memory across documents, chats, and
  tools.
- Non-engineer power users who understand the value of controlling context even
  if they do not want to operate QMD, Lossless-Claw, Hermes, or OpenClaw
  directly.

## Core Product Shape

MemoryCore should be experienced as:

- A chat/app interface for context selection, memory inspection, and memory
  movement.
- A direct plugin for Hermes, OpenClaw, and Codex.
- An MCP surface for agent clients.
- A narrow local API for search, get, verify, route, mirror, split, backup, and
  migration workflows.

The ChatGPT-style app surface matters because it makes MemoryCore legible to
users who already understand apps inside a chat interface. The local runtime and
plugin surfaces matter because serious users need MemoryCore embedded directly
where agents already work.

## Distribution Surfaces

MemoryCore should be packaged for the places users already choose tools:

- ChatGPT-style app directories.
- Codex plugin directories.
- OpenClaw plugin/runtime configuration.
- Hermes plugin/runtime configuration.
- MCP client registries.

The Codex plugin surface is especially important because it presents MemoryCore
beside work tools such as documents, mail, repositories, drives, and task
systems. That is the right mental category: MemoryCore is a context-shaping work
tool, not only an infrastructure daemon.

## Goals

- Route memory requests to appropriate backends based on capability, policy,
  provenance requirements, freshness, cost, and privacy.
- Preserve source pointers and verification state for every routed result.
- Support QMD and Lossless-Claw as initial read/search/get/verify backends.
- Provide first-class OpenClaw integration and a usable MCP surface.
- Prepare direct Hermes and Codex plugin paths as core product surfaces, not
  afterthoughts.
- Make context shaping inspectable enough that users can understand why a piece
  of context was included, omitted, stale, or moved.
- Keep backup and migration on the product path as a high-value continuity
  feature.

## Non-Goals

- Do not become a generic connector marketplace.
- Do not compete with Zapier, Make, Drive search, Notion AI, vector databases,
  or agent frameworks on their own terms.
- Do not flatten all memory-bearing substrates into one replacement database.
- Do not treat summaries, embeddings, or derived observations as authoritative
  without source pointers.
- Do not make policy prose a substitute for small buildable tasks and acceptance
  tests.

## v0.1 Requirements

- Backend registry with capability probing.
- QMD adapter for read/search/get/verify.
- Lossless-Claw adapter for read/search/get/verify.
- Provenance pointer ledger.
- Request/result audit log.
- Deterministic routing for specific-backend and simple auto-selection flows.
- MCP interface for agent clients.
- Initial OpenClaw plugin/integration path.
- CLI or local developer surface for direct testing.

## v0.1.5 Requirements

- Hermes plugin/integration path.
- Adapter contract hardening based on OpenClaw and Hermes usage.
- Graceful degradation when a backend is absent, stale, or unhealthy.
- Optional gated write/import path only if source ownership and rollback rules
  are clear.

## v0.2 Requirements

- Mirroring and splitting policies.
- Backup/migration dry-run plans.
- Stronger identity mapping across backends.
- Early insight-plugin lane for source-backed derived observations.
- Codex plugin path if the v0.1/v0.1.5 adapter contract holds.

## Later Requirements

- ChatGPT and Claude app/plugin packaging.
- REST API and Pinecone-style compatibility where it supports adoption without
  making MemoryCore look like only a vector database.
- Nontraditional memory substrates such as Notion, Google Drive, spreadsheets,
  filesystem shares, and object stores.
- Visualizations for provenance, context selection, compression, omission,
  staleness, and token/cost impact.

## Success Criteria

- A user can ask MemoryCore for context and see which backend supplied it, why it
  was selected, and how to verify it.
- OpenClaw can use MemoryCore through a real integration path, not a mock.
- MCP clients can query MemoryCore without custom glue.
- QMD and Lossless-Claw remain backend owners of their native data while
  MemoryCore owns routing, provenance pointers, verification state, and audit.
- The PRD, roadmap, and software spec agree on the control-plane boundary.
- The repo contains no private paths, account IDs, transcript exports, or
  secrets.
