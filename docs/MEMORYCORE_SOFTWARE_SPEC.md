# MemoryCore Software Spec

Date: 2026-06-15
Project: OpenReflect Local MemoryCore / Engram
Status: Draft v0.1
Source basis: `research/memory-stack-feature-spec-2026-06-15.md`

## Purpose

MemoryCore is a singular local-first product that performs the daily memory work currently split across QMD, Lossless-Claw, and Honcho.

The product must preserve the core strengths of each layer:

- QMD: exact and semantic local corpus recall over files, notes, docs, and research.
- Lossless-Claw: durable conversation continuity, compaction, deep recall, and context-window assembly.
- Honcho: reasoned peer/session memory, conclusions, representations, summaries, and conversational memory answers.
- Engram: provenance, versioning, branchability, and source-backed verification.

The product should not merely wrap three systems. It should expose one coherent memory substrate with one ingestion model, one provenance model, one retrieval API, one reasoning pipeline, and one operator surface.

## Product Thesis

AI memory should be searchable, reasoned, provenance-backed, and operationally inspectable.

Current memory stacks often force a tradeoff:

- Vector search finds related material but weakly proves where claims came from.
- Summaries preserve continuity but compress away source detail.
- Conversation memory gives statefulness but can drift from exact transcript evidence.
- File search finds evidence but does not reason over people, sessions, or changing context.

MemoryCore combines these into one local system:

1. Store all memory-bearing inputs as durable records.
2. Preserve exact source artifacts and version pointers.
3. Index records lexically and semantically.
4. Summarize conversations without losing raw provenance.
5. Derive reasoned observations about peers, projects, and sessions.
6. Assemble prompt-ready context from evidence, summaries, and reasoned memory.
7. Allow every claim to drill back to source.

## Target Users

Primary users:

- AI operators running persistent local agents.
- Developers building memory-aware agents.
- Researchers comparing memory substrates.
- OpenReflect/Empathos product developers needing provenance-aware recall.

Secondary users:

- Teams that need private local memory with optional cloud sync.
- Agents that need stable long-running identity and continuity.
- Audit workflows that need to distinguish source evidence, summaries, and inferred conclusions.

## Non-Goals

- Do not build a hosted-only SaaS as the default architecture.
- Do not require one model provider.
- Do not treat embeddings as the source of truth.
- Do not treat summaries or conclusions as authoritative without provenance.
- Do not hide compaction, derivation, or recall decisions from the operator.
- Do not force all deployments to ingest private raw transcripts into a public repository.

## Source Feature Mapping

This spec derives from the feature inventory in `research/memory-stack-feature-spec-2026-06-15.md`.

Core mappings:

- Local corpus search: QMD-001 through QMD-027.
- Conversation continuity and recall: LCM-001 through LCM-037.
- Reasoned peer/session memory: HON-001 through HON-037.
- Product integration rules: IMPL-001 through IMPL-010.

## Product Modules

MemoryCore should be implemented as six cooperating modules:

1. Memory Store
2. Indexing Engine
3. Transcript and Context Engine
4. Reasoning Engine
5. Provenance Engine
6. Operator and Agent Interfaces

These modules may run in one local process for MVP but must keep clear internal boundaries.

## System Architecture

```text
sources
  files, docs, notes, chats, transcripts, tool traces, imports
     |
     v
ingestion pipeline
  normalize -> identify -> version -> persist -> queue
     |
     +------------------+
     |                  |
     v                  v
memory store        provenance engine
  records              commits, diffs, source refs,
  messages             content hashes, lineage edges
  sessions
  peers
  observations
  summaries
  artifacts
     |
     +------------------+
     |                  |
     v                  v
indexing engine     reasoning engine
  FTS/BM25             explicit observations
  vectors              deductive conclusions
  hybrid rank          inductive patterns
  rerank               peer cards
  doc retrieval        session summaries
     |
     +------------------+
     |
     v
context engine
  fresh tail + summaries + retrieved evidence + representations
     |
     v
interfaces
  CLI, MCP/tools, HTTP API, SDK, operator UI
```

## Core Concepts

### Memory Record

