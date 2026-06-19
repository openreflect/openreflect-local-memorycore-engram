# ADR 0004: Lossless-Claw Host-Injected Adapter Boundary

Status: proposed.

## Context

Lossless-Claw access is host-tool-shaped rather than a standalone public CLI.

## Decision

MemoryCore should treat Lossless-Claw as a host-injected backend boundary with
fixture and local-only modes before any OpenClaw smoke.

## Consequences

- Public evals can model expected behavior without requiring private tools.
- Live verification semantics must remain explicit and conservative.

