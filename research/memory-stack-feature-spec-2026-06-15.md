# Memory Stack Feature Spec - QMD, Lossless-Claw, Honcho

Date: 2026-06-15
Project: OpenReflect Local MemoryCore / Engram
Scope: Features, elements, and capabilities used or relevant to daily memory operation from the local source/docs corpus.

## Source Corpus

Local source roots:

- `research/source-repos/qmd` at `6366024`
- `research/source-repos/lossless-claw` at `d404eba`
- `research/source-repos/honcho` at `340175a`
- `research/source-repos/openclaw-stable` at tag `v2026.6.6`, commit `8c802aa683`

Live wiring evidence:

- OpenClaw memory backend is `qmd`: `~/.openclaw/openclaw.json:584`
- OpenClaw plugin slot `contextEngine` is `lossless-claw`: `~/.openclaw/openclaw.json:607`
- OpenClaw plugin slot `memory` is `openclaw-honcho`: `~/.openclaw/openclaw.json:607`
- `memory-core` is disabled while `openclaw-honcho` is enabled: `~/.openclaw/openclaw.json:656`, `~/.openclaw/openclaw.json:660`
- Honcho endpoint is local HTTP, workspace `openclaw`: `~/.openclaw/openclaw.json:666`
- QMD live index has three configured collections: `~/.config/qmd/index.yml:1`

Live QMD state checked from `~/.cache/qmd/index.sqlite`:

- `store_collections`: 3
- active `documents`: 1546
- `content_vectors`: 57225
- collections: `memory`, `openclaw-docs`, `workspace-research`

## Stack Role Model

The daily memory stack is not one memory system. It is three complementary layers:

1. QMD: local corpus recall over files, notes, docs, and research using lexical, vector, and reranked retrieval.
2. Lossless-Claw: live conversation continuity and context-window management using persisted transcripts plus a summary DAG.
3. Honcho: peer/session memory that reasons over messages into conclusions, representations, cards, context, and natural-language answers.

## QMD Spec

### QMD-001: Local Document Memory Engine

Feature:
QMD is an on-device search engine for markdown notes, meeting transcripts, documentation, and knowledge bases.

Daily use:
This is the file/corpus memory layer. It answers "where is this written?", "what docs mention this?", "what did we write in memory/tasks?", and "pull relevant source snippets from local project knowledge."

Source:
`qmd/README.md:3`, `qmd/README.md:5`

### QMD-002: Collection Registry

Feature:
QMD indexes named collections, each with a root path, glob pattern, ignore list, include-by-default flag, and optional update command.

Daily use:
Alice's live QMD index separates memory notes, OpenClaw docs, and workspace research into distinct searchable scopes.

Source:
`qmd/README.md:23`, `qmd/README.md:583`, `qmd/src/store.ts:894`

Live configuration:

- `memory`: `~/.openclaw/workspace/memory`, `**/*.md`, excluding session-ingest/live/full JSONL-derived material
- `openclaw-docs`: `~/.openclaw/workspace/openclaw-docs`, `**/*.md`
- `workspace-research`: `~/.openclaw/workspace/{analysis,reports,notes,references}/**/*.md`

### QMD-003: Path and Collection Context

Feature:
QMD stores context descriptions for collections, paths, and global index scope. The docs call this a key feature because context is returned with matching subdocuments and helps LLMs choose results.

Daily use:
Context lets retrieval distinguish memory, docs, and research without relying only on filenames or text matches.

Source:
`qmd/README.md:28`, `qmd/README.md:312`, `qmd/README.md:628`

### QMD-004: Content-Addressed Document Store

Feature:
QMD stores document content by hash, maps documents to collection/path/title/hash, marks active documents, and keeps indexed content in SQLite.

Daily use:
This supports stable doc identity, update detection, deletion/inactivation, and safe local operation without remote service dependency.

Source:
`qmd/src/store.ts:840`, `qmd/src/store.ts:849`, `qmd/src/store.ts:866`

### QMD-005: SQLite, WAL, FTS5, and sqlite-vec

Feature:
QMD uses SQLite with WAL, FTS5 for lexical search, and sqlite-vec for vector search when available. If sqlite-vec is unavailable, vector search fails while FTS remains usable.

Daily use:
Lexical memory search should remain available even if GPU/vector dependencies degrade.

Source:
`qmd/src/store.ts:821`, `qmd/src/store.ts:833`, `qmd/src/store.ts:915`

### QMD-006: BM25 Lexical Search

Feature:
`qmd search` performs fast BM25/FTS keyword search.

Daily use:
Use this for exact terms, filenames, config keys, commit hashes, names, dates, and distinctive phrases.

Source:
`qmd/README.md:37`, `qmd/README.md:254`, `qmd/README.md:657`

### QMD-007: Vector Semantic Search

Feature:
`qmd vsearch` performs semantic vector search over embedded chunks.

Daily use:
Use this when a concept is likely present under different words than the query.

Source:
`qmd/README.md:38`, `qmd/README.md:257`, `qmd/README.md:658`

### QMD-008: Hybrid Query Pipeline

Feature:
`qmd query` combines query expansion, parallel FTS and vector retrieval, reciprocal rank fusion, top-rank bonus, candidate selection, LLM reranking, and position-aware score blending.

Daily use:
This is the high-quality recall mode for ambiguous or conceptual memory lookup.

Source:
`qmd/README.md:39`, `qmd/README.md:473`, `qmd/README.md:1049`

### QMD-009: Typed Query Documents

Feature:
QMD query supports typed subqueries:

