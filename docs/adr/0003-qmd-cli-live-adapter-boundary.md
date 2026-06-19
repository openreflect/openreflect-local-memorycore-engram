# ADR 0003: QMD CLI Live Adapter Boundary

Status: proposed.

## Context

QMD is an existing local memory/search backend with its own command surface.

## Decision

MemoryCore should call QMD through a narrow, allowlisted live adapter and
normalize output into the MemoryCore result contract.

## Consequences

- QMD remains the data plane.
- MemoryCore owns routing, normalization, provenance, and verification framing.
- Subprocess safety and timeout behavior must be defined before live mode.

