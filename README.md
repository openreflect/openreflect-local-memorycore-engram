# OpenReflect-Local-MemoryCore-Engram

OpenReflect-Local-MemoryCore-Engram is a local memory-core and provenance substrate for AI-assisted reasoning systems.

Its core idea is simple: semantic memory is useful, but durable reasoning needs provenance. Engram uses git-native primitives such as commits, branches, diffs, tags, and blame as an inspectable memory backbone that can anchor higher-level recall systems.

## Why it exists

AI systems often retrieve summaries, embeddings, or compressed memories without a reliable way to prove where a claim came from or whether it is stale. That makes memory feel fluent while weakening trust.

Engram exists to bind memory records back to durable source state. It gives recall systems a local, versioned substrate where a memory pointer can be checked against the exact commit, file, diff, or branch that produced it.

## Core idea

```text
source records
     |
     v
git-backed memory core
     |
     +--> commits as decision points
     +--> branches as reasoning paths
     +--> diffs as changes in understanding
     +--> tags as semantic markers
     +--> blame/log as provenance checks
     |
     v
semantic recall systems + insight agents
```

Engram does not replace semantic search or summarization. It gives those systems a local provenance layer they can cite, verify, branch, and repair.

## Architecture status map

```text
 Legend: [LIVE] operational, proven   [WIP] being worked on   [PLAN] designed only
         [GATE] awaiting operator approval (EVAL-012 hard stop)

┌─────────────────────────────────── CALLERS ───────────────────────────────────┐
│                                                                               │
│   OpenClaw sessions            Operator CLI             Any MCP client        │
│   [GATE] live connect          [LIVE] search, get,      [LIVE] FastMCP        │
│   surface ready; smoke         verify, health, audit,   stdio / sse /         │
│   blocked by EVAL-012          eval --public-safe       streamable-http       │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
                9 MCP tools / CLI verbs [LIVE]:  search · get · verify ·
                health · remember · recall · cache_search · flush ·
                confirm_delivery
                                       │
┌──────────────────────────────────────▼────────────────────────────────────────┐
│                         MEMORYCORE CONTROL PLANE                              │
│                                                                               │
│   ┌──────────────────────────┐      ┌───────────────────────────────────┐     │
│   │ BACKEND ROUTER  [LIVE]   │      │ CACHING MEMORY ROUTER  [LIVE]     │     │
│   │ intent -> backend,       │      │ SQLite cache as provenance        │     │
│   │ health-aware routing,    │      │ anchor; write / read / search;    │     │
│   │ fixture | live-local     │      │ flush by memory type; transient   │     │
│   │ mode switch              │      │ content write-through (ADR-0005)  │     │
│   └──────────────────────────┘      └───────────────────────────────────┘     │
│                                                                               │
│   ┌───────────────────────────────────────────────────────────────────────┐   │
│   │ AUDIT LOG [LIVE] content-sparse, client-attributed                    │   │
│   │ PROVENANCE LEDGER [LIVE] pointer-first records                        │   │
│   │ VERIFICATION [LIVE] QMD backend-proof (disk+index+hash); verdicts     │   │
│   │   update cached stamps; LCM describe + TTL re-verification [PLAN]    │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
└─────────────┬──────────────────────────┬───────────────────────┬──────────────┘
              │ reads [LIVE]             │ writes [LIVE]         │ [PLAN]
              │ live-local CLI           │ transient content     │
              │ shell-out                │ write-through         │
┌─────────────▼───────────┐ ┌────────────▼───────────┐ ┌─────────▼──────────────┐
│ QMD  [LIVE]             │ │ LCM (Lossless-Claw)    │ │ FUTURE BACKENDS [PLAN] │
│ local corpus index      │ │ [LIVE] contract        │ │ Honcho (peer memory)   │
│ reads: live-local       │ │ transcript memory      │ │ gbrain (knowledge)     │
│ writes: dedicated       │ │ callback delivery      │ │ Notion / Drive / S3    │
│ memorycore-writes       │ │ built (ADR-0006); live │ │ memory fabric          │
│ collection              │ │ executor + describe    │ └────────────────────────┘
│ proven end-to-end       │ │ verify gated: EVAL-012 │
│ 2026-07-04              │ └────────────────────────┘
└─────────────────────────┘

┌───────────────────────────── EVALUATION HARNESS ──────────────────────────────┐
│ [LIVE] 20 deterministic public-safe validators, CI green on every push        │
│ [LIVE] local-only live evals (QMD real index, LCM synthetic store)            │
│ [GATE] EVAL-012 OpenClaw integration smoke -> unlocks the final MVP verdict   │
└────────────────────────────────────────────────────────────────────────────────┘

Proven loops on the real local index:
- Write (2026-07-04): remember(content) -> cache stamps pointer -> markdown
  materialized with provenance frontmatter -> QMD indexes -> read-back earns
  "verified" -> recall hits cache -> QMD search finds the memory.
- Verify (2026-07-05): a memory whose source file was deleted honestly flipped
  to "missing" (despite index lag); a modified source flips to "stale"; the
  intact one re-proved "verified" — verdicts persist to the cached stamps.

Remaining before the MVP verdict: the OpenClaw-side delivery executor and
LCM describe-verify (both exercised live only after the EVAL-012 hard stop is
lifted), plus operational hardening (WAL, request ids, idempotency, retry).
```