- `lex`: keyword/BM25 route
- `vec`: semantic/vector route
- `hyde`: hypothetical answer/document route

Daily use:
This lets an operator combine exact anchors with semantic recall instead of trusting automatic expansion.

Source:
`qmd/README.md:77`, `qmd/README.md:142`, `qmd/src/store.ts:335`, `qmd/src/mcp/server.ts:226`

### QMD-010: Intent Disambiguation

Feature:
The MCP/query API accepts `intent` as disambiguation context. It does not search by itself.

Daily use:
Use intent when a query term is overloaded, for example "memory" as OpenClaw memory architecture rather than human recollection.

Source:
`qmd/README.md:144`, `qmd/src/mcp/server.ts:311`

### QMD-011: Reranking Control

Feature:
QMD supports candidate limits and `--no-rerank` / `rerank=false` to trade quality for latency.

Daily use:
Use reranking for high-value synthesis; skip it for quick exact checks or constrained CPU/GPU situations.

Source:
`qmd/README.md:147`, `qmd/README.md:247`, `qmd/README.md:690`

### QMD-012: Explainable Retrieval Scores

Feature:
`--explain` exposes retrieval score traces for hybrid query output.

Daily use:
Use this when judging whether QMD's answer is a strong match or a reranker hallucination/overreach.

Source:
`qmd/README.md:687`, `qmd/README.md:798`

### QMD-013: Agent-Oriented Output Formats

Feature:
QMD supports `--json`, `--files`, markdown/full output, line numbers, and full-document retrieval.

Daily use:
This is why QMD works well in agent loops: an agent can search, inspect result metadata, then retrieve precise files or line ranges.

Source:
`qmd/README.md:53`, `qmd/README.md:57`, `qmd/README.md:792`

### QMD-014: Document Retrieval by Path or DocID

Feature:
QMD can retrieve documents by path, virtual `qmd://` path, short docid, glob, comma-separated list, and line range suffix.

Daily use:
After search, use `get` or `multi_get` to pull source snippets into the working context.

Source:
`qmd/README.md:41`, `qmd/README.md:265`, `qmd/src/mcp/server.ts:368`, `qmd/src/mcp/server.ts:443`

### QMD-015: Virtual Path Namespace

Feature:
QMD uses `qmd://collection/path` URIs and can parse/resolve virtual paths to filesystem paths.

Daily use:
This gives memory hits a stable collection-aware identifier even when absolute paths are noisy.

Source:
`qmd/README.md:159`, `qmd/src/store.ts:580`, `qmd/src/store.ts:623`

### QMD-016: MCP Server

Feature:
QMD exposes MCP tools: `query`, `get`, `multi_get`, and `status`; it supports stdio and localhost HTTP transports.

Daily use:
This is the direct agent integration surface for search and retrieval.

Source:
`qmd/README.md:72`, `qmd/README.md:121`, `qmd/src/mcp/server.ts:1`, `qmd/src/mcp/server.ts:168`

### QMD-017: MCP Dynamic Instructions

Feature:
The MCP server injects current index state, collection names, vector-health notes, and search guidance into server instructions.

Daily use:
Agents can learn what collections exist and whether embeddings are stale before calling tools.

Source:
`qmd/src/mcp/server.ts:103`, `qmd/src/mcp/server.ts:108`, `qmd/src/mcp/server.ts:127`

### QMD-018: MCP Resource Access

Feature:
QMD exposes documents as read-only MCP resources under `qmd://{path}`.

Daily use:
This lets clients fetch markdown documents through MCP once discovered by search.

Source:
`qmd/src/mcp/server.ts:180`

### QMD-019: SDK / Embedded Library

Feature:
QMD can be used as a Node/Bun library via `createStore`, with explicit database path, collections config, `search`, `searchLex`, `searchVector`, `expandQuery`, `update`, and `embed`.

Daily use:
This is relevant for integrating QMD into OpenReflect/Engram services rather than shelling out.

Source:
`qmd/README.md:162`, `qmd/README.md:174`, `qmd/README.md:220`, `qmd/README.md:330`

### QMD-020: Embedding Generation

Feature:
`qmd embed` generates chunk embeddings; `-f` forces re-embedding; batch caps control memory; embeddings are model/fingerprint sensitive.

Daily use:
Run after indexed content changes or after model/prompt/fingerprint changes.

Source:
`qmd/README.md:33`, `qmd/README.md:342`, `qmd/README.md:595`, `qmd/src/store.ts:68`

### QMD-021: Smart Markdown Chunking

Feature:
Documents are chunked around 900 tokens with 15 percent overlap, preserving natural markdown breakpoints and avoiding splits inside code fences.

Daily use:
This makes memory recall more semantically coherent than blind fixed-window chunks.

Source:
`qmd/README.md:993`, `qmd/README.md:1005`, `qmd/src/store.ts:57`, `qmd/src/store.ts:115`

### QMD-022: AST-Aware Code Chunking

Feature:
Optional `--chunk-strategy auto` uses tree-sitter breakpoints for TypeScript, JavaScript, Python, Go, and Rust code.

Daily use:
Use when indexing source trees so functions/classes/imports remain coherent retrieval units.

Source:
`qmd/README.md:604`, `qmd/README.md:615`, `qmd/README.md:1036`

### QMD-023: Local GGUF Model Roles

Feature:
Default model roles:

- Embeddings: `embeddinggemma-300M-Q8_0`
- Reranking: `qwen3-reranker-0.6b-q8_0`
- Query expansion: `qmd-query-expansion-1.7B-q4_k_m`

Daily use:
These are the local recall pipeline actors. Changing embedding model requires re-embedding.