A Memory Record is the atomic durable unit of memory.

It may represent:

- A note or markdown document.
- A chat message.
- A tool call or tool result.
- A transcript segment.
- A source file.
- A summary.
- A conclusion.
- A peer card item.
- A generated report.
- An imported external document.

Every record must have:

- Stable id.
- Record type.
- Content or content pointer.
- Source pointer.
- Created timestamp.
- Optional observed timestamp.
- Provenance metadata.
- Version metadata.
- Visibility/privacy classification.
- Indexing state.
- Derivation state.

### Source Artifact

A Source Artifact is the thing the memory record came from.

Examples:

- Filesystem path plus content hash.
- Git commit and file path.
- Transcript id and message sequence.
- Tool call id and output file id.
- External import id.
- Uploaded file id.

Source artifacts are more authoritative than derived memory.

### Provenance Pointer

A Provenance Pointer links a memory record or derived claim back to source.

It should support:

- File path.
- Line range.
- Git commit.
- Git diff.
- Transcript message id.
- Summary id.
- Parent summary ids.
- Tool call id.
- Content hash.
- Import batch id.

### Derived Observation

A Derived Observation is memory created by reasoning over records.

Types:

- Explicit observation: directly stated in source.
- Deductive observation: conclusion forced by premises.
- Inductive observation: repeated pattern.
- Abductive observation: best explanation, lower confidence.
- Preference observation.
- Trait observation.
- Project observation.
- Operational state observation.

Derived observations must carry source links and confidence.

### Summary

A Summary is compressed memory over a bounded source range.

Summaries must not replace raw records. They are prompt-assembly accelerators and navigation aids.

Required summary metadata:

- Summary id.
- Summary kind.
- Source record ids or covered range.
- Parent summary ids when condensed.
- Earliest and latest source timestamps.
- Source token count.
- Summary token count.
- Model/provider.
- Created timestamp.
- Hash of covered source set.

### Context Packet

A Context Packet is the prompt-ready output assembled for an agent turn or memory query.

It may include:

- Fresh recent messages.
- Summary DAG prefix.
- Retrieved source evidence.
- Peer representation.
- Session representation.
- Relevant derived observations.
- Active focus brief.
- Provenance links.
- Omitted-content diagnostics.

## Storage Model

MVP storage should use local SQLite with WAL enabled.

Rationale:

- Local-first.
- Easy backup.
- Good fit for FTS5.
- Sufficient for single-user and small-team memory nodes.
- Compatible with deterministic export/import.

The schema should support later migration to Postgres without changing product semantics.

### Required Tables

`memory_records`

- `id`
- `type`
- `content`
- `content_hash`
- `source_id`
- `created_at`
- `observed_at`
- `metadata_json`
- `privacy_class`
- `active`

`source_artifacts`

- `id`
- `kind`
- `uri`
- `git_commit`
- `file_path`
- `line_start`
- `line_end`
- `transcript_id`
- `message_seq`
- `tool_call_id`
- `content_hash`
- `metadata_json`

`collections`

- `id`
- `name`
- `root_uri`
- `pattern`
- `ignore_json`
- `include_by_default`
- `description`
- `last_indexed_at`

`sessions`

- `id`
- `name`
- `workspace`
- `created_at`
- `active`
- `metadata_json`

`peers`

- `id`
- `name`
- `workspace`
- `created_at`
- `metadata_json`

`session_peers`

- `session_id`
- `peer_id`
- `role`
- `joined_at`
- `left_at`

`messages`

- `id`
- `session_id`
- `peer_id`
- `seq`
- `content`
- `content_hash`
- `created_at`
- `metadata_json`
- `source_artifact_id`

`message_parts`

- `id`
- `message_id`
- `part_type`
- `content`
- `tool_name`
- `tool_call_id`
- `is_error`
- `external_artifact_id`

`summaries`

- `id`
- `conversation_id`
- `kind`
- `depth`
- `content`
- `token_count`
- `source_token_count`
- `earliest_at`
- `latest_at`
- `descendant_count`
- `model`
- `created_at`
- `source_context_hash`

`summary_edges`

