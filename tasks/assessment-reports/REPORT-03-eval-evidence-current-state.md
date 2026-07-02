# REPORT-03 - Eval Evidence And Current State

Date: 2026-06-19
Agent: Agent 03
Packet: `tasks/assessment-packets/ASSESS-03-eval-evidence-current-state.md`
Scope: read-only eval evidence/current-state assessment
Status: `[SFV: VERIFIED]` for commands and file evidence listed below

## Executive Verdict

The public-safe eval surface is green, broad, and useful, but it currently proves
contract correctness over fixture/mock/synthetic paths, not full MVP operation
over real production memory backends.

Current eval state:

- Public-safe consolidated eval: passing.
- Public-safe passed eval IDs: 14.
- Public-safe failed eval IDs: 0.
- Public-safe backend mode: QMD fixture-only, Lossless-Claw fixture-only,
  OpenClaw not-run-hard-stop.
- Local-only LCM synthetic eval: passing.
- MCP server entrypoint eval: passing.
- OpenClaw/EVAL-012 smoke: not run by design.
- Live QMD local eval: not run by this assessment lane because it would depend
  on an existing local collection and this packet forbids creating/recreating
  QMD indexes.

The strongest proven claim is: MemoryCore has a working public-safe contract and
fixture-based control-plane skeleton covering schema packets, routing, adapter
normalization, provenance/audit sparsity, CLI, MCP-shaped calls, contract
security, and a CLI/MCP fixture-only golden path.

The strongest unproven MVP claim is: MemoryCore is not yet proven as a complete
functional MVP over real QMD, real Lossless-Claw, and an approved OpenClaw caller
path. The project docs themselves define the MVP as requiring real backends and
an end-to-end QMD/Lossless-Claw/OpenClaw/MCP loop.

## Commands Run

All commands were run from:

`~/workbench/openreflect/openreflect-local-memorycore-engram`

### Consolidated Public-Safe Eval

Command:

```bash
python3 -m memorycore.cli eval --public-safe
```

Observed result:

- `status`: `ok`
- `mode`: `public-safe`
- `failed_eval_ids`: `[]`
- `audit_records_created`: `0`
- `provenance_records_created`: `0`
- `fixture_corpus_status.status`: `present`
- `fixture_corpus_status.file_count`: `3`
- `backend_availability.qmd`: `fixture-only`
- `backend_availability.lossless_claw`: `fixture-only`
- `backend_availability.openclaw`: `not-run-hard-stop`

Passed eval IDs:

- `ENGRAM_MEMORY_RECORD`
- `MEMORYCORE_PACKET_A`
- `MEMORYCORE_PACKET_B`
- `MEMORYCORE_PACKET_C`
- `MEMORYCORE_ROUTER`
- `MEMORYCORE_QMD_ADAPTER`
- `MEMORYCORE_LCM_ADAPTER`
- `MEMORYCORE_PROVENANCE_LEDGER`
- `MEMORYCORE_VERIFICATION_STATE`
- `MEMORYCORE_AUDIT_LOG`
- `MEMORYCORE_CLI`
- `MEMORYCORE_MCP_SURFACE`
- `MEMORYCORE_CONTRACT_SECURITY`
- `MEMORYCORE_E2E_GOLDEN_PATH`

Skipped local-only eval IDs:

- `MEMORYCORE_QMD_LIVE_BACKEND`
- `MEMORYCORE_LCM_LIVE_BACKEND`
- `MEMORYCORE_OPENCLAW_SMOKE`

### Additional Read-Only Checks

Command:

```bash
python3 scripts/validate_local_lcm_adapter.py --synthetic
```

Observed result:

- `MEMORYCORE_LCM_LIVE_BACKEND_OK`

Interpretation: the host-injected LCM adapter boundary passes a synthetic
local-only bridge eval. This is useful evidence for adapter behavior, but it is
not evidence of a real private Lossless-Claw transcript store or live OpenClaw
tool bridge.

Command:

```bash
python3 scripts/validate_mcp_server_entrypoint.py
```

Observed result:

- `MEMORYCORE_MCP_SERVER_ENTRYPOINT_OK`

Interpretation: the real MCP server entrypoint/import/check path is currently
valid. This is separate from the public-safe MCP-shaped surface eval and does
not prove a real external MCP client integration or OpenClaw caller path.

Command:

```bash
python3 scripts/validate_e2e_golden_path.py
```

Observed result:

