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
                8 MCP tools / CLI verbs [LIVE]:  search · get · verify ·
                health · remember · recall · cache_search · flush
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
│   │ VERIFICATION [WIP] vocabulary live; real backend-proof checks and     │   │
│   │   re-verification policy are the current build frontier              │   │
│   └───────────────────────────────────────────────────────────────────────┘   │
└─────────────┬──────────────────────────┬───────────────────────┬──────────────┘
              │ reads [LIVE]             │ writes [LIVE]         │ [PLAN]
              │ live-local CLI           │ transient content     │
              │ shell-out                │ write-through         │
┌─────────────▼───────────┐ ┌────────────▼───────────┐ ┌─────────▼──────────────┐
│ QMD  [LIVE]             │ │ LCM (Lossless-Claw)    │ │ FUTURE BACKENDS [PLAN] │
│ local corpus index      │ │ [WIP]                  │ │ Honcho (peer memory)   │
│ reads: live-local       │ │ transcript memory      │ │ gbrain (knowledge)     │
│ writes: dedicated       │ │ fixture reads work;    │ │ Notion / Drive / S3    │
│ memorycore-writes       │ │ live path blocked on   │ │ memory fabric          │
│ collection              │ │ bridge-over-MCP        │ └────────────────────────┘
│ proven end-to-end       │ │ transport decision     │
│ 2026-07-04              │ └────────────────────────┘
└─────────────────────────┘

┌───────────────────────────── EVALUATION HARNESS ──────────────────────────────┐
│ [LIVE] 18 deterministic public-safe validators, CI green on every push        │
│ [LIVE] local-only live evals (QMD real index, LCM synthetic store)            │
│ [GATE] EVAL-012 OpenClaw integration smoke -> unlocks the final MVP verdict   │
└────────────────────────────────────────────────────────────────────────────────┘

The proven loop (2026-07-04): an OpenClaw-shaped caller sent remember(content)
-> the cache stamped a provenance pointer -> the content was materialized as a
markdown file with provenance frontmatter -> QMD indexed it -> read-back earned
a "verified" stamp -> recall served the pointer from cache -> QMD's own search
finds the memory.

Currently being worked on: real backend-proof verification (replacing the
caller-asserted stub) and the LCM bridge-over-MCP transport decision that
unblocks live transcript memory.
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
│   ├── ARCHITECTURE.md
│   ├── MVP_READINESS_LEDGER.md
│   ├── MVP_EVAL_PLAN.md
│   ├── OPENCLAW_INTEGRATION_SMOKE_PLAN.md
│   └── PRD.md
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
│   ├── cli.py
│   ├── lcm_adapter.py
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
    ├── validate_memory_record.py
    ├── validate_mvp_cli.py
    ├── validate_mvp_mcp_surface.py
    ├── validate_mvp_audit_log.py
    ├── validate_mvp_packet_a.py
    ├── validate_mvp_packet_b.py
    ├── validate_mvp_packet_c.py
    ├── validate_mvp_lcm_adapter.py
    ├── validate_mvp_qmd_adapter.py
    ├── validate_mvp_provenance_ledger.py
    ├── validate_mvp_verification_state.py
    └── validate_mvp_router.py
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
│   ├── [◐] QMD adapter (fixtures done; live-local shell-out partial)
│   ├── [◐] Lossless-Claw (LCM) adapter (fixtures done; host bridge partial)
│   ├── [○] Backend control ops (register, doctor, reindex, observe-only)
│   ├── [○] Mirroring & splitting policies (one event → many backends)
│   ├── [○] Honcho adapter (peer/session reasoning)
│   ├── [○/·] Gated write & import adapters (append-only, policy-routed)
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
│   ├── [✔] 13+ deterministic public-safe validators + consolidated runner
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

OpenReflect-Local-MemoryCore-Engram is staged as a public skeleton. The current implementation defines the product frame, architecture, synthetic memory-record schema, and deterministic validation.

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

Or run the individual validation scripts directly:

```bash
python3 scripts/validate_memory_record.py examples/memory-record.example.json
python3 scripts/validate_mvp_packet_a.py
python3 scripts/validate_mvp_packet_b.py
python3 scripts/validate_mvp_packet_c.py
python3 scripts/validate_mvp_router.py
python3 scripts/validate_mvp_qmd_adapter.py
python3 scripts/validate_mvp_lcm_adapter.py
python3 scripts/validate_mvp_provenance_ledger.py
python3 scripts/validate_mvp_verification_state.py
python3 scripts/validate_mvp_audit_log.py
python3 scripts/validate_mvp_cli.py
python3 scripts/validate_mvp_mcp_surface.py
```

Expected output:

```text
ENGRAM_MEMORY_RECORD_OK
MEMORYCORE_PACKET_A_OK
MEMORYCORE_PACKET_B_OK
MEMORYCORE_PACKET_C_OK
MEMORYCORE_ROUTER_OK
MEMORYCORE_QMD_ADAPTER_OK
MEMORYCORE_LCM_ADAPTER_OK
MEMORYCORE_PROVENANCE_LEDGER_OK
MEMORYCORE_VERIFICATION_STATE_OK
MEMORYCORE_AUDIT_LOG_OK
MEMORYCORE_CLI_OK
MEMORYCORE_MCP_SURFACE_OK
```

## Public/private model

Use this repository as the generic upstream. Keep environment-specific customizations in private downstream repositories or private branches.

```text
openreflect/openreflect-local-memorycore-engram  public generic framework
private downstream fork                          local credentials, IDs, deployment, logs
```

This keeps the public framework reusable while preserving operational privacy.
