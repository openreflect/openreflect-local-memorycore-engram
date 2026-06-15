# Memory Virtualization Write Adapter Research

Date: 2026-06-15
Project: OpenReflect Local MemoryCore / Engram
Status: Draft v0.1
Verification: [SFV: VERIFIED] by local source inspection of cloned repositories.

## Source Corpus

Local source roots inspected:

- `research/source-repos/gbrain` at `090bb53`
- `research/source-repos/lossless-claw` at `d404eba`
- `research/source-repos/qmd` at `6366024`
- `research/source-repos/honcho` at `340175a`

This document narrows the product direction from "combine memory systems into one product" to "virtualize memory systems behind a stable fabric." The practical question is not "how do we rewrite every backend?" It is:

> How is each backend written to today, and what adaptive adapter can sit above it without breaking its native invariants?

## Working Thesis

MemoryCore should be a memory virtualization layer, analogous to storage virtualization.

The underlying memory systems remain distinct devices:

- QMD: local corpus index and retrieval device.
- Lossless-Claw: transcript continuity and context-compaction device.
- Honcho: peer/session reasoning and representation device.
- gbrain: page/knowledge-brain device with schema, capture, source, write-through, and retrieval tools.
- Engram: provenance and verification fabric across devices.

MemoryCore should expose one memory fabric:

1. Identify write intent.
2. Select compatible backends.
3. Translate into each backend's native write surface.
4. Preserve the backend's invariants.
5. Normalize returned identifiers into a common MemoryCore record envelope.
6. Verify source/provenance where possible.
7. Route reads and context assembly across backends using capability metadata.

## Adapter Design Principle

Do not mutate backend databases directly unless a backend has no safer write API and the adapter is explicitly in witness/read-only mode.

Every inspected system has important side effects around writes: indexing, queueing, embedding, deduplication, ordering, compaction lineage, source scoping, permissions, write-through, or provenance stamping. A fabric adapter must enter through those native write paths.

## Common Adapter Contract

Every backend adapter should declare capabilities rather than pretending all memories are symmetric.

Proposed capabilities:

- `append_message`: append ordered conversational records.
- `batch_append_message`: append multiple conversational records atomically or near-atomically.
- `put_document`: insert/update a durable document/page.
- `import_collection`: index/import a folder or corpus.
- `reindex`: refresh an existing corpus index from source.
- `embed`: generate or refresh embeddings.
- `derive`: trigger summarization, representation, or observation generation.
- `search`: query backend-native memory.
- `get`: fetch a cited item by backend-native id.
- `verify`: check whether a cited item is still current.
- `status`: expose health, counts, and staleness.
- `observe_only`: read backend state without writing.

The fabric should use a normalized operation envelope:

```json
{
  "intent": "append_message | put_document | import_collection | derive | search | get | verify",
  "target_policy": "auto | specific_backend | fanout | witness_only",
  "content": {},
  "source": {
    "kind": "chat | file | transcript | page | tool | external",
    "uri": "string",
    "hash": "optional",
    "timestamp": "optional"
  },
  "identity": {
    "workspace": "optional",
    "session": "optional",
    "peer": "optional",
    "collection": "optional",
    "source_id": "optional"
  },
  "constraints": {
    "preserve_order": true,
    "allow_derive": true,
    "allow_embedding": true,
    "require_provenance": true
  }
}
```

## QMD Write Model

### Native Role

QMD is primarily a local corpus search/index device. It does not want to be a conversational memory store. Its write model is "configure collections, scan files, index content, embed chunks, cache LLM calls."

### Persistence Model

QMD uses SQLite with WAL and optional sqlite-vec. Its schema includes:

- `content`: content-addressed document bodies.
- `documents`: collection/path/title/hash/active mapping.
- `documents_fts`: FTS5 search index.
- `content_vectors` and `vectors_vec`: vector chunk metadata and sqlite-vec embeddings.
- `store_collections`: collection registry in SQLite.
- `store_config`: config and global context.
- `llm_cache`: cached query expansion/rerank responses.

Source evidence:

- `qmd/src/store.ts:821-921` initializes SQLite, WAL, content, documents, vectors, store collections, config, and FTS.
- `qmd/README.md:951-963` documents index location and table roles.

### Native Write Entrances

