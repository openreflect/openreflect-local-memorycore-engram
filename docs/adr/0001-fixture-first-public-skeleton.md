# ADR 0001: Fixture-First Public Skeleton

Status: proposed.

## Context

MemoryCore needs public-safe proof before private/live backend integration.

## Decision

Build fixture-first evals and contracts before live adapters.

## Consequences

- Public review can happen without private transcript exports.
- Live readiness must be explicitly separated from fixture confidence.

