# EVAL-012 OpenClaw Integration Smoke Run Note

Date: approved 2026-07-17, execution in progress
Status: hard stop lifted; staged execution authorized
Related plan: `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`

## Gate State

The integration hard stop was explicitly lifted by Mitchell on 2026-07-17 in
the working Claude Code session: "Let's get this fully tested with OpenClaw...
discover the issues and get this thing on a loop tonight." Execution is
authorized in the isolated `glasshouse` WSL distro only — a fresh environment
with no private memory stores, no production OpenClaw config, and no access to
the operator's live transcripts. The operator's primary OpenClaw installation
is out of scope and must not be touched.

## Required Before Execution

| Field | Value |
| --- | --- |
| Approval source | Mitchell, in-session instruction (Claude Code, Engram working session) |
| Approval timestamp | 2026-07-17 |
| Caller path | OpenClaw 2026.7.1 in isolated glasshouse WSL distro, calling the memorycore MCP server over stdio |
| Backend mode | staged: fixture-only first run, then live-local (jsonl_store + isolated glasshouse qmd test collection); no private stores exist in glasshouse |
| Entrypoint | `MEMORYCORE_MCP_AUDIT_LOG=/tmp/eval012-audit.jsonl /home/lumen/openreflect-local-memorycore-engram/.venv/bin/python -m memorycore.mcp_server --transport stdio` |
| Audit file path | `/tmp/eval012-audit.jsonl` inside glasshouse (temporary, outside any repo) |
| Cleanup action | delete temporary audit/provenance artifacts in glasshouse /tmp after recording results; glasshouse .memorycore stores are isolated synthetic evidence and never committed |
| Stop-condition reviewer | Alice (Claude) first per prepared defaults; Mitchell if approval scope or private-content risk changes |

All required fields are filled; execution may proceed under the smoke plan's
stop conditions.

## Alice-Preparable Defaults

These values can be prepared before Mitchell lifts the hard stop. They are not
approval to run EVAL-012, and they do not change the missing fields above.

| Field | Prepared default | Why this is safe before approval |
| --- | --- | --- |
| Caller path | local MCP wrapper | Matches the preferred first caller path in the smoke plan and avoids OpenClaw gateway mutation. |
| Backend mode | fixture-only | Keeps the smoke away from live QMD, live Lossless-Claw, Burrow, and private memory stores. |
| Entrypoint | `MEMORYCORE_MCP_AUDIT_LOG=<tmp-jsonl> python3 -m memorycore.mcp_server --transport stdio` | Uses the existing MCP server entrypoint; the exact temp audit path still must be chosen at run time. |
| Audit file path | temporary local-only JSONL outside committed fixtures | Prevents accidental retention of smoke artifacts until cleanup or isolation is inspected. |
| Cleanup action | delete temporary audit/provenance artifacts unless explicitly retained as synthetic evidence | Preserves the public/private boundary and keeps the repo from carrying unreviewed smoke output. |
| Stop-condition reviewer | Alice first, Mitchell only if approval scope or private-content risk changes | Lets Alice stop the smoke on documented safety conditions without turning every normal observation into a Mitchell decision. |

The only Mitchell-only field is the approval source/timestamp lifting the current
integration hard stop, unless he chooses a different caller path or backend mode.

## Approval-Time Fill Order

When the hard stop is lifted, fill the required fields in this order before any
command starts:

1. Record the approval source and timestamp.
2. Copy or revise the selected caller path and backend mode from the prepared
   defaults above.
3. Choose the exact temporary audit file path.
4. Confirm the entrypoint command with that audit path inserted.
5. Confirm cleanup action and stop-condition reviewer.

If approval changes the caller path, backend mode, or artifact handling, re-check
the stop conditions in the smoke plan before starting.

## Intended First Run Shape

The preferred first caller path is the local MCP wrapper in fixture-only mode,
unless Mitchell explicitly selects another path.

The smallest approved call set should be:

1. `memorycore_health`
2. `memorycore_search` against public fixtures
3. `memorycore_verify` against a mock-supported pointer
4. one structured failure, such as unsupported QMD verify

## Commands Not To Run During Prep

These commands remain out of scope until the hard stop is explicitly lifted and
all required pre-execution fields are filled:

- `python3 -m memorycore.cli eval --public-safe`
- any command that starts OpenClaw, Burrow, or the OpenClaw gateway
- any live QMD or live Lossless-Claw adapter invocation
- any smoke command that writes audit/provenance artifacts without a recorded
  temporary path and cleanup decision

Prep work may continue by editing plans, fixtures, contracts, and run notes.

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