- `MEMORYCORE_E2E_GOLDEN_PATH_OK`

Interpretation: the EVAL-013 public-safe CLI/MCP fixture subset passes. It
explicitly keeps the OpenClaw caller leg gated.

Command:

```bash
git status --short
```

Observed result before writing this report:

- no output

Interpretation: the worktree was clean before this report was written.

## Source Evidence

### Public-Safe Runner Boundaries

`memorycore/eval.py` states that the public-safe runner "does not call live QMD,
Lossless-Claw, Burrow, OpenClaw, or any private runtime" (lines 1-5).

The public-safe eval list contains 14 eval IDs (lines 25-39), exactly matching
the command result above.

The same runner defines three local-only skipped IDs (lines 42-46):

- `MEMORYCORE_QMD_LIVE_BACKEND`
- `MEMORYCORE_LCM_LIVE_BACKEND`
- `MEMORYCORE_OPENCLAW_SMOKE`

The runner reports backend availability as fixture-only for QMD and
Lossless-Claw, and `not-run-hard-stop` for OpenClaw (lines 60-64).

### MVP Requires Real Backend Proof

`docs/MVP_EVAL_PLAN.md` says real backend evals are required before the MVP can
be called functional (lines 14-21).

`docs/MVP_SCOPE.md` defines the MVP as a control plane proving source-backed
context routing over real memory backends (lines 6-19), and says the MVP
succeeds if QMD, Lossless-Claw, OpenClaw, and MCP prove the loop end to end
(lines 24-35).

### QMD Proof Boundary

`docs/MVP_EVAL_PLAN.md` says the public-safe QMD scaffold uses static
QMD-shaped fixtures and verifies adapter preservation without calling a live QMD
index (lines 219-226). It also says failure to prove real backend local corpus
recall means MemoryCore cannot prove local corpus recall through a real backend
(lines 247-264).

`docs/LIVE_BACKEND_BOUNDARIES.md` says fixture success proves contract stability
and does not prove live backend functionality (current fixture boundary section,
lines 15-25 from the inspected file). It also says the first live QMD path
should be local-only and skipped by the public-safe eval runner.

### Lossless-Claw Proof Boundary

`docs/MVP_EVAL_PLAN.md` says the public-safe Lossless-Claw scaffold uses static
LCM-shaped fixtures and validates without calling live lossless-claw tools or a
transcript store (lines 268-277). The local-only synthetic validator passed in
this assessment, but it still uses synthetic in-memory data only.

### MCP Proof Boundary

`docs/MVP_EVAL_PLAN.md` says the MCP-shaped public-safe surface is checked
against static QMD, LCM, mock backend, and temporary audit fixtures only; it
does not start an MCP server or call live QMD, Lossless-Claw, Burrow, OpenClaw,
or the public-safe eval runner (lines 507-516).

The separate MCP server entrypoint validator passed in this assessment. That
improves current-state confidence that a server entrypoint exists, but the
public-safe eval itself still proves a fixture-mode surface, not an external
client deployment.

### OpenClaw Proof Boundary

`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md` is marked "Draft, not executed"
(lines 1-6). It says the artifact is prep only and does not start an MCP
server, mutate a gateway, call live QMD, call Lossless-Claw, run Burrow runtime
tests, run OpenClaw integration tests, or execute the public-safe eval runner
(lines 8-15).

The same document says `MEMORYCORE_OPENCLAW_SMOKE` is `not-run-by-design`, and
the hard stop remains active until an approval source and timestamp are recorded
in a run note (lines 26-32). Its pre-execution checklist requires approval
source/timestamp, caller path, backend mode, entrypoint, audit path, cleanup
action, and stop-condition reviewer before any smoke run (lines 71-84).

### EVAL-013 Boundary

`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md` says the current EVAL-013 public-safe
status is executable only for the CLI/MCP fixture subset (lines 154-159). It
also says the OpenClaw caller leg must not run until EVAL-012 has an approved,
completed, public-safe run note and the public-safe eval route is green (lines
161-163).

`docs/MVP_EVAL_PLAN.md` says the current EVAL-013 validator runs the
fixture-only CLI/MCP subset and represents the OpenClaw caller leg as
`not-run-by-design` (lines 592-602).

### Task-State Evidence

`tasks/todo.md` marks the public-safe eval command complete (lines 9-15), QMD
and LCM live adapter boundaries complete as boundaries (lines 17-27), MCP
handoff complete (lines 29-34), and second-wave packet outputs integrated
without running OpenClaw smoke (lines 55-62).

