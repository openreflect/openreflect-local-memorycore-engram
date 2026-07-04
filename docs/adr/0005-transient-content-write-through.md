# ADR 0005: Transient Content Write-Through

Status: accepted 2026-07-03.

## Context

The cache is content-sparse: it stores pointers, never prose. That means
`memorycore_remember` can only reference content that already lives
somewhere. New content authored by a caller (an OpenClaw session keeping a
thought, decision, or note) has no path into a backend.

Three options were considered for how content travels: transient
pass-through, a local spool file held until flush, and storing content in
the cache. The operator selected transient pass-through.

## Decision

1. `memorycore_remember` accepts an optional `content` field. Content is
   held in process memory only for the duration of the call. It is never
   written to the cache, the audit log, or the provenance ledger.
2. A remember call that carries content becomes a synchronous
   write-through: MemoryCore materializes the content into the routed
   backend during the call, and the cache stores the resulting pointer
   with `flush_state: "flushed"`. Pointer-only remembers keep the existing
   pending/flush lifecycle.
3. QMD materialization: content is written as a markdown file with YAML
   provenance frontmatter (`memorycore: true`, memory id, memory type,
   client surface, timestamp) into a dedicated operator-approved
   collection directory, followed by an allowlisted `qmd update` and a
   read-back `get` that earns the `verified` stamp. MemoryCore never
   writes into existing operator collections.
4. LCM write-through is deferred until the host-bridge transport decision
   (frontier item: bridge over MCP). Until then, transcript remembers that
   carry content fail with a structured `backend_unavailable` error.
5. Failure semantics: if materialization or indexing fails, the call
   returns a structured error, nothing is cached, and the content is
   dropped. The caller owns retry. There is no spool.
6. Fixture mode performs no disk or subprocess work: remember-with-content
   returns a synthesized pointer disclosed with
   `write_mode: "fixture-only"`, mirroring the flush disclosure rule.

## Consequences

- The content-sparse persistence contract survives unchanged; content
  exists on disk only inside backend-owned corpora.
- Write-through makes delivery synchronous, so callers get a real pointer
  (or a real error) immediately; there is no pending window for content.
- A failed write-through loses the content by design. If that proves
  painful in practice, the spool option can be revisited as a follow-up
  ADR without changing the caller contract.
- The dedicated collection keeps MemoryCore-authored files separable,
  inspectable, and deletable as a unit.