Source:
`qmd/README.md:514`, `qmd/README.md:522`, `qmd/README.md:1087`

### QMD-024: LLM Cache

Feature:
QMD stores cached LLM outputs for query expansion and rerank scores in `llm_cache`.

Daily use:
Reduces repeated local model work for recurring queries.

Source:
`qmd/README.md:962`, `qmd/src/store.ts:870`

### QMD-025: Named Indexes

Feature:
QMD supports named indexes via `--index` and explicit DB paths.

Daily use:
Allows separate corpora such as normal memory, forensic sessions, or experimental indexes.

Source:
`qmd/README.md:688`, `qmd/README.md:801`, `qmd/src/store.ts:548`

### QMD-026: CJK Lexical Normalization

Feature:
QMD normalizes CJK text for FTS5 exact search and supports alternate multilingual embedding models.

Daily use:
Relevant for multilingual notes and mixed English/German/CJK corpora.

Source:
`qmd/src/store.ts:754`, `qmd/src/store.ts:758`, `qmd/README.md:520`

### QMD-027: Index Status and Doctor Checks

Feature:
QMD reports total docs, embedding freshness, vector index availability, collections, model cache, sqlite-vec status, embedding fingerprints, and vector sample reproducibility.

Daily use:
This is the health gate for avoiding stale-embedding confidence failures.

Source:
`qmd/README.md:835`, `qmd/src/mcp/server.ts:516`, `qmd/src/cli/qmd.ts:3629`, `qmd/src/cli/qmd.ts:3980`

## Lossless-Claw Spec

### LCM-001: OpenClaw Context Engine

Feature:
Lossless-Claw is an OpenClaw context engine that replaces sliding-window truncation with persisted messages plus DAG summaries.

Daily use:
This is the continuity layer for active conversations, Telegram/Discord sessions, Codex sessions, cron sessions when not ignored, and long-running context.

Source:
`lossless-claw/README.md:3`, `lossless-claw/README.md:20`

### LCM-002: Lossless Raw Message Persistence

Feature:
LCM persists every message in SQLite, organized by conversation, while keeping summaries linked back to source messages.

Daily use:
This is what allows exact recall after compaction instead of trusting summary text alone.

Source:
`lossless-claw/README.md:22`, `lossless-claw/README.md:28`, `lossless-claw/docs/architecture.md:7`

### LCM-003: Structured Message Parts

Feature:
LCM stores `message_parts` for structured content blocks: text, reasoning, tool calls/results, files, patches, subtasks, compaction events, snapshots, agents, retries, and metadata.

Daily use:
Preserves the original shape of turns and tool events for later reconstruction and transcript repair.

Source:
`lossless-claw/docs/architecture.md:18`, `lossless-claw/src/db/migration.ts:255`

### LCM-004: Conversation and Context Item Model

Feature:
Each OpenClaw session maps to a conversation. `context_items` is the ordered list of messages and summaries the model sees.

Daily use:
This is the durable model-context ledger that lets LCM replace old raw messages with compact summaries without losing order.

Source:
`lossless-claw/docs/architecture.md:9`, `lossless-claw/docs/architecture.md:45`, `lossless-claw/src/store/summary-store.ts:63`

### LCM-005: Summary DAG

Feature:
LCM creates leaf summaries from raw messages and condensed summaries from lower-depth summaries, linking nodes through `summary_messages` and `summary_parents`.

Daily use:
This is the core compaction structure. It lets the model carry compact memory while agents can drill back down.

Source:
`lossless-claw/docs/architecture.md:20`, `lossless-claw/docs/architecture.md:24`, `lossless-claw/docs/architecture.md:30`, `lossless-claw/src/store/summary-store.ts:566`

### LCM-006: Summary Metadata

Feature:
Summaries carry id, conversation id, kind, depth, time range, descendant count, file ids, token count, source token count, model, and created timestamp.

Daily use:
This metadata lets prompts reason about summary age, scope, abstraction level, and expansion options.

Source:
`lossless-claw/docs/architecture.md:36`, `lossless-claw/src/store/summary-store.ts:12`, `lossless-claw/src/store/summary-store.ts:28`

### LCM-007: Bootstrap Reconciliation

Feature:
On session start, LCM reconciles OpenClaw JSONL transcript files against the LCM database and imports missing tail messages after the last anchor.

Daily use:
Crash recovery and session replay integrity depend on this.

Source:
`lossless-claw/docs/architecture.md:53`, `lossless-claw/docs/architecture.md:202`, `lossless-claw/src/store/summary-store.ts:114`

### LCM-008: Transcript Entry ID Reconciliation

Feature:
LCM tracks transcript envelope ids to make transcript imports idempotent and resume from exact anchors.

Daily use:
Prevents duplicated memory rows after replay, transcript repair, or session rotation.

Source:
`lossless-claw/src/db/migration.ts:354`

### LCM-009: Lifecycle Hooks

Feature:
LCM implements OpenClaw lifecycle hooks: bootstrap, ingest/ingestBatch, assemble-before-prompt, after-turn, maintain, compact, and runtime-LLM-complete.

Daily use:
This is how LCM participates in normal turns without requiring manual user action.

Source:
`lossless-claw/docs/architecture.md:55`, `lossless-claw/src/engine.ts:78`, `lossless-claw/src/engine.ts:332`

### LCM-010: Fresh Tail Protection

Feature:
LCM protects recent raw messages from compaction via `freshTailCount`.

Daily use:
The live Alice config sets `LCM_FRESH_TAIL_COUNT=32`, meaning recent conversational texture stays raw while older content becomes summarized.