QMD has two configuration planes:

1. YAML or inline config:
   - `loadConfig()` reads file or inline config.
   - `saveConfig()` writes YAML or updates inline config.
   - `addCollection()`, `removeCollection()`, and `renameCollection()` mutate collection config.
   - Source: `qmd/src/collections.ts:176-222`, `qmd/src/collections.ts:308-348`.

2. SQLite store sync:
   - `upsertStoreCollection()` inserts/updates `store_collections`.
   - `syncConfigToDb()` syncs config into SQLite and deletes removed collections.
   - Context writes update `store_collections.context` or `store_config.global_context`.
   - Source: `qmd/src/store.ts:1033-1140`.

Actual document writes happen through indexing:

- `reindexCollection()` scans a filesystem collection, reads files, hashes content, identifies title, compares existing row state, inserts content, updates documents, and deactivates removed paths.
- Source: `qmd/src/store.ts:1272-1345`.

Low-level document mutation helpers:

- `insertContent()` inserts content by hash.
- `insertDocument()` upserts collection/path rows and rebuilds FTS.
- `updateDocumentTitle()` and `updateDocument()` update rows and rebuild FTS.
- `deactivateDocument()` marks missing docs inactive.
- Source: `qmd/src/store.ts:2414-2584`.

Embedding writes:

- `insertEmbedding()` writes `content_vectors` first, then deletes/inserts into `vectors_vec` because sqlite-vec does not support `OR REPLACE`.
- Source: `qmd/src/store.ts:3729-3752`.

MCP exposure is read-oriented:

- `query` is explicitly read-only and supports typed `lex`, `vec`, and `hyde` subqueries.
- `multi_get` retrieves documents.
- `status` exposes index state.
- Source: `qmd/src/mcp/server.ts:237-337`, `qmd/src/mcp/server.ts:443-540`.

### Adapter Shape

QMD adapter should be mostly `read`, `reindex`, and `embed`, not general `write`.

Supported fabric operations:

- `import_collection`: map to `collection add` or SDK `addCollection`.
- `reindex`: map to `store.update()` / `qmd update`.
- `embed`: map to `store.embed()` / `qmd embed`.
- `search`: map to MCP/SDK `query`, `searchLex`, `searchVector`, or hybrid search.
- `get`: map to `get` or `multi_get`.
- `status`: map to `status`.
- `verify`: compare MemoryCore source pointer against QMD `documents.hash`, active flag, and current filesystem hash.

Avoid:

- Direct inserts into `documents`, `content`, `documents_fts`, or `vectors_vec`.
- Treating QMD as a message append target.
- Writing raw files through QMD. QMD indexes files; it is not the source-of-truth editor.

## Lossless-Claw Write Model

### Native Role

Lossless-Claw is a conversation continuity and context-compaction device. Its write model is append-only conversation ingest, transcript reconciliation, summary DAG persistence, context item ordering, large-file sidecars, and deferred compaction telemetry.

### Persistence Model

Lossless-Claw uses SQLite for conversations, messages, message parts, summaries, summary lineage, context items, large files, bootstrap state, and maintenance telemetry.

Source evidence:

- `lossless-claw/src/store/conversation-store.ts:381-418` creates conversations.
- `lossless-claw/src/store/conversation-store.ts:626-700` writes messages and bulk messages.
- `lossless-claw/src/store/conversation-store.ts:1058-1078` writes structured message parts.
- `lossless-claw/src/store/conversation-store.ts:1235-1249` writes optional FTS rows.
- `lossless-claw/src/store/summary-store.ts:411-430` begins summary insert handling.
- `lossless-claw/src/store/summary-store.ts:566-596` links summaries to source messages or parent summaries.

### Native Write Entrances

The safe write entrance is the engine, not the store classes.

Single message ingest:

- `engine.ingest()` checks ignored/stateless sessions, ensures migrations, serializes via `withSessionQueue`, and calls `ingestSingle()`.
- Source: `lossless-claw/src/engine.ts:2660-2684`.

Batch message ingest:

- `engine.ingestBatch()` does the same with transaction handling and replay filtering.
- Source: `lossless-claw/src/engine.ts:2686-2738`.

`ingestSingle()` performs critical preprocessing before any message write:

- skips heartbeat and non-persistable roles.
- skips failed/empty assistant messages.
- blocks OpenClaw runtime context leakage.
- gets or creates the conversation.
- deduplicates transcript entry ids.
- intercepts large inline images/files/tool results/raw payloads.
- computes next sequence number.
- writes the message.
- writes message parts.
- appends a context item.
- Source: `lossless-claw/src/engine.ts:2486-2657`.

After-turn host path:

- `afterTurn` constructs a batch from new messages and optional auto-compaction summary, then calls `ingestBatch()`.
- Source: `lossless-claw/src/engine.ts:2878-2920`.

Summary writes:

- Leaf compaction summarizes raw messages, generates summary id, then `summaryStore.insertSummary()`.
- Condensed compaction summarizes summaries and writes another summary row.
- Source: `lossless-claw/src/compaction.ts:2160-2205`, `lossless-claw/src/compaction.ts:2308-2328`.

Lineage writes:

- `linkSummaryToMessages()` writes `summary_messages`.
- `linkSummaryToParents()` writes `summary_parents`.
- Source: `lossless-claw/src/store/summary-store.ts:566-596`.

### Adapter Shape

Lossless-Claw adapter should target conversation append and context read operations.

Supported fabric operations:

- `append_message`: map to `engine.ingest()`.
- `batch_append_message`: map to `engine.ingestBatch()`.
- `derive`: request/allow compaction through engine maintenance paths, not direct summary insert.
- `search`: map to LCM grep/expand/query tools or native retrieval.
- `get`: map to `lcm_describe`/summary/message expansion.
- `status`: expose conversations, summaries, context pressure, deferred compaction debt.
- `verify`: check transcript entry id, message id, summary lineage, and whether source transcript still contains the referenced entry.

Avoid:

- Direct writes to `messages`, `message_parts`, `context_items`, `summaries`, `summary_messages`, or `summary_parents`.
- Direct summary injection unless explicitly implementing an import/migration mode.
- Bypassing `withSessionQueue`, replay filtering, large-file interception, or context item append.

MemoryCore should treat Lossless-Claw as the authoritative transcript/continuity device, not as a general document store.

## Honcho Write Model

### Native Role

Honcho is a peer/session memory and reasoning device. It stores workspaces, peers, sessions, messages, embeddings, queue items, summaries, conclusions/representations, peer cards, and dream/reconciler tasks.

### Persistence Model

Honcho uses SQLAlchemy models over PostgreSQL-style storage.

Core tables:

- `workspaces`
- `peers`
- `sessions`
- `messages`
- `queue`

Source evidence:

- `honcho/src/models.py:96-120` defines workspaces.
- `honcho/src/models.py:129-160` defines peers and unique `(name, workspace_name)`.
- `honcho/src/models.py:166-199` defines sessions and unique `(name, workspace_name)`.
- `honcho/src/models.py:205-260` defines messages, public ids, sequence, token count, metadata, session and peer foreign keys.
- `honcho/src/models.py:478-530` defines queue items and dedup indexes.

### Native Write Entrances

Session creation/update:

- `POST /workspaces/{workspace_id}/sessions` gets or creates a session.
- It validates JWT/workspace/session access, calls `crud.get_or_create_session()`, and returns 201 if created.
- Source: `honcho/src/routers/sessions.py:274-321`.

Message append:

- `POST /workspaces/{workspace_id}/sessions/{session_id}/messages` calls `crud.create_messages()`.
- It emits metrics/events, creates queue payloads, enqueues derivation work in background, and optionally embeds messages immediately.
- Source: `honcho/src/routers/messages.py:85-151`.

File upload:

- `POST /upload` converts uploaded files into messages, commits file metadata, enqueues derivation, and optionally embeds.
- Source: `honcho/src/routers/messages.py:157-229`.

Message schema:

- `MessageCreate` includes `content`, `peer_id`, optional metadata/configuration, and optional `created_at`.
- `MessageBatchCreate` caps batches at 100 messages.
- Source: `honcho/src/schemas/api.py:244-300`.

Message persistence:

- `crud.create_messages()` gets or creates session and peers, acquires a per-workspace/session advisory lock, reads last `seq_in_session`, assigns ordered sequence numbers, constructs message rows, optionally creates pending embedding rows, and commits.
- Source: `honcho/src/crud/message.py:211-310`.

