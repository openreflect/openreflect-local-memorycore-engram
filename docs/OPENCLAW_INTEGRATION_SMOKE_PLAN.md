# OpenClaw Integration Smoke Plan

Date: 2026-06-18
Status: Draft, not executed
Related eval: EVAL-012
End eval: MEMORYCORE_OPENCLAW_SMOKE

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

## Current Eval Status

`MEMORYCORE_OPENCLAW_SMOKE` is `not-run-by-design`.

This document is a complete pre-execution template for EVAL-012, not evidence
that EVAL-012 has run. The hard stop remains active until an approval source and
timestamp are recorded in an actual run note.

## Proposed First Caller Path

Use a local MCP wrapper first.

Rationale:

- It exercises the same MCP-shaped MemoryCore surface planned for agent clients.
- It can remain fixture-only and local without OpenClaw gateway mutation.
- It avoids committing to an OpenClaw plugin packaging shape before the MCP
  contract and public-safe eval route are stable.

Do not start with an OpenClaw plugin shim unless the local MCP wrapper path is
blocked or Mitchell explicitly selects the plugin path.

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

## Pre-Execution Checklist

Before any smoke run starts, record these choices in the run note:

- approval source and timestamp lifting the current integration hard stop,
- caller path selected from the allowed options above,
- fixture-only or live-backend mode,
- exact command or tool entrypoint to be invoked,
- audit file path,
- expected cleanup action for temporary files,
- stop-condition reviewer.

If any item is unknown, do not start the smoke. Update this plan or ask for the
missing decision instead.

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

## Cleanup Rules

- Write smoke audit/provenance output to a temporary or clearly named local-only
  path recorded in the run note.
- Do not commit smoke audit/provenance files unless they are synthetic,
  content-sparse, and intentionally retained as public-safe evidence.
- If smoke artifacts are retained, isolate them under an approved docs or
  fixtures path and record why they are public-safe.
- If smoke artifacts are temporary, delete them after the run and record cleanup
  completion in the run note.
- Re-run `python3 -m memorycore.cli eval --public-safe` after cleanup or
  isolation.

## EVAL-013 Golden-Path Planning

Related eval: EVAL-013
End eval: MEMORYCORE_E2E_GOLDEN_PATH
Current public-safe status: executable for the CLI/MCP fixture-only subset via
`python3 scripts/validate_e2e_golden_path.py`.

The OpenClaw caller leg of EVAL-013 must not run until EVAL-012 has an
approved, completed, public-safe run note and the public-safe eval route is
green.

The public-safe golden path proves the same request loops through CLI and
MCP-shaped calls now, while representing the OpenClaw caller path as gated and
not-run-by-design:

1. Successful request loop
   - health or route availability is inspectable;
   - a public-safe search or verify request returns `status: ok`;
   - the selected backend id is visible;
   - pointer metadata is visible without private content persistence;
   - verification state is visible;
   - audit id and provenance pointer are inspectable from the CLI/MCP caller
     boundary.
2. Failed request loop
   - one intentionally unsupported or missing-pointer request returns a stable
     failure status;
   - the error category and code are visible at each caller boundary;
   - audit/provenance output records the failure without snippets, content,
     citations, summaries, or transcript text;
   - cleanup or isolation leaves public-safe evals passing.
3. OpenClaw gate
   - EVAL-012 remains `not-run-by-design` until the documented hard stop is
     lifted;
   - no OpenClaw runtime configuration, gateway, Burrow runtime test, or
     integration smoke is executed by the public-safe EVAL-013 validator.

The current EVAL-013 artifact is
`scripts/validate_e2e_golden_path.py`. It records temporary audit/provenance
files, validates CLI/MCP success and failure loops, deletes temporary artifacts
at process exit, and leaves the OpenClaw caller path gated.

## Run Note Template

Use this template when the smoke is actually approved and run:

```markdown
# EVAL-012 OpenClaw Integration Smoke Run

Date:
Approval source:
Caller path:
Backend mode:
Entrypoint:
Audit file:

## Calls

| Call | Status | Selected backend | Pointer or reason | Verification state | Audit id |
| --- | --- | --- | --- | --- | --- |
| `memorycore_health` | | | | | |
| `memorycore_search` | | | | | |
| `memorycore_verify` | | | | | |
| structured failure | | | | | |

## Boundary Check

- Private snippets/content/citations/summaries/transcript text persisted: yes/no
- Fixture mode distinguishable from live mode: yes/no
- Cleanup completed: yes/no

## Verdict

Pass/fail:
Reason:
Next action:
```
