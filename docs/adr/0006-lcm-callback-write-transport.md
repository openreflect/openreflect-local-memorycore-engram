# ADR 0006: LCM Callback Write Transport

Status: accepted 2026-07-14.

## Context

LCM (Lossless-Claw) lives inside OpenClaw's process. MemoryCore runs as a
separate MCP server process and cannot call `engine.ingest()` across that
boundary, so transcript memories captured by the cache have no delivery
path (register: RISK-001). Three transports were considered:

1. Callback: OpenClaw executes the LCM write itself on MemoryCore's
   instruction.
2. Sidecar: OpenClaw hosts a local socket service wrapping LCM ingest and
   describe; MemoryCore proxies writes through it.
3. Punt: ship v0.1 QMD-only and defer transcript writes.

## Decision

Adopt the callback transport. MemoryCore stays in the middle logically —
capture, cache, provenance stamp, audit, and verification all happen in
MemoryCore — while the physical write into LCM is executed by OpenClaw,
the process that owns LCM's safe write entrance.

Flow for a transcript remember that carries content:

1. Caller sends `memorycore_remember` (memory_type `transcript`, content).
2. MemoryCore caches a pending record, stamps provenance, audits the call,
   and returns a delivery instruction in the response: the record id plus
   the content to ingest. Content remains transient (ADR-0005): echoed in
   the response only, never persisted by MemoryCore.
3. OpenClaw's own plugin ingests through `engine.ingest()` /
   `engine.ingestBatch()` — LCM's native entrance, preserving session
   queuing, dedup, message parts, and summary lineage.
4. OpenClaw confirms delivery back to MemoryCore with the resulting
   summary/message pointer; MemoryCore updates the cached record to
   `flushed` and stores the pointer.
5. Verification uses `lcm_describe` on the stored pointer — existence
   confirmed is the only accepted LCM proof (ADR-0004, RISK-008 rules).

## Rationale

- LCM's ingest assumes in-process invocation; the callback keeps writes on
  that native path. A sidecar would wrap the same calls in a new always-on
  service — the same code plus a daemon to launch, monitor, and secure.
- No new moving parts: the callback is one tool registration in OpenClaw's
  existing plugin configuration.
- Trust guarantees are unchanged: nothing reaches LCM that MemoryCore did
  not record first, and delivery is not trusted until confirmed and
  describable.

## Escape hatch

If clients other than OpenClaw ever need transcript writes, the sidecar
becomes worth its keep as a standalone LCM service. This decision does not
preclude it; the delivery-instruction contract defined here would simply
gain a second executor.

## Consequences

- The write path is two-legged for transcripts: unconfirmed deliveries
  remain `pending` with a structured state a retry pass can pick up.
- A delivery-confirmation surface (new tool) must be added to the cache
  API before the LCM half can be built.
- EVAL-012 remains the gate for exercising the callback against live
  OpenClaw; the contract is buildable and testable fixture-first with a
  simulated executor.