Source:
`lossless-claw/README.md:191`, `lossless-claw/README.md:296`, `~/.openclaw/openclaw.json:14`

### LCM-011: Leaf Compaction

Feature:
Leaf compaction summarizes oldest eligible raw messages outside the fresh tail, capped by `leafChunkTokens`, with prior summary continuity context.

Daily use:
This is the first compression layer for long sessions.

Source:
`lossless-claw/docs/architecture.md:61`

### LCM-012: Condensed Compaction

Feature:
Condensation merges same-depth summaries into higher-depth summaries with progressively more abstract prompts.

Daily use:
This keeps very long conversations usable after many leaf summaries accumulate.

Source:
`lossless-claw/docs/architecture.md:75`

### LCM-013: Threshold Compaction

Feature:
LCM checks context usage against a threshold and compacts when needed. Thresholds can vary by model, context window, or session pattern.

Daily use:
The live Alice config sets `LCM_CONTEXT_THRESHOLD=0.78`.

Source:
`lossless-claw/README.md:190`, `lossless-claw/README.md:299`, `lossless-claw/docs/architecture.md:85`, `~/.openclaw/openclaw.json:15`

### LCM-014: Deferred Maintenance Mode

Feature:
LCM advertises `turnMaintenanceMode: "background"` and can defer proactive threshold compaction debt to maintenance/pre-assembly.

Daily use:
Keeps prompt-mutating compaction out of the immediate turn when possible and explains background "Context engine turn maintenance" updates.

Source:
`lossless-claw/README.md:216`, `lossless-claw/README.md:220`, `lossless-claw/src/engine.ts:337`

### LCM-015: Runtime LLM Boundary

Feature:
LCM sends summarization to OpenClaw's host-owned `runtime.llm.complete`; it does not own provider credentials, base URLs, OAuth refresh, or dispatch.

Daily use:
Keeps compaction model routing inside OpenClaw policy and avoids leaking auth into the plugin.

Source:
`lossless-claw/README.md:274`, `lossless-claw/docs/architecture.md:230`

### LCM-016: Summary Model Routing and Spend Guards

Feature:
LCM supports summary provider/model overrides, timeout, call-window limits, max calls per window, and spend backoff.

Daily use:
The live config routes summary, large-file summary, and expansion to `openai-codex/gpt-5.4-mini`.

Source:
`lossless-claw/README.md:179`, `lossless-claw/README.md:204`, `lossless-claw/README.md:210`, `~/.openclaw/openclaw.json:18`

### LCM-017: Three-Level Summarization Escalation

Feature:
Summarization escalates from normal prompt to aggressive prompt to deterministic truncation fallback.

Daily use:
Compaction should always make progress even if the summarizer returns unusable output.

Source:
`lossless-claw/docs/architecture.md:104`

### LCM-018: Context Assembly

Feature:
Before each model turn, LCM assembles summaries plus recent raw messages, budget-constrains older context, reconstructs messages from parts, and sanitizes tool-use/tool-result pairing.

Daily use:
This is the live prompt construction layer.

Source:
`lossless-claw/docs/architecture.md:114`

### LCM-019: XML Summary Prompt Format

Feature:
Summaries are injected into context as XML-wrapped user messages with id, kind, depth, descendant count, time range, content, and optional parents.

Daily use:
The "Expand for details about" footer tells Alice when to use recall expansion.

Source:
`lossless-claw/docs/architecture.md:133`

### LCM-020: Prompt-Relevance Eviction

Feature:
When prompt-aware eviction is enabled and a searchable prompt exists, LCM ranks evictable prefix items by prompt relevance before restoring chronological order.

Daily use:
Helps choose which summaries survive tight context budgets.

Source:
`lossless-claw/docs/architecture.md:129`

### LCM-021: Recall Tool Escalation

Feature:
LCM provides an escalation flow:

1. `lcm_grep`
2. `lcm_describe`
3. `lcm_expand_query`

Daily use:
This is the exact recall protocol after compaction or summary-only context.

Source:
`lossless-claw/docs/agent-tools.md:7`

### LCM-022: lcm_grep

Feature:
Searches messages and/or summaries by regex or FTS full-text, with scope, time, conversation, all-conversation, limit, and sort controls.

Daily use:
First-line transcript recall.

Source:
`lossless-claw/docs/agent-tools.md:31`

### LCM-023: lcm_describe

Feature:
Retrieves full summary or stored-file content plus metadata, links, source message ids, parent/child summary ids, and file ids.

Daily use:
Cheap drilldown when a summary id or file id is already known.

Source:
`lossless-claw/docs/agent-tools.md:75`

### LCM-024: lcm_expand_query

Feature:
Spawns a bounded sub-agent to expand summaries through the DAG and answer a focused question with cited ids.

Daily use:
Use when exact commands, file paths, rationale, tool outputs, or verbatim facts were compressed away.

Source:
`lossless-claw/docs/agent-tools.md:113`, `lossless-claw/docs/architecture.md:162`

### LCM-025: Delegated Expansion Grants

Feature:
Expansion creates scoped grants with conversation ids, token caps, TTL, revocation, and cleanup. Sub-agents get low-level `lcm_expand`, not recursive `lcm_expand_query`.

Daily use:
Bounds deep recall and prevents recursive expansion loops.

Source:
`lossless-claw/docs/architecture.md:176`

### LCM-026: Conversation Scoping

Feature:
LCM tools default to current session family, with optional `allConversations` or exact `conversationId`.

Daily use:
Prevents unrelated session contamination while still supporting global discovery when requested.