- `parent_summary_id`
- `child_summary_id`
- `ordinal`

`summary_sources`

- `summary_id`
- `source_record_id`
- `source_message_id`
- `source_artifact_id`
- `ordinal`

`observations`

- `id`
- `kind`
- `subject_peer_id`
- `observer_peer_id`
- `session_id`
- `project_id`
- `content`
- `confidence`
- `created_at`
- `valid_from`
- `valid_until`
- `status`
- `metadata_json`

`observation_sources`

- `observation_id`
- `source_record_id`
- `source_message_id`
- `summary_id`
- `premise_text`

`embeddings`

- `id`
- `record_id`
- `model`
- `vector`
- `created_at`

`index_jobs`

- `id`
- `collection_id`
- `status`
- `started_at`
- `finished_at`
- `error`

`reasoning_jobs`

- `id`
- `job_type`
- `status`
- `source_scope_json`
- `model`
- `started_at`
- `finished_at`
- `error`

`context_packets`

- `id`
- `purpose`
- `request_json`
- `assembled_json`
- `token_count`
- `created_at`

## Indexing Engine

The Indexing Engine provides exact and semantic recall over local records.

### Requirements

The product must support:

- Named collections.
- Glob-based file ingestion.
- Ignore patterns.
- Markdown-aware chunking.
- Code-aware chunking.
- Content hash update detection.
- FTS/BM25 lexical search.
- Vector search.
- Hybrid reciprocal-rank fusion.
- Reranking.
- Result snippets.
- Line-numbered document retrieval.
- Stable short ids for quick retrieval.
- Index status and doctor checks.

### Search Modes

`lex`

- Exact keyword search.
- Best for names, paths, config keys, dates, ids, and phrases.

`vec`

- Semantic similarity search.
- Best for concepts and paraphrases.

`hyde`

- Hypothetical answer/document search.
- Best when query terms differ from source wording.

`hybrid`

- Combines lexical and vector result sets.
- Default for broad agent recall.

### Search Output

Each result must include:

- Record id.
- Source artifact id.
- Collection.
- Path/title.
- Score.
- Rank components when requested.
- Snippet.
- Line range when available.
- Context description.
- Provenance pointer.

## Transcript and Context Engine

The Transcript and Context Engine preserves live conversation continuity.

### Requirements

The product must support:

- Raw message persistence.
- Structured tool call/result persistence.
- Fresh tail preservation.
- Leaf summaries over raw messages.
- Condensed summaries over summaries.
- Summary DAG traversal.
- Context assembly from summaries plus live tail.
- Deep recall by grep/describe/expand equivalents.
- Deferred maintenance.
- Context threshold controls.
- Stateless session patterns.
- Ignored session patterns.
- Transcript repair for missing tool results.
- Large tool result externalization.
- Context packet diagnostics.

### Context Assembly Rules

Default assembly order:

1. System/runtime instructions from host.
2. Active focus brief when present.
3. Relevant high-level summaries.
4. Relevant lower-level summaries.
5. Retrieved source evidence.
6. Peer/session representation.
7. Fresh tail messages.
8. Current user input.

Fresh tail must be protected because recent messages are the highest-fidelity working context.

Summaries must be included only with enough provenance to drill down.

### Deep Recall Tools

The product should expose three recall layers:

`memory_grep`

- Search summary and transcript text by regex or full text.
- Returns compact snippets and source ids.

`memory_describe`

- Inspect a selected summary, record, or source artifact.
- Returns metadata and immediate content.

`memory_expand`

- Reconstruct source context from summaries and records.
- May spawn bounded background work.
- Must return citations to summary ids and source records.

## Reasoning Engine

The Reasoning Engine turns stored messages and records into usable state.

### Requirements

The product must support:

- Asynchronous reasoning jobs.
- Ordered processing per session/peer representation.
- Explicit observation extraction.
- Deductive conclusion generation.
- Inductive pattern detection.
- Abductive hypothesis generation.
- Peer cards.
- Session summaries.
- Project or topic representations.
- Staleness and contradiction tracking.
- Confidence scoring.
- Source-linked premises.

