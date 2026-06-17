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
│   └── PRD.md
├── examples/
│   └── memory-record.example.json
├── fixtures/
│   ├── corpus/
│   ├── backend-registry/
│   ├── mock-backends/
│   └── requests/
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
    ├── validate_mvp_packet_a.py
    └── validate_mvp_packet_b.py
```

## Current status

OpenReflect-Local-MemoryCore-Engram is staged as a public skeleton. The current implementation defines the product frame, architecture, synthetic memory-record schema, and deterministic validation.

Run the public-safe eval:

```bash
python3 scripts/validate_memory_record.py examples/memory-record.example.json
python3 scripts/validate_mvp_packet_a.py
python3 scripts/validate_mvp_packet_b.py
```

Expected output:

```text
ENGRAM_MEMORY_RECORD_OK
MEMORYCORE_PACKET_A_OK
MEMORYCORE_PACKET_B_OK
```

## Public/private model

Use this repository as the generic upstream. Keep environment-specific customizations in private downstream repositories or private branches.

```text
openreflect/openreflect-local-memorycore-engram  public generic framework
private downstream fork                          local credentials, IDs, deployment, logs
```

This keeps the public framework reusable while preserving operational privacy.
