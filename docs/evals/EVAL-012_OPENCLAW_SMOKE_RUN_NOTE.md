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

## Execution Log (glasshouse campaign, 2026-07-17)

Completed:

- OpenClaw 2026.7.1 and qmd 2.5.3 installed in glasshouse (npm, user prefix).
- `openclaw mcp add memorycore` saved and probed the stdio server
  successfully (transport-level OpenClaw -> MemoryCore connectivity proven).
- Gateway configured (`gateway.mode=local`, synthetic auth token) and running
  as a persistent systemd user service with linger; health ok.
- Live-local leg (step [d]) PASSED in glasshouse: isolated collection
  `memorycore-writes` at `~/.memorycore/corpus`; `memorycore_remember`
  (file_corpus, content) -> `write_mode: live-local`,
  `qmd://memorycore-writes/memory-78b28919b5db5912.md`, `verified`;
  `memorycore_verify` by record_id -> `verified`; live `memorycore_search`
  -> 1 result, `recall_mode: qmd_live_local`.

Discovered:

- `openclaw agent --local` turns require a model auth profile; provider auth
  is an interactive browser OAuth (operator-only). The fixture smoke call set
  below therefore waits on that one operator step.
- `openclaw attach` grants expose OpenClaw's native gateway tools
  (including `memory_get`/`memory_search`) but not `mcp.servers` entries, so
  attach is not a substitute caller path for the agent-driven smoke.
- Gateway start requires `gateway.mode` and `gateway.auth` to be explicitly
  configured; background processes must run under systemd (transient WSL
  sessions kill nohup children).

Executor scaffold (step [e], 2026-07-17): `openclaw plugins init` generated
`/home/lumen/openclaw-plugins/memorycore-executor/` in glasshouse; `src/index.ts`
carries the EN-019 design skeleton — a `memorycore_deliver` tool that will
execute delivery instructions via the native context engine and confirm back
through `memorycore_confirm_delivery`. Ingest is stubbed (EN-022): glasshouse
stock OpenClaw 2026.7.1 does not include lossless-claw; its stock plugin set
does include an unrelated plugin with id `memory-core` (RISK-004 naming
collision). No enforcement paths were created.

Remaining before the call table can fill: one operator step — interactive
model-auth OAuth in glasshouse (`openclaw models auth login` for a provider,
TTY) — then `openclaw agent --local` can drive the four fixture-only calls.

## Calls

Executed 2026-07-17 by the OpenClaw agent (gateway session `main`, model
openai/gpt-5.5, operator OAuth profile) calling the memorycore MCP stdio
server registered in glasshouse `mcp.servers`, fixture-only mode.

| Call | Status | Selected backend | Pointer or reason | Verification state | Audit id |
| --- | --- | --- | --- | --- | --- |
| `memorycore_health` | ok | n/a (health) | n/a | n/a | n/a (health is not audited by design) |
| `memorycore_search` | ok | qmd | fixtures/corpus/project-alpha.md | unknown | audit_11de3620cc061fe5 |
| `memorycore_verify` | ok | mock_healthy | fixtures/corpus/project-alpha.md | verified | audit_01d0f82f5188dc13 |
| structured failure (`verify` on qmd) | error | qmd | VERIFICATION_UNSUPPORTED / verification_unsupported | unsupported | audit_23d175d50dfe5c3b |

The agent-reported results and the server-side audit log
(`/tmp/eval012-audit.jsonl`, 3 records) corroborated exactly; the audit log
contained zero private result fields (snippet/content/citations/summary/
answer/text all absent).

## Artifact Handling

The temporary audit file `/tmp/eval012-audit.jsonl` in glasshouse was
inspected (content-sparse confirmed), its metadata recorded in the call table
above, and then deleted per the approved cleanup action. The glasshouse
`.memorycore` stores remain as isolated synthetic evidence, never committed.

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