## What OpenReflect-Local-MemoryCore-Engram manages

- Git-native memory records and provenance pointers.
- Commit hashes attached to higher-level memory entries.
- Branchable reasoning experiments.
- Staleness checks for semantic recall outputs.
- Versioned reflection, analysis, and decision artifacts.
- Public-safe synthetic memory records for validation.

## Design principles

- Treat provenance as part of memory, not metadata added later.
- Prefer durable local records over opaque recall claims.
- Let semantic systems search broadly, then verify through git.
- Keep private memory contents outside the public repo.
- Make branch, diff, and restore behavior inspectable.
- Support local-first operation with optional external integrations.

## Repository layout

```text
.
├── AGENTS.md
├── README.md
├── docs/
│   ├── REGISTER.md                  (QTrellis product register)
│   ├── ARCHITECTURE.md
│   ├── AGENT_CONTEXT.md             (first-load map for agent sessions)
│   ├── CACHING_MEMORY_ROUTER.md
│   ├── CACHE_API_OPENCLAW.md
│   ├── MVP_READINESS_LEDGER.md
│   ├── MVP_EVAL_PLAN.md
│   ├── OPENCLAW_INTEGRATION_SMOKE_PLAN.md
│   ├── PRD.md
│   └── adr/                         (0001..0006)
├── examples/
│   └── memory-record.example.json
├── fixtures/
│   ├── corpus/
│   ├── errors/
│   ├── backend-registry/
│   ├── lcm/
│   ├── mcp/
│   ├── mock-backends/
│   ├── qmd/
│   └── requests/
├── memorycore/
│   ├── audit_log.py
│   ├── cache_router.py
│   ├── cli.py
│   ├── eval.py
│   ├── lcm_adapter.py
│   ├── mcp_server.py
│   ├── mcp_surface.py
│   ├── provenance_ledger.py
│   ├── qmd_adapter.py
│   ├── registry_router.py
│   └── verification_state.py
├── prompts/
│   └── validate-memory-record.prompt.md
├── schemas/
│   ├── error.schema.json
│   ├── backend.schema.json
│   ├── memory-record.schema.json
│   ├── request.schema.json
│   └── result.schema.json
└── scripts/
    └── validate_*.py                (20 deterministic public-safe validators
                                      plus local-only live evals and helpers)
```

## Feature treemap

A hierarchical map of features and subfeatures, both implemented and planned, compiled from the project docs (SPEC, PRD, software spec, roadmap, risk register, threat model, research notes).

Legend: `[✔] done` · `[◐] partial` · `[○] planned` · `[·] implied-only (mentioned once in research/roadmap)`

