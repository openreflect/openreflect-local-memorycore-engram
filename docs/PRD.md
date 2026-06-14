# OpenReflect-Local-MemoryCore-Engram PRD

## Product thesis

Engram is a local memory-core that makes AI memory inspectable. It anchors semantic recall and agent-generated insight to versioned source records.

## Goals

- Store durable memory records with source provenance.
- Attach commit hashes or equivalent version pointers to recallable records.
- Support branchable reasoning paths.
- Detect stale semantic memories by comparing recalled claims to source state.
- Provide public-safe schemas and examples.

## Non-goals

- Replacing vector search, transcript summarization, or external memory systems.
- Publishing private memory content.
- Depending on a single model provider.
- Treating summaries as authoritative without source verification.

## v0.1 requirements

- Define a public memory-record schema.
- Validate synthetic memory records.
- Document the git-native memory-core pattern.
- Keep operational memory stores outside the public repo.

## Success criteria

- A synthetic memory record validates deterministically.
- Public docs explain how semantic recall can verify against durable source state.
- The repo contains no private paths, account IDs, transcript exports, or secrets.