`tasks/todo.md` leaves Task 7, EVAL-012 execution, open and explicitly blocked
on hard-stop lift and recorded preconditions (lines 75-82).

`tasks/todo.md` leaves Task 8, the full end-to-end public-safe golden path,
open because the OpenClaw leg remains blocked until approved EVAL-012
completion (lines 84-92).

## Eval Classification

### Public-Safe Fixture/Contract Evals Passing

These are proven by `python3 -m memorycore.cli eval --public-safe`:

- `ENGRAM_MEMORY_RECORD`: memory record example/schema check.
- `MEMORYCORE_PACKET_A`: schema/public fixture packet checks.
- `MEMORYCORE_PACKET_B`: registry/router/backend packet checks.
- `MEMORYCORE_PACKET_C`: error model packet checks.
- `MEMORYCORE_ROUTER`: deterministic fixture/mock routing.
- `MEMORYCORE_QMD_ADAPTER`: QMD fixture adapter normalization.
- `MEMORYCORE_LCM_ADAPTER`: LCM fixture adapter normalization.
- `MEMORYCORE_PROVENANCE_LEDGER`: temporary public-safe ledger behavior.
- `MEMORYCORE_VERIFICATION_STATE`: shared verification state contract.
- `MEMORYCORE_AUDIT_LOG`: temporary public-safe audit behavior.
- `MEMORYCORE_CLI`: fixture-mode CLI behavior.
- `MEMORYCORE_MCP_SURFACE`: fixture-mode MCP-shaped local contract behavior.
- `MEMORYCORE_CONTRACT_SECURITY`: schema/security/content-sparse checks.
- `MEMORYCORE_E2E_GOLDEN_PATH`: CLI/MCP fixture success/failure loop with
  OpenClaw represented as gated.

### Local-Only Evals

- `MEMORYCORE_LCM_LIVE_BACKEND`: passed in this assessment via
  `python3 scripts/validate_local_lcm_adapter.py --synthetic`. Classification:
  local-only synthetic host bridge proof, not live private transcript proof.
- `MEMORYCORE_QMD_LIVE_BACKEND`: not run in this assessment. Classification:
  local-only live QMD proof exists as a validator surface, but this lane did not
  execute it because it requires an explicitly supplied existing collection and
  the packet forbids creating/recreating QMD indexes.

### Gated/Not-Run-By-Design

- `MEMORYCORE_OPENCLAW_SMOKE`: not run by design. The hard stop is still active
  until an approval source/timestamp and smoke run note are recorded.
- OpenClaw leg of `MEMORYCORE_E2E_GOLDEN_PATH`: not run by design. The CLI/MCP
  fixture subset passes; OpenClaw remains gated on EVAL-012.

## What The Public-Safe Suite Proves

The public-safe suite proves:

- The consolidated eval command works and reports pass/fail/skipped/backend
  fixture status in machine-readable JSON.
- The normalized request/result/error contracts are covered by deterministic
  scripts.
- QMD-shaped fixture results normalize into the shared result/error contract.
- Lossless-Claw-shaped fixture results normalize into the shared result/error
  contract.
- Deterministic routing works against fixture/mock backends.
- Verification states are normalized and avoid overclaiming obvious missing,
  unsupported, timeout, and unknown cases.
- Audit and provenance records can be written/read in temporary public-safe
  form without persisting raw snippets/content/citations/summaries/transcript
  text.
- CLI fixture-mode operations pass.
- MCP-shaped fixture-mode operations pass.
- A real MCP server entrypoint check passes as a separate read-only validator.
- The EVAL-013 CLI/MCP fixture golden path passes for successful and failed
  loops.

## What The Public-Safe Suite Does Not Prove

The public-safe suite does not prove:

- Live QMD search/get/verify works against the operator's actual QMD index.
- Live QMD freshness semantics are sufficient beyond pointer resolution.
- Live Lossless-Claw tool calls work against a real transcript/summary store.
- Lossless-Claw recall can be verified beyond synthetic host bridge behavior.
- OpenClaw can invoke MemoryCore through an approved caller path.
- OpenClaw receives backend id, pointer metadata, verification state, and audit
  id at its actual caller boundary.
- EVAL-012 has been run.
- The complete MVP success definition is satisfied across CLI, MCP, and
  OpenClaw.