Queue writes:

- `enqueue()` cancels pending dreams for affected peers, resolves session behavior, creates queue records, inserts `QueueItem` rows, and commits.
- Source: `honcho/src/deriver/enqueue.py:25-75`.
- `generate_queue_records()` creates summary and representation tasks based on per-message configuration and effective observer policy.
- Source: `honcho/src/deriver/enqueue.py:293-388`.

Context read:

- Session context uses summaries plus messages.
- Summary selection uses a 40/60 budget split, choosing a fitting long or short summary before fetching messages after the summary boundary.
- Source: `honcho/src/routers/sessions.py:138-240`.

### Adapter Shape

Honcho adapter should target peer/session append plus derived-memory reads.

Supported fabric operations:

- `append_message`: map to Honcho messages API.
- `batch_append_message`: map to Honcho message batch API, max 100 messages.
- `put_document`: only indirectly via upload-as-messages, not arbitrary page writes.
- `derive`: normally implicit by enqueue/background tasks after message write; explicit dream/queue triggers may be separate advanced adapter capabilities.
- `search`: map to Honcho session/peer search APIs.
- `get`: fetch session context, summaries, peer representation, peer card, messages, or conclusions.
- `status`: expose queue status, active queue sessions, embedding/reconciler state.
- `verify`: check workspace/session/peer/message public id and sequence in DB; check whether queue items were generated/processed if derivation is required.

Avoid:

- Direct insert into `messages`, because sequence allocation and advisory locking live in `crud.create_messages()`.
- Direct insert into `queue`, because queue payloads depend on session configuration, peer observer policy, and dream cancellation.
- Treating Honcho conclusions as source evidence. They are derived memory and need source-message links when virtualized.

MemoryCore should treat Honcho as the authoritative peer/session reasoning device, not as the raw transcript source of record when Lossless-Claw is present.

## gbrain Write Model

### Native Role

gbrain is a personal knowledge brain with page-level memory, source scoping, schema packs, capture, import, chunks, embeddings, timeline entries, links, ingest logs, sync, and context engine tooling.

Its write model is closest to a knowledge base or wiki database with strong operator tooling.

### Persistence Model

gbrain supports Postgres and PGLite engines behind a `BrainEngine` interface.

Important engine write surfaces:

- `putPage(slug, page, opts)`: insert/update page.
- `upsertChunks(slug, chunks, opts)`: replace chunk set for a page.
- `addTimelineEntry(slug, entry, opts)`: append timeline entry.
- `logIngest(entry)`: record ingestion event.
- `transaction(fn)`: run writes transactionally.

Source evidence:

- `gbrain/src/core/engine.ts:646-687` defines lifecycle and `putPage`.
- `gbrain/src/core/engine.ts:942-957` defines `upsertChunks`.
- `gbrain/src/core/engine.ts:1342-1353` defines `addTimelineEntry`.
- `gbrain/src/core/engine.ts:1805-1811` defines `logIngest`.

### Native Write Entrances

Human-facing capture:

- `gbrain capture` is explicitly documented as the single human-facing entrypoint for getting content into the brain.
- Local install routes through `put_page`.
- Thin-client install routes through remote MCP `put_page`.
- It outputs slug, status, content hash, and write-through details.
- Source: `gbrain/src/commands/capture.ts:1-30`, `gbrain/src/commands/capture.ts:447-565`.

MCP/operation write:

- `put_page` is the canonical page write operation.
- It handles subagent write confinement, embedding-provider availability, source scoping, schema-pack type inference, provenance, remote trust gates, import, and write-through.
- Source: `gbrain/src/core/operations.ts:696-825`, `gbrain/src/core/operations.ts:863-880`.

Import pipeline:

- `importFromContent()` does parse, hash, embedding/chunking, and transactional writes.
- It enforces max payload size, strips gate-owned frontmatter markers from untrusted remote writes, runs guardrails, and runs content sanity before persistence.
- Source: `gbrain/src/core/import-file.ts:208-286`, `gbrain/src/core/import-file.ts:287-340`, `gbrain/src/core/import-file.ts:342-430`.

Validated writer:

- `BrainWriter` is a transaction-scoped writer with pre-commit validators.
- Strict mode can roll back on validator errors; lint mode warns.
- It delegates to engine writes inside a transaction.
- Source: `gbrain/src/core/output/writer.ts:1-18`, `gbrain/src/core/output/writer.ts:240-264`.

Manual timeline:

- `add_timeline_entry` validates date and calls `engine.addTimelineEntry()`.
- Source: `gbrain/src/core/operations.ts:2060-2097`.

Ingest log:

- `log_ingest` calls `engine.logIngest()`.
- Source: `gbrain/src/core/operations.ts:2475-2495`.

OpenClaw packaging:

- gbrain plugin exposes a local MCP server command `./bin/gbrain serve`.
- It declares skills for ingest, maintain, query, media ingest, meeting ingestion, and voice note ingest.
- Source: `gbrain/openclaw.plugin.json:24-31`, `gbrain/openclaw.plugin.json:32-69`.

### Adapter Shape

gbrain adapter should target page/capture/import operations and schema-aware writes.

Supported fabric operations:

- `put_document`: map to `put_page` or `gbrain capture`.
- `import_collection`: map to `gbrain import`.
- `append_timeline`: map to `add_timeline_entry`.
- `log_ingest`: map to `log_ingest`.
- `search`: map to gbrain search/query/context tools.
- `get`: map to `get_page`, `get_chunks`, timeline, ingest log.
- `status`: map to stats/health.
- `verify`: compare page content hash, source id, source path, write-through file state, and ingest log.

Avoid:

- Direct engine `putPage` from the fabric unless MemoryCore is running inside gbrain's trusted process boundary.
- Direct chunk writes unless implementing a migration/importer that intentionally owns chunking.
- Bypassing `put_page` provenance trust gates and write-through.
- Treating gbrain as an ordered conversation transcript store. It can store pages and timeline entries, not necessarily turn-perfect conversation continuity.

MemoryCore should treat gbrain as a knowledge-brain/page device with schema-aware write controls.

## Cross-System Write Capability Matrix

| Backend | Native write unit | Safe write entrance | Derived work trigger | Best MemoryCore role |
|---|---|---|---|---|
| QMD | Indexed file/document in a collection | collection config + update/embed | embedding, query cache | corpus retrieval/index device |
| Lossless-Claw | ordered conversation message + summary DAG | `engine.ingest()` / `engine.ingestBatch()` | compaction/maintenance | transcript continuity device |
| Honcho | session message from a peer | Honcho messages API / SDK | queue, summary, representation, embedding | peer/session reasoning device |
| gbrain | page, timeline entry, ingest log | `capture`, `put_page`, import, `BrainWriter` | chunking, embedding, schema validation, write-through | knowledge-brain/page device |

## Adaptive Abstraction Strategy

MemoryCore should not define one universal write method. It should define a router with backend capability negotiation.

### Intent: conversational append

Default route:

1. Lossless-Claw as transcript continuity device.
2. Honcho as peer/session reasoning device if peer/session identity is available.
3. gbrain only if the append is being transformed into a durable note, page, or timeline item.
4. QMD never directly; it may later index the files produced by another source.

### Intent: document/page write

Default route:

1. gbrain if the content is a structured knowledge page or capture.
2. Filesystem source plus QMD reindex if the document belongs in a corpus.
3. Honcho upload only when the document is conversational evidence inside a session.
4. Lossless-Claw only when the document is a transcript/tool artifact tied to conversation continuity.

### Intent: corpus refresh

Default route:

1. QMD collection update and embed.
2. gbrain import/sync for page-oriented brain content.
3. MemoryCore verifies source hashes and records adapter outcomes.

### Intent: derived memory

Default route:

1. Honcho for peer/session observations, summaries, representations, peer cards.
2. Lossless-Claw for conversation compaction and summary DAG.
3. gbrain for page-level synthesis, timeline, schema-bound facts/takes if appropriate.
4. MemoryCore records all derived outputs as non-source memory unless provenance links are attached.

### Intent: verification

Default route:

1. Engram verifies source artifact state.
2. QMD verifies indexed hash against filesystem source.
3. Lossless-Claw verifies message/summary lineage against transcript and DB rows.
4. Honcho verifies public ids, session sequence, queue/deriver completion.
5. gbrain verifies page hash, source id/path, ingest log, and write-through file state.