Source:
`lossless-claw/docs/agent-tools.md:192`

### LCM-027: Session Reset Semantics

Feature:
LCM distinguishes `/new`, `/reset`, and `/lcm rotate`.

Daily use:
`/new` prunes context within the same active LCM conversation; `/reset` archives and creates a new active row; `/lcm rotate` trims transcript backing while preserving LCM conversation identity.

Source:
`lossless-claw/README.md:304`, `lossless-claw/README.md:316`

### LCM-028: Session Pattern Controls

Feature:
LCM supports ignored sessions and stateless sessions. Ignored sessions do not create/write/compact. Stateless sessions can read but skip writes and grants.

Daily use:
Live config ignores `cron:*` and treats `subagent:*` as stateless.

Source:
`lossless-claw/README.md:328`, `lossless-claw/README.md:369`, `~/.openclaw/openclaw.json:25`

### LCM-029: Cron Runtime Isolation

Feature:
LCM can archive prior active cron runs and create a fresh LCM conversation when OpenClaw reuses session keys for new runtime session ids.

Daily use:
Relevant to heartbeat/cron pressure and avoiding long-running cron conversations contaminating each other.

Source:
`lossless-claw/README.md:330`

### LCM-030: Large File Externalization

Feature:
Large file/tool-output blocks above threshold are stored externally under `largeFilesDir`, summarized, replaced with compact references, and retrievable by `lcm_describe`.

Daily use:
Prevents huge tool outputs or pasted files from consuming active context while preserving access.

Source:
`lossless-claw/README.md:201`, `lossless-claw/docs/architecture.md:187`, `lossless-claw/src/store/summary-store.ts:93`

### LCM-031: Tool Payload Stub Tier

Feature:
LCM can mark messages with externalized `large_content` sidecars, leaving `messages.content` lossless while allowing assembler stubs outside fresh tail.

Daily use:
Controls context bloat from large tool results without amputating the raw stored transcript.

Source:
`lossless-claw/src/db/migration.ts:330`

### LCM-032: Transcript Repair / Tool Pairing

Feature:
LCM sanitizes tool-use/result pairing and has transcript repair utilities for malformed tool-result histories.

Daily use:
This explains synthetic missing tool-result repair warnings and prevents malformed histories from breaking model prompts.

Source:
`lossless-claw/README.md:490`, `lossless-claw/docs/architecture.md:131`

### LCM-033: Operation Serialization

Feature:
Mutating operations are serialized per stable session identity using a promise queue.

Daily use:
Prevents concurrent ingest/compaction races during overlapping turn maintenance or runtime activity.

Source:
`lossless-claw/docs/architecture.md:226`, `lossless-claw/src/engine.ts:558`

### LCM-034: FTS5 Summary Search With Fallback

Feature:
Summaries are indexed into FTS5 and CJK FTS when available; if unavailable, LCM falls back to LIKE search.

Daily use:
`lcm_grep` remains usable even if Node SQLite lacks FTS5, though slower/weaker.

Source:
`lossless-claw/src/store/summary-store.ts:484`, `lossless-claw/src/engine.ts:387`

### LCM-035: Doctor, Backup, Rotation, and Status Commands

Feature:
LCM provides `/lcm`, `/lcm backup`, `/lcm rotate`, `/lcm doctor`, `/lcm doctor clean`, `/lcm status`, and `/lossless` alias.

Daily use:
These are the operator-facing health and maintenance controls.

Source:
`lossless-claw/README.md:36`

### LCM-036: Focus Briefs

Feature:
LCM persists focus briefs, focus sources, active/draft/superseded states, generator session info, source context hashes, and delta refresh operations.

Daily use:
Useful for active-work summarization and keeping long tasks oriented around selected summary context.

Source:
`lossless-claw/src/db/migration.ts:216`, `lossless-claw/src/plugin/lcm-command.ts:1619`

### LCM-037: Context Engine Projection Epoch

Feature:
LCM computes a projection epoch hash from summary-prefix state and active focus brief to support thread bootstrap projection for forked children.

Daily use:
Important for Codex/subagent thread reuse and avoiding raw transcript replay.

Source:
`lossless-claw/src/engine.ts:126`, `lossless-claw/src/engine.ts:136`

## Honcho Spec

### HON-001: Peer-Centric Stateful Memory

Feature:
Honcho is memory infrastructure for stateful agents that understand changing people, agents, groups, projects, and ideas over time.

Daily use:
This is the person/agent/project modeling layer, distinct from local file recall and transcript compaction.

Source:
`honcho/README.md:16`, `honcho/README.md:18`

### HON-002: Store, Reason, Query, Inject Loop

Feature:
Honcho's basic loop is to store messages/events/documents/tool traces, reason in the background, query context/search/representations/answers, and inject results into LLM calls.

Daily use:
This is the daily memory cycle for durable user and agent state.

Source:
`honcho/README.md:62`

### HON-003: Workspaces

Feature:
Workspaces isolate memory between applications/use cases.

Daily use:
Live OpenClaw is configured to use Honcho workspace `openclaw`.

Source:
`honcho/README.md:246`, `honcho/README.md:577`, `~/.openclaw/openclaw.json:667`

### HON-004: Peers

Feature:
Peers are first-class entities for humans, agents, groups, projects, and ideas.

Daily use:
This lets Honcho model Mitchell, Alice, assistant lanes, channels, and agents as durable entities.

Source:
`honcho/README.md:237`, `honcho/README.md:247`, `honcho/README.md:583`

### HON-005: Sessions

Feature:
Sessions are conversation contexts with many-to-many peer participation.

