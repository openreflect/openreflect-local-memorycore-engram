# Claude Opus MemoryCore Feasibility Assessment

Date: 2026-06-16
Project: OpenReflect Local MemoryCore / Engram
Status: Associate assessment
Reviewer lane: Claude Code associate, `--model opus`
Source files reviewed:

- `docs/PRD.md`
- `docs/MEMORYCORE_SOFTWARE_SPEC.md`
- `docs/CLAUDE_OPUS_READINESS_ASSESSMENT_2026-06-15.md`
- `research/memory-virtualization-write-adapter-research-2026-06-15.md`

## Blunt Verdict

Opus says the current product direction is technically feasible only if
MemoryCore v0.1 is treated as a routing/provenance control plane, not as a
replacement memory database.

The main contradiction is now explicit:

- `docs/PRD.md` says MemoryCore should not replace vector search, transcript
  summarization, or external memory systems.
- `research/memory-virtualization-write-adapter-research-2026-06-15.md` says
  MemoryCore should sit above distinct backends as a capability-aware memory
  fabric.
- `docs/MEMORYCORE_SOFTWARE_SPEC.md` now has the correct routing/control-plane
  positioning after commit `ec78332`, but still contains replacement-era
  storage, indexing, summary, and reasoning sections.

Opus's core judgment:

> The prose says route while the storage model, reasoning engine, summary DAG,
> and observation tables say replace.

## Feasible As Written

The technically feasible pieces are:

- Backend registry and capability probing.
- Read-path fabric over existing backends.
- Native-safe write adapters that enter through backend write APIs rather than
  direct database mutation.
- Normalized operation and record envelopes.
- Provenance and verification contracts.
- A QMD + LCM first MVP.

The strongest current foundation is the adapter research document, because it
maps real backend write/read paths and native invariants.

## Category Errors

Opus flagged these as the main category errors:

- The spec mixes replacement and orchestration in the same document.
- The storage model is still a replacement design because it owns messages,
  summaries, observations, embeddings, and context packets.
- The LCM retrieval-layer rule is correct, but the owned message/summary schema
  undercuts it.
- The I/O grid currently includes model routing, browser, email, agent, and
  coding-task lanes, which pushes MemoryCore beyond a memory/context control
  plane.
- The event taxonomy is inconsistent: the grid and canonical event list do not
  name the same types.
- `RecallIndex` and `SemanticIndex` are service lanes, not normalized input
  event types.

## Routing Positioning

Opus agrees with the new positioning from `ec78332`:

- MemoryCore should be a backend routing and provenance control plane.
- It is not a frontend router.
- It is not only a model gateway.
- It is not an agent framework.
- It is not a sandbox.
- It sits between context/provenance infrastructure and reasoning
  orchestration.

The required correction is to propagate that decision through the rest of the
spec. The positioning section is correct, but much of the lower-level design
still assumes MemoryCore owns the data plane.

## I/O Grid And LCM Rule

Opus says the LCM rule is correct and should be generalized:

> No retrieval, indexing, or reasoning substrate is ever `authority: source`.

Examples:

- LCM is a recall/provenance endpoint over transcript material.
- QMD semantic index is an index over source files.
- Honcho conclusions are derived reasoning artifacts.

The I/O grid is useful as a sketch, but should be narrowed to memory,
context, retrieval, and provenance. Non-memory rows should move to future scope
or be removed from v0.1.

## MemoryCore-Owned Tables For v0.1

Under the routing-control-plane assumption, Opus recommends these tables only:

### `backends`

Adapter registry.

Fields:

- `id`
- `kind`: `qmd | lcm | honcho | gbrain`
- `name`
- `endpoint_uri`
- `capabilities_json`
- `status`: `up | degraded | down`
- `last_seen_at`
- `config_json`

### `provenance_pointers`

Pointer ledger.

Fields:

- `id`
- `backend_id`
- `backend_ref`
- `artifact_kind`: `file | git | transcript | message | tool_call | import`
- `uri`
- `content_hash`
- `git_commit`
- `file_path`
- `line_start`
- `line_end`
- `transcript_id`
- `message_seq`
- `tool_call_id`
- `captured_at`
- `metadata_json`

### `requests`

Routing audit log.

Fields:

- `id`
- `intent_type`: `search | write | verify | get`
- `normalized_intent_json`
- `candidate_backends_json`
- `selected_backend_ids_json`
- `status`
- `latency_ms`
- `error`
- `created_at`

### `result_refs`

Request-result pointer table.

Fields:

- `id`
- `request_id`
- `backend_id`
- `backend_ref`
- `provenance_id`
- `score`
- `rank`
- `snippet_cache`
- `snippet_hash`
- `created_at`

### `identity_map`

Logical identity across backends.

Fields:

- `id`
- `logical_id`
- `kind`: `peer | session | collection`
- `backend_id`
- `backend_native_id`
- `created_at`

### `verifications`

Verification ledger.

Fields:

- `id`
- `provenance_id`
- `claim_ref`
- `verdict`: `current | stale | unsupported`
- `source_hash_at_check`
- `checked_at`
- `detail_json`

### `schema_migrations`

Fields:

- `version`
- `applied_at`

Deleted from v0.1:

- `memory_records`
- `messages`
- `message_parts`
- `summaries`
- `summary_edges`
- `summary_sources`
- `observations`
- `observation_sources`
- `embeddings`
- `index_jobs`
- `reasoning_jobs`
- `context_packets`

Those are backend-owned in the routing model.

## Snippet Boundary

Default should be pointers only.

MemoryCore may persist snippets only as disposable cache if:

- The snippet is a verbatim span returned by a backend.
- It is bounded, with a hard cap around 512 characters.
- It is keyed to `snippet_hash` and provenance/source hash.
- It inherits the backend privacy class.
- It is excluded from export by default.
- Search never runs over snippet cache.

MemoryCore must not store full documents, full messages, full transcripts,
MemoryCore-authored summaries, observations, or derived text.

## Minimal Adapter Interfaces

```ts
type BackendKind = "qmd" | "lcm" | "honcho" | "gbrain";
type SearchMode = "lex" | "vec" | "hybrid";
type PrivacyClass = "public" | "private" | "secret";

interface ProvenancePointer {
  backendId: string;
  backendRef: string;
  artifactKind: "file" | "git" | "transcript" | "message" | "tool_call" | "import";
  uri?: string;
  contentHash?: string;
  gitCommit?: string;
  filePath?: string;
  lineStart?: number;
  lineEnd?: number;
  transcriptId?: string;
  messageSeq?: number;
  capturedAt: string;
}

interface SearchIntent {
  query: string;
  mode?: SearchMode;
  limit?: number;
  collections?: string[];
  sessionId?: string;
  filters?: Record<string, unknown>;
}

interface SearchResult {
  backendId: string;
  backendRef: string;
  provenance: ProvenancePointer;
  score: number;
  rank: number;
  snippet?: string;
  privacyClass: PrivacyClass;
}

interface WriteIntent {
  kind: "message" | "note" | "artifact";
  payload: unknown;
  sessionId?: string;
  peerId?: string;
  privacyClass?: PrivacyClass;
}

interface WriteResult {
  backendId: string;
  backendRef: string;
  provenance: ProvenancePointer;
}

interface VerifyResult {
  provenanceId: string;
  verdict: "current" | "stale" | "unsupported";
  sourceHashAtCheck?: string;
  checkedAt: string;
  detail?: string;
}

interface BackendStatus {
  backendId: string;
  kind: BackendKind;
  status: "up" | "degraded" | "down";
  capabilities: {
    search: SearchMode[];
    write: boolean;
    verify: boolean;
  };
  lastSeenAt: string;
  latencyMsP50?: number;
}

interface Adapter {
  readonly id: string;
  readonly kind: BackendKind;
  status(): Promise<BackendStatus>;
  search(intent: SearchIntent): Promise<SearchResult[]>;
  get(backendRef: string): Promise<{ content?: string; provenance: ProvenancePointer }>;
  write?(intent: WriteIntent): Promise<WriteResult>;
  verify?(p: ProvenancePointer): Promise<VerifyResult>;
}
```

## MVP Acceptance Scenario

MVP target:

- QMD adapter registered as search/get/verify, no write.
- LCM adapter registered as search/get/write/verify.
- MemoryCore stores pointers, not backend content.

Golden path:

1. Register QMD and LCM adapters.
2. Submit a write intent for a session message.
3. Router selects LCM because it has write capability.
4. Write result returns an LCM `backend_ref`.
5. MemoryCore stores a provenance pointer, not the message content.
6. Submit a search intent.
7. Router fans out to QMD and LCM.
8. Each result carries `backend_id`, `backend_ref`, source pointer, score, and
   optional bounded snippet.
9. `get` fetches live content from the backend, not MemoryCore state.
10. `verify` returns `current`.
11. Mutate the underlying source file or transcript fixture.
12. `verify` returns `stale` or `unsupported`, depending on backend capability.
13. If one backend is down, the request degrades gracefully and records the
   skipped candidate in `requests`.

## Immediate Spec Edits Recommended

Opus recommends Alice apply these after the route/orchestrate decision is
explicitly accepted:

1. Rewrite Purpose and Product Modules to control-plane framing.
2. Replace Required Tables with the control-plane schema above.
3. Move Indexing Engine, Transcript/Context Engine, and Reasoning Engine to a
   backend-owned appendix.
4. Scope the I/O grid to memory substrates only.
5. Add Adapter Contracts and MVP Acceptance Test sections.

## Decisions For Mitchell

These decisions gate implementation:

1. Ratify v0.1 as a routing control plane, not a replacement store.
2. Decide pointer-only vs bounded snippet cache.
3. Decide whether v0.1 owns any write path or starts read/verify-only.
4. Decide whether MemoryCore creates git commits or only records pointers and
   hashes supplied by sources/backends.
5. Decide whether MemoryCore owns canonical peer/session identity or defers to
   backend-native ids.
6. Confirm implementation language, likely TypeScript/Bun.

## Alice's Operational Read

The technical feasibility is good if v0.1 is narrowed to:

- adapter registry,
- QMD + LCM read fabric,
- provenance pointer ledger,
- verification contract,
- one safe LCM write path, if writes are in MVP.

The technical feasibility is poor if v0.1 tries to be the whole memory system:
owned content store, embeddings, summaries, observations, context packet
assembler, agent router, model router, and tool router.

The next spec move should be controlled surgery, not more additive prose.