```text
ENGRAM / MEMORYCORE
│
├── 1. MEMORY RECORDS & SCHEMAS
│   ├── [✔] Request / result / error / backend JSON contracts
│   ├── [✔] Contract-security drift eval
│   ├── [◐] Memory-record contract (schema done; rich typed records planned)
│   ├── [◐] Provenance pointer model (basic done; commit/diff/line-range fields planned)
│   ├── [○] Source-artifact model (path+hash, commit, transcript, tool-call, import)
│   ├── [○] Derived-observation model (deductive/inductive/abductive, confidence)
│   ├── [○] Summary model (DAG parents, covered range, source-set hash)
│   ├── [○] Context-packet model (assembled context + omission diagnostics)
│   ├── [○] Storage layer (SQLite+WAL+FTS5, ~17 tables; Postgres later)
│   └── [·] Normalized record envelope for the memory fabric
│
├── 2. PROVENANCE & VERIFICATION            ← the product's core bet
│   ├── [✔] Provenance pointer ledger
│   ├── [✔] Verification states (verified/stale/missing/unsupported/unknown)
│   ├── [✔] "Never present unknown as verified" rule
│   ├── [✔] Real backend-proof verification (QMD: disk+index+hash, stamps update)
│   ├── [○] Git-native provenance engine
│   │   ├── [○] Commit pointers & content hashes
│   │   ├── [○] Diff-based staleness checks
│   │   ├── [○] Branchable reasoning experiments
│   │   ├── [○] Tags as semantic milestones
│   │   ├── [○] Blame/log inspection
│   │   └── [○] Exportable evidence bundles
│   └── [·] Cross-backend verification semantics (per-backend proof rules)
│
├── 3. BACKEND ROUTING & ADAPTERS           ← the "virtualization" layer
│   ├── [✔] Backend registry, capability probe, health
│   ├── [✔] Request normalization + deterministic intent routing
│   ├── [✔] Mock backend + fixtures
│   ├── [✔] Caching memory router + OpenClaw cache API (remember/recall/flush)
│   ├── [✔] QMD adapter (live reads, transient write-through, real verify)
│   ├── [◐] Lossless-Claw (LCM) adapter (callback contract built; live executor gated)
│   ├── [○] Backend control ops (register, doctor, reindex, observe-only)
│   ├── [○] Mirroring & splitting policies (one event → many backends)
│   ├── [○] Honcho adapter (peer/session reasoning)
│   ├── [◐] Gated write & import adapters (QMD write-through + LCM callback built)
│   ├── [·] gbrain adapter (knowledge-brain pages)
│   └── [·] Backend classes taxonomy (corpus / transcript / peer / brain / fabric)
│
├── 4. INTERFACES
│   ├── [✔] CLI (search, get, verify, health, audit, backends)
│   ├── [✔] Consolidated eval command (memorycore eval --public-safe)
│   ├── [✔] MCP tool surface + real FastMCP server (stdio/sse/http)
│   ├── [◐] OpenClaw integration (gated behind EVAL-012 hard stop)
│   ├── [○] Production MCP handoff (session ids, cancellation, packaging)
│   ├── [○] Full CLI verbs (init, ingest, index, recall, context, doctor…)
│   ├── [○] HTTP/REST API + SDK primitives
│   ├── [○] Operator UI (summary-DAG viewer, provenance drilldown, doctor)
│   ├── [○] Hermes / Codex / desktop-app plugin paths
│   └── [·] Nontraditional substrates (Notion, Drive, S3, spreadsheets…)
│
├── 5. RETRIEVAL, CONTEXT & REASONING       ← full-product ambition, nearly all planned
│   ├── [○] Indexing engine (chunking, BM25+vector hybrid, rerank, doctor)
│   ├── [○] Transcript/context engine (fresh tail, summary DAG, deep recall)
│   ├── [○] Reasoning engine (async observation extraction, peer cards)
│   └── [○] Insight-plugin lane (scoped mining jobs, privacy gates)
│
├── 6. EVALUATION & VALIDATION
│   ├── [✔] 20 deterministic public-safe validators + consolidated runner
│   ├── [✔] Fixture corpus (8 families) + CI on every push
│   ├── [✔] Parallel agent work packets (PACKET-01…10)
│   ├── [◐] E2E golden path (CLI+MCP pass; OpenClaw leg blocked)
│   ├── [◐] Local-only live evals (QMD, LCM; skipped in public runs)
│   ├── [○] EVAL-012 OpenClaw smoke (planned, hard-stopped, template ready)
│   └── [○] pytest bridge
│
├── 7. OBSERVABILITY & OPS
│   ├── [✔] Content-sparse audit log (deny-listed private fields)
│   ├── [✔] Backend health + graceful degradation
│   ├── [◐] Observability event vocabulary (allowlist/denylist defined)
│   ├── [◐] Runbook, performance baseline, migration plan (scaffolds)
│   ├── [○] Full doctor checks (index integrity, stale embeddings, DAG health)
│   └── [○] Cost/token & spend diagnostics
│
├── 8. SECURITY & PRIVACY
│   ├── [✔] Content-sparse persistence contract (no snippets/secrets at rest)
│   ├── [✔] Verification-misrepresentation controls
│   ├── [◐] Retrieved-content-is-untrusted rule (prompt-injection control)
│   ├── [◐] Live-command allowlisting, timeouts, redacted logging
│   ├── [◐] Public/private boundary discipline + trust-boundary map
│   ├── [○] Per-record privacy classes, secret scanning, export audit
│   └── [○] Pre-release leak checks
│
└── 9. ROADMAP HORIZONS
    ├── [◐] v0.1  Control-plane foundation (mostly the ✔/◐ items above)
    ├── [○] v0.1.5 Hermes path, contract hardening, gated writes
    ├── [○] v0.2  Insight plugins, mirroring/splitting, Codex path
    └── [○] Later  Backup/migration, identity mapping, visualization,
                   Postgres/hosted sync, memory-fabric expansion
```