Daily use:
Use sessions for Telegram groups, Discord/Slack channels, coding-project contexts, task runs, and imports.

Source:
`honcho/README.md:248`, `honcho/README.md:589`, `honcho/src/models.py:166`

### HON-006: Messages

Feature:
Messages are atomic session-level data units labeled by source peer, content, metadata, token count, sequence number, and timestamps.

Daily use:
Every stored conversation turn or ingested artifact becomes source material for reasoning and retrieval.

Source:
`honcho/README.md:249`, `honcho/README.md:595`, `honcho/src/models.py:205`

### HON-007: Many-to-Many Session Peer Membership

Feature:
Honcho uses `session_peers` with peer/session/workspace keys and per-session peer configuration.

Daily use:
Supports group chats and multi-agent sessions where multiple humans and agents share a single memory surface.

Source:
`honcho/src/models.py:40`, `honcho/src/routers/sessions.py:427`

### HON-008: Peer/Session Configuration

Feature:
Peers and session-peer memberships carry configuration, including observation settings.

Daily use:
Lets deterministic agents or import jobs be included for context while disabling expensive self-modeling when appropriate.

Source:
`honcho/README.md:239`, `honcho/docs/v3/guides/recipes/unified-memory-setup.mdx:148`, `honcho/src/routers/sessions.py:536`

### HON-009: Message Ingestion Triggers Reasoning

Feature:
Saving messages kicks off background reasoning tasks by default.

Daily use:
Daily chats and imports can update memory without blocking the write path.

Source:
`honcho/docs/v3/documentation/features/storing-data.mdx:41`, `honcho/docs/v3/documentation/core-concepts/reasoning.mdx:57`

### HON-010: Asynchronous Deriver Worker

Feature:
Honcho separates synchronous storage from asynchronous insights via a background deriver worker.

Daily use:
The API can accept writes quickly, while representations/summaries/cards update later.

Source:
`honcho/README.md:442`, `honcho/README.md:533`, `honcho/README.md:617`

### HON-011: Formal Reasoning Outputs

Feature:
Honcho extracts explicit facts, deductive conclusions, inductive/abductive patterns, peer cards, consolidation, and summaries.

Daily use:
This is why Honcho is not only vector RAG. It creates derived memory claims about people and agents.

Source:
`honcho/docs/v3/documentation/core-concepts/reasoning.mdx:13`, `honcho/docs/v3/documentation/core-concepts/reasoning.mdx:20`, `honcho/docs/v3/documentation/core-concepts/reasoning.mdx:53`

### HON-012: Token-Batched Representation Reasoning

Feature:
Representation tasks batch pending messages until roughly 1000 tokens per peer representation.

Daily use:
Low-volume imports may wait before reasoning runs; ongoing per-source sessions avoid never reaching the threshold.

Source:
`honcho/docs/v3/documentation/core-concepts/reasoning.mdx:67`, `honcho/docs/v3/guides/recipes/unified-memory-setup.mdx:134`

### HON-013: Conclusions

Feature:
Honcho exposes extracted observations/conclusions about peers through public APIs while storing them internally as vector-embedded documents.

Daily use:
This is the durable fact/pattern layer used by representations and chat answers.

Source:
`honcho/README.md:251`, `honcho/README.md:262`, `honcho/src/models.py:334`

### HON-014: Observer/Observed Collections

Feature:
Internal collections are keyed by `(observer, observed, workspace)`, supporting self-representation and cross-peer modeling.

Daily use:
Supports "what Alice knows about Mitchell," "what Mitchell knows about Alice," and self-modeling variants.

Source:
`honcho/README.md:262`, `honcho/README.md:572`, `honcho/src/models.py:334`

### HON-015: Vector-Embedded Documents

Feature:
Conclusions/documents and message embeddings use pgvector with HNSW indexes.

Daily use:
Supports semantic retrieval over both raw messages and derived conclusions.

Source:
`honcho/src/models.py:276`, `honcho/src/models.py:378`

### HON-016: Session Context Endpoint

Feature:
`session.context()` returns a blend of summaries and messages under a token limit, defaulting to summary plus recent messages.

Daily use:
Use this to hydrate an LLM with conversation context for long-running sessions.

Source:
`honcho/README.md:105`, `honcho/docs/v3/documentation/features/get-context.mdx:7`, `honcho/src/routers/sessions.py:615`

### HON-017: Context Budgeting

Feature:
Honcho allocates roughly 40 percent of context budget to summary and 60 percent to recent messages when summaries are enabled.

Daily use:
This is Honcho's session-context equivalent of compacted history plus tail.

Source:
`honcho/src/routers/sessions.py:201`, `honcho/src/routers/sessions.py:676`

### HON-018: Peer Representation in Context

Feature:
Session context can include a peer representation and peer card via `peer_target` and optional `peer_perspective`.

Daily use:
This is how LLM prompts get durable "what we know about the user/agent" material alongside local conversation context.

Source:
`honcho/docs/v3/documentation/features/get-context.mdx:100`, `honcho/src/routers/sessions.py:641`

### HON-019: Semantic Conclusion Search in Context

Feature:
Session context can include semantically relevant conclusions via `search_query`, `search_top_k`, `search_max_distance`, `include_most_frequent`, and `max_conclusions`.

Daily use:
Use for targeted memory hydration, such as "coding preferences" or "current work priorities."

Source:
`honcho/docs/v3/documentation/features/get-context.mdx:146`, `honcho/src/routers/sessions.py:632`

### HON-020: Session-Scoped Representations

Feature:
Representations can be limited to conclusions from the current session.

