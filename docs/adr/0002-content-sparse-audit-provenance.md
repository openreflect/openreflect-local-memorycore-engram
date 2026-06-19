# ADR 0002: Content-Sparse Audit And Provenance

Status: proposed.

## Context

MemoryCore must explain where memory answers came from without becoming another
private memory store.

## Decision

Audit and provenance records default to pointers, metadata, and verification
state rather than raw memory content.

## Consequences

- Logs are safer to inspect and share.
- Debugging may require a local-only follow-up step to inspect source content.