## Current status

The control plane is operational: a caching memory router (SQLite as
provenance anchor) sits behind a nine-tool MCP surface and CLI, with live
QMD reads, transient content write-through into a dedicated collection, real
backend-proof verification (both proven against a real local index), and the
callback delivery contract for LCM transcript writes (ADR-0006). Fixture mode
remains the public-safe default; live paths sit behind explicit env flags.
Product state is tracked as a QTrellis register in `docs/REGISTER.md`; agent
sessions start from `docs/AGENT_CONTEXT.md`.

EVAL-012 OpenClaw integration smoke is planned but not executed. The smoke
boundary and stop conditions are documented in
`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`, including the pre-execution
checklist and run-note template that must be filled when the current
integration hard stop is lifted.

The current MVP completion state is tracked in
`docs/MVP_READINESS_LEDGER.md`. The ledger separates complete fixture-first
kernel work from the blocked OpenClaw smoke and the final MVP verdict.

Run the public-safe eval:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e ".[eval]"
python3 -m memorycore.cli eval --public-safe
```

The editable install also exposes the same CLI as a console script:

```bash
memorycore eval --public-safe
```

The direct module command remains the canonical compatibility path for agents
and scripts that run from a checkout.

The consolidated run executes all 20 public-safe validators; each can also be
run directly (`python3 scripts/validate_mvp_<name>.py`), printing its OK token:

```text
ENGRAM_MEMORY_RECORD_OK          MEMORYCORE_CONTRACT_SECURITY_OK
MEMORYCORE_PACKET_A_OK           MEMORYCORE_CACHE_ROUTER_OK
MEMORYCORE_PACKET_B_OK           MEMORYCORE_CACHE_API_OK
MEMORYCORE_PACKET_C_OK           MEMORYCORE_LIVE_MODE_OK
MEMORYCORE_ROUTER_OK             MEMORYCORE_WRITE_THROUGH_OK
MEMORYCORE_QMD_ADAPTER_OK        MEMORYCORE_REAL_VERIFY_OK
MEMORYCORE_LCM_ADAPTER_OK        MEMORYCORE_CALLBACK_DELIVERY_OK
MEMORYCORE_PROVENANCE_LEDGER_OK  MEMORYCORE_E2E_GOLDEN_PATH_OK
MEMORYCORE_VERIFICATION_STATE_OK MEMORYCORE_CLI_OK
MEMORYCORE_AUDIT_LOG_OK          MEMORYCORE_MCP_SURFACE_OK
```

## Public/private model

Use this repository as the generic upstream. Keep environment-specific customizations in private downstream repositories or private branches.

```text
openreflect/openreflect-local-memorycore-engram  public generic framework
private downstream fork                          local credentials, IDs, deployment, logs
```

This keeps the public framework reusable while preserving operational privacy.
