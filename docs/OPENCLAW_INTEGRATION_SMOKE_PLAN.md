# OpenClaw Integration Smoke Plan

Date: 2026-06-18
Status: Draft, not executed
Related eval: EVAL-012

## Purpose

Define the first OpenClaw integration smoke before running it.

This is a prep artifact only. It does not start an MCP server, mutate a
gateway, call live QMD, call Lossless-Claw, run Burrow runtime tests, run
OpenClaw integration tests, or execute the public-safe eval runner.

## Smoke Boundary

The first smoke should answer one narrow question:

Can an OpenClaw caller invoke a MemoryCore search or verify operation and
receive structured output with backend id, pointer metadata, verification
state, and audit id?

The smoke is not a full MVP validation and is not an end-to-end golden path.

## Preconditions

- Mitchell is present or has explicitly lifted the current integration hard
  stop.
- The MemoryCore repo is clean enough to distinguish smoke artifacts from prior
  changes.
- The caller path is selected before execution:
  - local MCP tool wrapper,
  - OpenClaw plugin shim,
  - or another explicitly named OpenClaw runtime path.
- The backend mode is fixture-only unless a separate live-backend decision is
  made.
- Audit output is written to a temporary or clearly named local file.

## Initial Fixture-Only Calls

Use the smallest call set that proves the surface:

1. `memorycore_health`
2. `memorycore_search` with the public fixture corpus
3. `memorycore_verify` against a mock-supported pointer
4. one structured failure, such as unsupported QMD verify

## Required Observations

For each successful routed call, capture:

- caller path,
- operation,
- selected backend id,
- pointer id or empty result reason,
- verification state,
- audit id,
- audit file path,
- whether private snippets, content, citations, summaries, or transcript text
  were absent from persisted audit records.

For the failure call, capture:

- stable error code,
- stable error category,
- visible failure status at the OpenClaw caller boundary.

## Stop Conditions

Stop the smoke immediately if:

- the caller path needs live gateway mutation that was not explicitly approved,
- private memory content would be persisted into the public repo,
- a runtime test suite is about to run instead of a single smoke call,
- the output cannot distinguish fixture mode from live backend mode,
- audit records include raw snippets, content, citations, summaries, or
  transcript text.

## Expected Result Shape

The OpenClaw caller should be able to inspect:

```json
{
  "status": "ok",
  "selected_backend": "qmd",
  "results": [
    {
      "pointer": {
        "backend_id": "qmd",
        "pointer_id": "fixtures/corpus/project-alpha.md"
      },
      "verification_state": "verified"
    }
  ],
  "audit_id": "audit_example"
}
```

The exact pointer can differ by selected fixture. The structural fields should
not.