## Proposed MemoryCore Adapter Interface

```ts
type MemoryBackendCapability =
  | "append_message"
  | "batch_append_message"
  | "put_document"
  | "import_collection"
  | "reindex"
  | "embed"
  | "derive"
  | "search"
  | "get"
  | "verify"
  | "status"
  | "observe_only";

type MemoryBackendClass =
  | "corpus_index"
  | "transcript_continuity"
  | "peer_reasoning"
  | "knowledge_brain"
  | "provenance_fabric";

interface MemoryBackendAdapter {
  id: string;
  backendClass: MemoryBackendClass;
  capabilities(): Promise<MemoryBackendCapability[]>;
  status(): Promise<BackendStatus>;
  write?(op: MemoryWriteIntent): Promise<MemoryWriteResult>;
  search?(query: MemorySearchIntent): Promise<MemorySearchResult[]>;
  get?(ref: MemoryRef): Promise<MemoryRecord | null>;
  verify?(ref: MemoryRef): Promise<VerificationResult>;
}
```

The important design choice is that `write` is optional. QMD may expose no general `write`; it exposes `import_collection`, `reindex`, and `embed`. Lossless-Claw exposes append, not page writes. Honcho exposes peer/session messages, not arbitrary source documents. gbrain exposes pages/captures, not turn-perfect transcript append.

## Normalized Record Envelope

Every adapter result should return a normalized envelope with backend-native ids preserved.

```json
{
  "memorycore_id": "mc_...",
  "backend": "qmd | lossless_claw | honcho | gbrain",
  "backend_ref": {
    "type": "document | message | summary | page | timeline | queue_item | collection",
    "id": "backend-native-id",
    "uri": "optional backend URI"
  },
  "record_kind": "source | index | summary | inference | representation | page | timeline",
  "authority": "source | derived | index_only | witness",
  "content_pointer": "optional",
  "source_pointer": {
    "kind": "file | transcript | db_row | page | message | upload | external",
    "path": "optional",
    "line_range": "optional",
    "hash": "optional",
    "commit": "optional",
    "session": "optional",
    "message_id": "optional"
  },
  "derivation": {
    "derived_from": [],
    "model": "optional",
    "confidence": "optional"
  },
  "verification": {
    "status": "current | stale | unsupported | unknown",
    "checked_at": "timestamp"
  }
}
```

## Immediate Product Implications

The MVP changes from "rebuild memory" to "route memory."

The first buildable product should include:

1. Backend registry and capability probing.
2. Adapter implementations for status/search/get/verify first.
3. Write adapters only for native-safe entrances:
   - QMD: collection update/embed, not document DB mutation.
   - Lossless-Claw: `ingest`/`ingestBatch`.
   - Honcho: messages API/SDK.
   - gbrain: `capture`/`put_page`/import.
4. Normalized record envelope.
5. Provenance verification fabric.
6. Routing policy:
   - `auto`: choose backend by intent and identity.
   - `specific_backend`: user/operator chooses.
   - `fanout`: write to multiple native surfaces when safe.
   - `witness_only`: observe/index without writing.

## Recommended Next Research Tasks

1. Build a concrete adapter contract document in `docs/`, using this research as the source basis.
2. For each backend, add request/response examples for one safe write and one safe read.
3. Build a "write intent routing table" with exact policy:
   - What gets written to Lossless-Claw only.
   - What gets written to Honcho only.
   - What gets written to both.
   - What becomes a gbrain page.
   - What is indexed by QMD but sourced elsewhere.
4. Inspect live running configs to confirm which write entrances are active in Alice's Burrow environment.
5. Define the provenance verifier contract before implementation so "current vs stale" is consistent across backends.

## Bottom Line

The virtualization approach is technically better and product-wise stronger.

The systems are not redundant. They are different memory devices with different write physics:

- QMD indexes external documents.
- Lossless-Claw appends and compacts transcripts.
- Honcho appends peer/session messages and derives representations.
- gbrain writes schema-aware pages and knowledge artifacts.
- Engram can verify and connect the fabric.

MemoryCore should sit above them as a capability-aware memory fabric, not flatten them into one replacement database.