### Reasoning Cadence

Reasoning should not block writes.

Default behavior:

- Store new records immediately.
- Queue reasoning jobs.
- Batch small message bursts.
- Preserve chronological order for same session/peer.
- Mark stale derived observations when source changes.

### Observation Quality Rules

Observations must be:

- Short.
- Source-backed.
- Typed.
- Timestamped.
- Confidence-labeled.
- Separable from exact source text.
- Marked as inference when not explicit.

## Provenance Engine

The Provenance Engine is the Engram-specific layer.

### Requirements

The product must support:

- Git commit pointers for versioned files.
- Content hashes for all source artifacts.
- Diff-based staleness checks.
- Branchable reasoning experiments.
- Tags for semantic milestones.
- Blame/log inspection for source state.
- Exportable provenance bundles.
- Verification of recalled claims against source.

### Provenance Contract

Every memory answer must be able to say:

- What sources support this?
- Which parts are exact text?
- Which parts are summaries?
- Which parts are inferred observations?
- What source version produced the answer?
- Is the source still current?
- What changed since the memory was derived?

## Agent Interfaces

MemoryCore should expose four interfaces:

1. CLI
2. MCP/tools
3. HTTP API
4. SDK

### CLI Commands

Required MVP commands:

```bash
memorycore init
memorycore ingest <path-or-collection>
memorycore index
memorycore search <query>
memorycore get <record-or-source-id>
memorycore recall <query>
memorycore context <session-id>
memorycore observe <session-id>
memorycore doctor
memorycore status
memorycore verify <claim-or-observation-id>
memorycore export <scope>
```

### MCP / Tool Surface

Required tools:

- `memory_search`
- `memory_get`
- `memory_multi_get`
- `memory_status`
- `memory_grep`
- `memory_describe`
- `memory_expand`
- `memory_context`
- `memory_observe`
- `memory_verify`

### HTTP API

Core endpoints:

- `POST /records`
- `GET /records/{id}`
- `POST /collections`
- `POST /collections/{id}/index`
- `POST /search`
- `POST /sessions`
- `POST /sessions/{id}/messages`
- `GET /sessions/{id}/context`
- `POST /observations/query`
- `GET /observations/{id}`
- `POST /verify`
- `GET /status`
- `POST /doctor`

### SDK

SDK primitives:

- `MemoryCore`
- `Collection`
- `Record`
- `Session`
- `Peer`
- `Observation`
- `ContextPacket`
- `ProvenancePointer`

Example shape:

```python
core = MemoryCore(path="~/.memorycore")
session = core.session("main")
session.add_message(peer="user", content="...")
context = session.context(tokens=8000, peer_target="user")
answer = core.recall("What did we decide about memory provenance?")
```

## Operator UI

The first UI should be utilitarian, not decorative.

Required views:

- System status.
- Collections and indexing state.
- Search and retrieval.
- Session timeline.
- Summary DAG viewer.
- Observation/peer memory viewer.
- Provenance drilldown.
- Doctor and repair actions.
- Queue status.
- Model/spend status.

The UI must make memory state inspectable. It should show the distinction between source, summary, and inference.

## Privacy and Safety

MemoryCore must assume memory contents are sensitive.

Required controls:

- Local-first default.
- Explicit export.
- Privacy class per record.
- Redaction rules for tool output.
- Secret scanning before public export.
- No private path leakage in public artifacts.
- Configurable ignored sessions.
- Configurable stateless sessions.
- Audit log for external sync.

## Health and Correctness

Memory correctness includes operational health.

Doctor checks should cover:

- Database availability.
- WAL status.
- FTS availability.
- Vector index availability.
- Embedding model availability.
- Reranker availability.
- Pending index jobs.
- Pending reasoning jobs.
- Failed jobs.
- Missing source artifacts.
- Summary DAG integrity.
- Tool call/result pairing.
- Stale embeddings.
- Stale observations.
- Git provenance availability.
- Disk usage.

## MVP Scope

MVP should build the smallest coherent singular product, not a complete replacement for all three source systems.

### MVP In Scope