- The system is ready to claim production-quality memory virtualization over
  arbitrary backends.

## Unproven MVP Claims

These claims should not be made without additional evidence:

1. "The MVP is functional over real memory backends."
   - Not yet proven. The docs require real backend evals before the MVP can be
     called functional.

2. "MemoryCore can route real file memory through QMD end to end."
   - Partially prepared, but not proven by the public-safe suite. This requires
     `MEMORYCORE_QMD_LIVE_BACKEND` against an approved existing public-safe or
     synthetic QMD collection.

3. "MemoryCore can route real conversation continuity through Lossless-Claw end
   to end."
   - Partially prepared. Synthetic host bridge passed, but a real host-injected
     Lossless-Claw path over an approved isolated/private-safe data source is
     not proven here.

4. "OpenClaw can use MemoryCore."
   - Not proven. EVAL-012 remains hard-gated and unrun.

5. "The full golden path is complete."
   - Not fully. The CLI/MCP fixture subset passes, but the OpenClaw caller leg
     remains gated.

6. "MemoryCore is a complete memory virtualization product."
   - Too strong. The current evidence supports a contract/control-plane
     skeleton and fixture-mode MVP path, not full multi-backend product
     maturity.

## Evidence Needed To Call The MVP Functional

Minimum additional evidence:

1. Run `MEMORYCORE_QMD_LIVE_BACKEND` against an approved existing public-safe or
   synthetic QMD collection without creating private index leakage.
2. Run a real or isolated host-injected Lossless-Claw eval that proves search,
   get/describe, missing pointer, unavailable path, timeout, and verification
   behavior without committing private transcript content.
3. Lift the EVAL-012 hard stop explicitly and record a run note with approval
   source/timestamp, caller path, backend mode, entrypoint, audit file, cleanup
   action, and stop-condition reviewer.
4. Run the approved fixture-only OpenClaw smoke and confirm the caller can
   inspect selected backend id, pointer metadata, verification state, audit id,
   and structured failure state.
5. Re-run `python3 -m memorycore.cli eval --public-safe` after any smoke
   cleanup/isolation.
6. Update EVAL-013 evidence so the golden path covers CLI, MCP, and the
   approved OpenClaw caller path, not only CLI/MCP fixture mode.

## Current Confidence

Confidence levels:

- Public-safe fixture eval status: high.
  - Direct command run passed with 14 passing eval IDs and no failures.
- Contract/control-plane skeleton: high.
  - Multiple deterministic validators cover routing, adapters, audit,
    provenance, verification, CLI, MCP-shaped calls, and contract security.
- Local-only synthetic LCM bridge: medium-high.
  - Direct synthetic validator passed, but it is not live transcript-store proof.
- MCP server entrypoint: medium-high.
  - Direct validator passed, but this does not prove deployment/client
    integration.
- Live QMD backend proof: medium-low from this lane.
  - Validator exists, and task state says the fixture collection path was
    integrated, but this assessment did not run it because QMD index creation or
    recreation was out of scope.
- OpenClaw integration proof: low.
  - Documentation is strong, but execution is explicitly not-run-by-design.
- Full MVP functional readiness: medium-low.
  - The public-safe skeleton is close, but the MVP definition requires real
    backends plus OpenClaw/MCP end-to-end proof. The currently open tasks are
    exactly those gates.

## Blockers Or Non-Runs In This Lane

- Did not run EVAL-012/OpenClaw smoke. It is hard-gated and explicitly out of
  scope for this packet.
- Did not run `scripts/create_qmd_fixture_collection.py`. The user explicitly
  forbade creating/recreating QMD indexes.
- Did not run `scripts/validate_local_qmd_adapter.py --collection ...` because
  this assessment did not create/recreate or select a QMD collection. This keeps
  the lane compliant with the packet constraints.
- No implementation, docs, schema, fixture, package, CI, task-state, or packet
  files were modified by this agent.

## Final Assessment

MemoryCore's eval evidence is strong for a public-safe, fixture-first
implementation scaffold. It is not yet sufficient for the stronger MVP claim
that MemoryCore is functional over real backends and OpenClaw.

The correct current-state phrase is:

MemoryCore has a passing public-safe contract/eval skeleton and CLI/MCP
fixture-mode golden path, with local-only backend validation surfaces prepared;
the remaining MVP proof is live QMD, live or isolated Lossless-Claw, and the
approved OpenClaw smoke/golden-path leg.
