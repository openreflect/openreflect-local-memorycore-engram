# EVAL-012 OpenClaw Integration Smoke Run Note

Date: not run
Status: not-run-by-design
Related plan: `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`

## Gate State

EVAL-012 has not been approved or executed.

The current hard stop remains active. Do not run Burrow runtime tests, OpenClaw
integration tests, live OpenClaw gateway calls, or the public-safe eval runner
as part of this note.

## Required Before Execution

| Field | Value |
| --- | --- |
| Approval source | missing |
| Approval timestamp | missing |
| Caller path | missing |
| Backend mode | missing |
| Entrypoint | missing |
| Audit file path | missing |
| Cleanup action | missing |
| Stop-condition reviewer | missing |

If any field remains `missing`, the smoke must not start.

## Intended First Run Shape

The preferred first caller path is the local MCP wrapper in fixture-only mode,
unless Mitchell explicitly selects another path.

The smallest approved call set should be:

1. `memorycore_health`
2. `memorycore_search` against public fixtures
3. `memorycore_verify` against a mock-supported pointer
4. one structured failure, such as unsupported QMD verify

## Calls

| Call | Status | Selected backend | Pointer or reason | Verification state | Audit id |
| --- | --- | --- | --- | --- | --- |
| `memorycore_health` | not run | n/a | n/a | n/a | n/a |
| `memorycore_search` | not run | n/a | n/a | n/a | n/a |
| `memorycore_verify` | not run | n/a | n/a | n/a | n/a |
| structured failure | not run | n/a | n/a | n/a | n/a |

## Artifact Handling

No smoke artifacts exist from this note.

Before any future run, choose whether artifacts are temporary or retained as
public-safe synthetic evidence. After the run, record the cleanup or isolation
result here before making any MVP completion claim.

## Completion Criteria

EVAL-012 can be marked complete only when:

- the hard stop has been explicitly lifted,
- every required pre-execution field above is filled,
- the call table records observed results,
- audit/provenance artifacts are cleaned or isolated,
- no private snippets, content, citations, summaries, or transcript text are
  persisted,
- and `python3 -m memorycore.cli eval --public-safe` is green after cleanup or
  artifact isolation.