Daily use:
Useful when global memory would contaminate a local project/task context.

Source:
`honcho/docs/v3/documentation/features/get-context.mdx:180`, `honcho/src/routers/sessions.py:649`

### HON-021: LLM Format Adapters

Feature:
Session context can be converted to OpenAI/Anthropic-compatible message formats.

Daily use:
Makes Honcho context directly injectable into agent prompts.

Source:
`honcho/README.md:109`, `honcho/README.md:162`, `honcho/docs/v3/documentation/features/get-context.mdx:221`

### HON-022: Chat Endpoint

Feature:
`peer.chat()` is a natural-language interface that searches peer representation/conclusions and synthesizes an answer.

Daily use:
Use for questions like "what does this user care about?", "what tone do they prefer?", or "what should the agent remember about this situation?"

Source:
`honcho/README.md:106`, `honcho/docs/v3/documentation/features/chat.mdx:8`, `honcho/src/routers/peers.py:158`

### HON-023: Chat Reasoning Levels

Feature:
Chat accepts `reasoning_level` values `minimal`, `low`, `medium`, `high`, and `max` to trade speed/cost against depth.

Daily use:
Use low/minimal for routine checks and high/max for complex synthesis.

Source:
`honcho/docs/v3/documentation/features/chat.mdx:46`

### HON-024: Streaming Chat

Feature:
Chat supports streaming responses over server-sent events.

Daily use:
Useful for long memory answers or UI integration.

Source:
`honcho/docs/v3/documentation/features/chat.mdx:72`, `honcho/src/routers/peers.py:193`

### HON-025: Chat Answer Construction

Feature:
Chat searches peer card and representation, retrieves semantically relevant conclusions, may combine source message segments, and synthesizes a response.

Daily use:
This is the most operator-friendly Honcho recall path.

Source:
`honcho/docs/v3/documentation/features/chat.mdx:192`

### HON-026: Peer Representation Endpoint

Feature:
`/peers/{peer_id}/representation` returns a curated markdown subset of a peer's representation, optionally session-scoped, target-scoped, semantically queried, and constrained by conclusion limits.

Daily use:
Use when low-latency static memory is enough and a synthesized chat answer is too expensive or too slow.

Source:
`honcho/README.md:154`, `honcho/README.md:164`, `honcho/src/routers/peers.py:246`

### HON-027: Peer Cards

Feature:
Honcho provides peer cards as compact identity summaries, including observer/target variants.

Daily use:
Useful as short identity/context priors in prompts.

Source:
`honcho/README.md:255`, `honcho/src/routers/peers.py:307`, `honcho/README.md:450`

### HON-028: Session Summaries

Feature:
Honcho creates session summaries and exposes short/long summaries through `/sessions/{session_id}/summaries`.

Daily use:
Session summaries support long-running sessions without replaying every message.

Source:
`honcho/README.md:256`, `honcho/README.md:620`, `honcho/src/routers/sessions.py:807`

### HON-029: Hybrid Search

Feature:
Honcho has search endpoints at workspace, session, and peer level using hybrid search, with filters.

Daily use:
Use for direct message/document retrieval when a reasoned answer is not required.

Source:
`honcho/README.md:163`, `honcho/README.md:643`, `honcho/src/routers/sessions.py:848`

### HON-030: File Uploads as Messages

Feature:
Honcho can upload files into sessions, creating message chunks from document content.

Daily use:
Relevant for importing reports, PDFs, transcripts, and research docs into peer/session memory.

Source:
`honcho/README.md:165`, `honcho/docs/v3/documentation/features/advanced/file-uploads.mdx:46`

### HON-031: Unified Memory Setup Across Surfaces

Feature:
Honcho supports one shared workspace and one shared user peer across chat companion, coding agent, autonomous agent, and scheduled ingestion job.

Daily use:
This is the model for making Alice's Telegram/Discord/coding/import memory converge into one durable user representation.

Source:
`honcho/docs/v3/guides/recipes/unified-memory-setup.mdx:12`, `honcho/docs/v3/guides/recipes/unified-memory-setup.mdx:160`

### HON-032: Stable Peer and Session IDs

Feature:
Guides recommend deriving peer ids from immutable platform ids and scoping sessions by surface/project/import.

Daily use:
Prevents memory fragmentation when display names change or multiple hosts interact with the same person.

Source:
`honcho/docs/v3/guides/recipes/unified-memory-setup.mdx:22`, `honcho/docs/v3/guides/recipes/unified-memory-setup.mdx:29`, `honcho/docs/v3/guides/recipes/unified-memory-setup.mdx:47`

### HON-033: Agent Tool Integrations

Feature:
Honcho integrates with MCP, Claude Code, OpenCode, OpenClaw, Hermes, Cursor-compatible clients, SDKs, and raw HTTP.

Daily use:
OpenClaw currently reaches Honcho through `openclaw-honcho`; Hermes can expose Honcho tools such as reasoning, search, and context.

Source:
`honcho/README.md:48`, `honcho/README.md:176`, `honcho/docs/v3/guides/recipes/unified-memory-setup.mdx:101`

### HON-034: Local/Managed Deployment Split

Feature:
Honcho can run managed at `api.honcho.dev` or self-host as a FastAPI server with background deriver worker.

Daily use:
Live OpenClaw is configured against local `http://127.0.0.1:18001`.

Source:
`honcho/README.md:18`, `honcho/README.md:292`, `honcho/README.md:434`, `~/.openclaw/openclaw.json:666`

### HON-035: Queue and Reconciliation System

Feature:
Honcho stores background work in a queue with work-unit keys, task types, processed state, errors, dedupe indexes, and active queue session tracking.

