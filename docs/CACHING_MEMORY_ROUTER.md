# Design Note: Caching Memory Router

Status: draft sketch, 2026-07-02. Not yet scoped into the MVP ledger.

## Idea

Simplify Engram's read/write story to a single shape: a minimal
`read / write / search` surface in front, a local cache store in the
middle, and typed backends behind adapters. Engram becomes a caching
router between memory types rather than a family of bespoke paths.

```text
caller (CLI / MCP / OpenClaw)
        |
        v
  read | write | search        <- three verbs, one contract
        |
        v
  +-------------------+
  |   local cache     |        <- SQLite; every record stamped with
  |   (= provenance   |           pointer + verification state on entry
  |    ledger)        |
  +-------------------+
        |
        v
  route by memory type
        |
        +--> QMD      (file / corpus recall)
        +--> LCM      (transcript continuity)
        +--> Honcho   (peer / session reasoning, later)
        +--> others   (fabric substrates, later)
```

## Write path

1. Caller issues `write(record)`.
2. Record lands in the cache first: fast, durable, provenance-stamped.
3. A flush policy sends it onward by memory type. Transcript events go
   to LCM, file artifacts to QMD, peer observations to Honcho later.
4. Flush outcomes update the record's verification state. Unflushed
   records are still readable from cache and marked accordingly.

Writes to backends stay gated and append-only, per the existing
adapter boundaries (ADR-0003, ADR-0004).

## Read path

1. Caller issues `read(pointer)` or `search(query)`.
2. Cache is checked first. A hit returns with its stored verification
   state.
3. A miss falls through to the routed backend, and the result is
   re-cached with a fresh pointer and verification stamp.

## Why the cache is not extra machinery

The cache in the middle *is* the provenance ledger. Every record that
passes through gets its pointer, timestamps, and freshness state as a
side effect of being cached. No separate bookkeeping pass.

Two roadmap items collapse into cache policy instead of standing
features:

- Mirroring = flush the same cached record to more than one backend.
- Splitting = flush different parts of one cached event to different
  backends.

## Minimal schema

One table to start:

```text
cache_records
  record_id        stable id
  memory_type      routing key (file_corpus | transcript | peer | ...)
  content_ref      content or content-sparse pointer, per audit rules
  source_pointer   provenance pointer (backend_id, pointer_id, uri)
  verification     verified | stale | missing | unsupported | unknown
  flush_state      pending | flushed | failed | mirrored
  created_at / updated_at
```

Content-sparse rules from the API contract and threat model apply
unchanged: the cache stores pointers and bounded fields by default,
not private content.

## What this reuses

- `registry_router.py` — routing by intent becomes routing by
  memory type; same registry, same capability model.
- `provenance_ledger.py` — becomes the cache's stamp-on-entry step.
- `verification_state.py` — vocabulary used as-is for cache hits.
- Adapters — unchanged read normalization; flush is the only new verb.

## What this defers

- Reasoning/insight engines (separate product layer).
- Full indexing engine; cache search can start as FTS over cached
  records only.
- Cross-backend identity mapping beyond the pointer fields above.

## Direction: attributed multi-backend recall (EN-021)

Adopted direction 2026-07-16: MemoryCore evolves from a switch (pick one
backend per intent) toward a synthesizer — consult multiple memory
technologies simultaneously and merge results with per-item attribution.

- Fan-out reads: one recall query dispatched to all capable backends.
- Attributed merge: the assembled bundle preserves each item's backend,
  pointer, verification state, and relevance — never anonymous soup.
- Cross-backend identity: mirrored records are recognized as one memory.
- Attribution is the product surface: every assembled context answers
  "who contributed what, and how trustworthy is each piece."

The merge contract should be designed before the governance evidence
envelope (OG-003 in the composition register) freezes, so the envelope
carries multi-source attribution from day one.

## Open questions

- Write-through vs write-back default per memory type.
- Cache eviction: probably none for MVP (memory is the product).
- Whether flush failures should degrade to witness-only records or
  retry queues.
