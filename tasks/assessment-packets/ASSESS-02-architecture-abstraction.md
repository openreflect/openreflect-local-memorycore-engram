# ASSESS-02 - Architecture And Abstraction

## Purpose

Assess whether the current architecture genuinely supports memory
virtualization: one stable memory contract across different backend systems,
with routing, normalization, provenance, verification, and safe client access.

## Ownership

- Write only: `tasks/assessment-reports/REPORT-02-architecture-abstraction.md`
- Read: architecture docs, contracts, code, schemas, adapters, CLI/MCP surfaces.
- Do not touch: implementation, docs, schemas, evals, fixtures, task state,
  existing packets, git config, package files, CI.

## Context To Load

- `docs/ARCHITECTURE.md`
- `docs/API_CONTRACT.md`
- `docs/LIVE_BACKEND_BOUNDARIES.md`
- `docs/MCP_HANDOFF.md`
- `docs/MVP_SCOPE.md`
- `memorycore/registry_router.py`
- `memorycore/qmd_adapter.py`
- `memorycore/lcm_adapter.py`
- `memorycore/mcp_surface.py`
- `memorycore/mcp_server.py`
- `memorycore/cli.py`
- `schemas/`

## Research Questions

- What is the actual architectural boundary of MemoryCore?
- Does the code implement a memory abstraction layer or mostly a wrapper around
  fixtures/tools?
- How well are backend-specific details hidden behind shared request/result
  contracts?
- Does routing behave as policy infrastructure instead of model improvisation?
- Are provenance and verification first-class architectural concepts?
- Is MCP only an interface, or is the product accidentally collapsing into
  "MCP for memory tools"?
- What architectural pieces are missing before the abstraction can be called
  functional over real backends?

## Constraints

- Read-only assessment only.
- You may run validation commands if they do not mutate repo state.
- Treat generated local indexes, caches, and live smoke as out of scope unless
  already present and documented.
- Do not run EVAL-012 or any OpenClaw smoke.

## End Eval

- Eval ID: `MEMORYCORE_ASSESS_ARCHITECTURE_ABSTRACTION`
- Command: not executable; report review by coordinator.
- Passing condition: the report maps architecture claims to concrete files and
  identifies whether the abstraction is conceptual, fixture-proven,
  locally-proven, or live-integrated.
- Correct blocked condition: if architecture cannot be assessed without live
  smoke, state exactly why and what evidence is missing.

## Reporting Contract

Return:

- report path written,
- files inspected,
- commands run,
- architecture readiness judgment,
- abstraction gaps,
- contradictions or design risks,
- confidence level.