Daily use:
This is the operational substrate for async reasoning, deletion, dream, and reconciler tasks.

Source:
`honcho/src/models.py:476`

### HON-036: Dreaming Tasks

Feature:
Honcho includes dreamer modules and queue support for dream tasks.

Daily use:
Relevant as future/autonomous memory consolidation substrate, separate from immediate chat/context lookup.

Source:
`honcho/src/dreamer/orchestrator.py`, `honcho/src/models.py:522`

### HON-037: Webhooks

Feature:
Honcho stores webhook endpoints and has webhook routers/delivery code.

Daily use:
Useful for event-driven memory updates or external system integration.

Source:
`honcho/src/models.py:548`, `honcho/src/webhooks/README.md`

## Daily Memory Capability Map

### Exact Local Evidence

Primary system:
QMD.

Use when:

- searching workspace memory/docs/research by exact phrase, path, config key, date, or commit
- retrieving local files or line-numbered snippets
- checking whether indexed docs are stale

Key features:
QMD-006, QMD-009, QMD-014, QMD-027.

### Semantic Local Corpus Recall

Primary system:
QMD.

Use when:

- concept exists in files but exact wording is unknown
- comparing docs/source across memory systems
- collecting evidence before writing specs

Key features:
QMD-007, QMD-008, QMD-011, QMD-012.

### Live Conversation Continuity

Primary system:
Lossless-Claw.

Use when:

- active conversation outgrows context
- recent tail must remain raw
- older turns must stay recoverable
- compaction should not destroy source messages

Key features:
LCM-002, LCM-005, LCM-010, LCM-018.

### Post-Compaction Deep Recall

Primary system:
Lossless-Claw.

Use when:

- summary says "Expand for details about..."
- exact commands, tool outputs, file paths, or config values were compressed
- conversation details may be in old or archived segments

Key features:
LCM-021 through LCM-026.

### Person/Agent/Project Memory

Primary system:
Honcho.

Use when:

- asking what Honcho knows about a person/agent/project
- retrieving preferences, patterns, goals, current priorities, or cross-session understanding
- unifying memory across chat, coding, autonomous agents, and imports

Key features:
HON-001, HON-011, HON-013, HON-016, HON-022, HON-031.

### Prompt Hydration

Primary systems:
Honcho and Lossless-Claw.

Use when:

- current turn needs session context plus peer/user representation
- long-running session needs summary plus recent messages
- model prompt needs compact durable context

Key features:
LCM-018, HON-016, HON-018, HON-021.

### Import and External Data Assimilation

Primary systems:
Honcho and QMD.

Use when:

- adding docs/reports/transcripts for search
- adding emails/meeting notes/tool traces for peer reasoning
- avoiding fragmentation by using stable sessions and peers

Key features:
QMD-002, QMD-020, HON-030, HON-031, HON-032.

### Operational Health and Guardrails

Primary systems:
QMD and Lossless-Claw.

Use when:

- checking stale embeddings
- checking compaction health
- rotating transcript storage
- investigating transcript repair warnings
- preventing cron/subagent memory pollution

Key features:
QMD-027, LCM-014, LCM-028, LCM-032, LCM-035.

## Integration Implications For Engram / Local MemoryCore

### IMPL-001: Keep QMD as Local Corpus Retrieval

QMD should remain the source-backed retrieval layer for local markdown/source/docs. It is strongest where exact evidence, line-level retrieval, local-only operation, and operator-tuned lexical/semantic queries matter.

### IMPL-002: Do Not Treat QMD as Conversation Continuity

QMD indexes files. It does not own turn lifecycle, model-context assembly, transcript reconciliation, or compaction. Those are LCM responsibilities.

### IMPL-003: Keep Lossless-Claw as Turn Continuity and Compaction

LCM should remain the context engine for preserving raw messages, assembling compact prompt state, and enabling drilldown after summarization.

### IMPL-004: Do Not Treat Lossless-Claw as Semantic Corpus Search

LCM recall is transcript/DAG recall. It is not the replacement for QMD's file corpus search or Honcho's reasoned peer memory.

### IMPL-005: Keep Honcho as Reasoned Peer/Session Memory

Honcho should own modeled representations, conclusions, peer cards, natural-language memory answers, and cross-surface user/agent continuity.

### IMPL-006: Avoid Memory Fragmentation

Honcho's unified-memory guidance implies one stable workspace and one stable user peer for Alice/Mitchell continuity, with sessions scoped by channel/project/import. QMD can index many collections; Honcho should unify identity where appropriate.

### IMPL-007: Separate Storage From Insight

QMD and LCM preserve/search source. Honcho derives conclusions. Engram should preserve this distinction: source-contact remains auditable, while derived insight remains marked as derived.

### IMPL-008: Treat Health Gates As Part Of Memory Correctness

Memory correctness requires operational checks:

- QMD embedding freshness and vector sample reproducibility
- LCM summary health, deferred maintenance, and transcript repair state
- Honcho deriver queue health and representation latency

### IMPL-009: Preserve Drilldown Paths

Every derived memory object should have a path back to source:

- QMD result -> document/path/docid/line
- LCM summary -> source messages/parent summaries/file ids
- Honcho conclusion -> source messages/documents/session/observer-observed collection

### IMPL-010: Daily Operator Rule

Use the stack in this order:

1. Need file/source/docs evidence: QMD.
2. Need exact prior conversation detail: LCM grep/describe/expand.
3. Need what is known about a person/agent/project over time: Honcho.
4. Need prompt context now: Honcho context plus LCM assembled context.