- SQLite store.
- File collection ingestion.
- Message/session ingestion.
- FTS lexical search.
- Optional vector search behind feature flag.
- Source artifact and provenance pointers.
- Basic summaries.
- Basic observations.
- Context packet assembly.
- CLI.
- MCP-compatible tool surface.
- Doctor/status.
- Deterministic public-safe validation.

### MVP Out of Scope

- Full Honcho-style custom reasoning model stack.
- Full Lossless-Claw subagent expansion auth.
- Multi-tenant hosted deployment.
- Complex UI.
- Automatic cloud sync.
- Large multimodal ingestion.
- Public-private fork automation beyond documented export rules.

## v0.1 Milestones

### Phase 1: Unified Store

Deliver:

- SQLite schema.
- Migration runner.
- Memory record CRUD.
- Source artifact CRUD.
- Session/message CRUD.
- CLI init/status.
- Schema validation tests.

Exit criteria:

- A message, file record, and source artifact can be stored and retrieved.
- Every record has a provenance pointer or explicit reason why not.

### Phase 2: Corpus Search

Deliver:

- Collection config.
- File ingestion.
- FTS index.
- `search` and `get`.
- Snippets and line-number retrieval.
- Doctor checks for index state.

Exit criteria:

- A markdown collection can be indexed.
- Exact local evidence can be found and cited by source pointer.

### Phase 3: Transcript Continuity

Deliver:

- Session message ingestion.
- Fresh tail assembly.
- Basic summary generation.
- Context packet generation.
- Summary source links.

Exit criteria:

- A long session can be reduced to summary plus fresh tail without losing drilldown.

### Phase 4: Reasoned Observations

Deliver:

- Async reasoning queue.
- Explicit observation extraction.
- Deductive observation extraction.
- Observation source links.
- Observation query endpoint.

Exit criteria:

- The system can derive a small set of source-linked observations from a session and inject relevant ones into context.

### Phase 5: Provenance Verification

Deliver:

- Git commit pointer capture.
- Content hash verification.
- Staleness check.
- `verify` command.
- Exportable evidence bundle.

Exit criteria:

- A recalled claim can be checked against source state and marked current, stale, or unsupported.

## Future Scope

Later phases:

- Full hybrid vector/rerank pipeline.
- Summary DAG condensation.
- Deep expansion subagents.
- Peer cards.
- Inductive and abductive observation passes.
- Project/topic representations.
- Focus briefs.
- Operator UI.
- Optional Postgres backend.
- Optional hosted sync.
- Multimodal artifacts.
- Public/private repo publishing workflow.

## Build Principles

1. Source is more authoritative than summary.
2. Summary is more authoritative than inference only for what it directly covers.
3. Inference must point back to premises.
4. Retrieval should return evidence, not just answers.
5. Context assembly should be observable.
6. Memory health is part of memory correctness.
7. Local-first should be the default deployment mode.
8. Public artifacts must not require private memory content.
9. Every feature must preserve a drilldown path.
10. The product should make memory quieter for agents, not more opaque.

## Open Design Questions

- Should the MVP embed vectors locally from day one, or ship lexical search first with vector as an optional module?
- Should summaries be model-generated immediately, or should v0.1 start with deterministic extractive summaries?
- Should observations be stored as first-class records or as a separate derived table only?
- Should git commits be created automatically on every ingestion batch, or only on operator-approved checkpoints?
- Should the MCP tool surface be built before the HTTP API, given agent usage is the primary early path?
- Should provenance bundles use a custom JSON schema or a git-native patch/report format?

## Recommended Implementation Direction

Start with a local SQLite and CLI implementation that can ingest files and sessions, preserve provenance, search exact text, assemble basic context, and verify source pointers.

Do not start with a full UI or a hosted deployment. The first proof should be behavioral:

- Ingest a small local memory corpus.
- Add a synthetic long conversation.
- Summarize it.
- Derive observations.
- Ask a recall question.
- Return a context packet with source, summary, and inference separated.
- Verify the answer against source pointers.

That path proves the singular product thesis without prematurely rebuilding the entire QMD, Lossless-Claw, and Honcho surface area.
