# REPORT-05 - Remaining Work And Roadmap Assessment

Packet: `ASSESS-05-remaining-work-roadmap`
Eval ID: `MEMORYCORE_ASSESS_REMAINING_WORK_ROADMAP`
Date: 2026-06-19
Mode: read-only assessment
Status: complete
[SFV: VERIFIED] Source-contact methods are listed below.

## Executive Summary

MemoryCore is close to a credible MVP skeleton, but not yet a fully claimable MVP.

The current repo has a strong public-safe contract/eval base: registry/router,
QMD and Lossless-Claw fixture adapters, provenance ledger, verification state,
audit log, CLI, MCP-shaped surface, contract-security validation, MCP server
entrypoint, package metadata, and a public-safe CLI/MCP golden path. The
consolidated public-safe eval passed with 14 evals and no failures.

The remaining MVP work is concentrated in three places:

1. The OpenClaw integration smoke (`EVAL-012`) is still gated and unrun.
2. The full golden path is still incomplete until the OpenClaw leg is approved
   and executed.
3. Live backend readiness is split: QMD has a local public-fixture collection
   path documented, and LCM has a synthetic host-bridge eval path, but both are
   intentionally skipped by the public-safe runner and should not be overclaimed
   as general live production readiness.

Bottom line: the shortest credible MVP path is not more broad implementation.
It is controlled acceptance: reconcile stale docs, run/record the already
planned local-only checks where appropriate, obtain explicit EVAL-012 approval,
execute a fixture-only OpenClaw smoke through the selected caller path, then
rerun public-safe evals and update the MVP verdict.

## Files Inspected

- `tasks/assessment-packets/ASSESS-05-remaining-work-roadmap.md`
- `tasks/todo.md`
- `tasks/plan.md`
- `docs/ROADMAP.md`
- `docs/MVP_SCOPE.md`
- `docs/MVP_EVAL_PLAN.md`
- `docs/LIVE_BACKEND_BOUNDARIES.md`
- `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`
- `tasks/agent-packets/README.md`
- `docs/reviews/REVIEW-2026-06-19.md`
- `docs/reviews/REVIEW-2026-06-19-regression.md`
- `README.md`
- `pyproject.toml`
- `memorycore/eval.py`
- `docs/SOURCES.md`
- `docs/RUNBOOK.md`
- `docs/RISK_REGISTER.md`

## Commands Run

```bash
git status --short
```

Result: clean before report writing.

```bash
python3 -m memorycore.cli eval --public-safe
```

Result: `status: ok`; 14 passed eval ids; no failed eval ids; skipped local-only
eval ids were `MEMORYCORE_QMD_LIVE_BACKEND`,
`MEMORYCORE_LCM_LIVE_BACKEND`, and `MEMORYCORE_OPENCLAW_SMOKE`. Backend
availability reported `qmd: fixture-only`, `lossless_claw: fixture-only`, and
`openclaw: not-run-hard-stop`. Audit/provenance record counts were both 0.

```bash
python3 scripts/validate_mcp_server_entrypoint.py
python3 scripts/validate_e2e_golden_path.py
python3 scripts/validate_mvp_contract_security.py
```

Results:

- `MEMORYCORE_MCP_SERVER_ENTRYPOINT_OK`
- `MEMORYCORE_E2E_GOLDEN_PATH_OK`
- `MEMORYCORE_CONTRACT_SECURITY_OK`

No live OpenClaw smoke, live Lossless-Claw store call, QMD collection creation,
gateway mutation, or implementation mutation was performed.

## Evidence Baseline

The MVP is defined as the smallest control plane proving source-backed context
routing over real memory backends, with real routing, real provenance pointers,
real verification checks, real client access, and clear failure behavior
(`docs/MVP_SCOPE.md:8-19`). The stated MVP thesis asks whether MemoryCore can
select an appropriate backend, retrieve source-backed context, explain source,
verify freshness, and expose the result through an agent-usable interface
(`docs/MVP_SCOPE.md:24-35`).

The formal MVP success definition requires the same loop from CLI, MCP, and
OpenClaw (`docs/MVP_SCOPE.md:404-416`). That is the key reason the current repo
cannot honestly be called complete MVP while OpenClaw remains gated.

The roadmap frames v0.1 as a control-plane foundation whose goal is to prove the
pointer/provenance/routing model over real backends (`docs/ROADMAP.md:188-205`).
It also explicitly excludes broad SaaS substrates, replacement memory database
behavior, reasoning engine behavior, agent framework behavior, and broad tool or
model routing from v0.1 (`docs/ROADMAP.md:206-214`).

The eval plan states that real backend evals are required before the MVP can be
called functional, while mock evals are allowed for fast contract checks or
unavailable backends (`docs/MVP_EVAL_PLAN.md:14-21`). The same document says
EVAL-012 has not been executed while the OpenClaw/Burrow integration hard stop
remains active (`docs/MVP_EVAL_PLAN.md:553-563`) and that individual pieces may
work while the MVP is not yet functional if EVAL-013 is incomplete
(`docs/MVP_EVAL_PLAN.md:592-633`).

## Complete Now

### Complete For Public-Safe Contract/Eval Baseline

These are complete enough to count as current public-safe implementation
strength, based on task state and command verification:

- Canonical spec/task surfaces are complete (`tasks/todo.md:3-7`;
  `tasks/plan.md:26-53`).
- Consolidated public-safe eval command is complete and currently passes
  (`tasks/todo.md:9-15`; command result above).
- QMD live adapter boundary is marked complete in task state
  (`tasks/todo.md:17-21`), and QMD source-contact notes now describe an
  isolated public fixture collection path (`docs/SOURCES.md:46-75`).
- Lossless-Claw live adapter boundary is marked complete in task state
  (`tasks/todo.md:23-27`), with host-injected bridge assumptions and synthetic
  local-only validation constraints recorded (`docs/SOURCES.md:88-111`;
  `docs/RUNBOOK.md:104-114`).
- MCP server/tool handoff is marked complete in task state, including a real MCP
  server entrypoint (`tasks/todo.md:29-34`), and
  `validate_mcp_server_entrypoint.py` passed in this assessment.
- Second-wave packet integration is marked complete, covering QMD public fixture
  collection path, real MCP server entrypoint, public-safe golden path, package
  install path, and regression review without running OpenClaw smoke
  (`tasks/todo.md:55-62`).
- Scaffold discipline artifacts exist and are marked complete
  (`tasks/todo.md:64-73`; `tasks/plan.md:177-213`).
- Contract/security review found no critical issue in the public-safe fixture
  path and records that content-sparse audit/provenance constraints are covered
  (`docs/reviews/REVIEW-2026-06-19.md:52-68`).
- Regression review findings were resolved for MCP argument validation, LCM
  optional `None` fields, and live-local error category/schema drift
  (`docs/reviews/REVIEW-2026-06-19-regression.md:113-118`,
  `docs/reviews/REVIEW-2026-06-19-regression.md:148-150`,
  `docs/reviews/REVIEW-2026-06-19-regression.md:173-175`).

### Complete For Public-Safe Golden Path Subset

The CLI/MCP fixture-only golden path is complete and executable. The smoke plan
states that EVAL-013 is executable for the CLI/MCP fixture-only subset through
`scripts/validate_e2e_golden_path.py` (`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:154-193`),
and that script passed in this assessment.

This does not complete the full MVP, because the OpenClaw caller leg remains
gated by EVAL-012 (`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:161-188`).

## Remaining For MVP

### Required MVP Remaining Work

1. Reconcile current state versus stale planning docs before giving operators a
   final MVP checklist.

   Evidence: `tasks/todo.md` has newer state showing Task 5 and Task 5d complete
   (`tasks/todo.md:29-62`), while some older planning/boundary language still
   says current implementation is fixture-only (`docs/LIVE_BACKEND_BOUNDARIES.md:13-26`).

2. Decide and record the EVAL-012 approval source/timestamp.

   Evidence: Task 7 remains incomplete specifically because approval source,
   caller path, backend mode, entrypoint, audit file, cleanup action, and
   stop-condition reviewer still need to be recorded before execution
   (`tasks/todo.md:75-82`; `tasks/plan.md:215-247`).

3. Execute EVAL-012 fixture-only through the selected OpenClaw caller path.

   Evidence: the smoke plan says the first smoke should answer whether an
   OpenClaw caller can invoke search or verify and receive structured output with
   backend id, pointer metadata, verification state, and audit id
   (`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:16-24`). Current status remains
   `MEMORYCORE_OPENCLAW_SMOKE` as `not-run-by-design`
   (`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:26-33`).

4. Complete the OpenClaw leg of the golden path after EVAL-012.

   Evidence: Task 8 says the CLI/MCP success/failure loop now passes but the
   OpenClaw leg remains blocked until approved EVAL-012 completion
   (`tasks/todo.md:84-92`). `docs/MVP_SCOPE.md` requires CLI, MCP, and OpenClaw
   use of the same loop for MVP success (`docs/MVP_SCOPE.md:404-416`).

5. Re-run the public-safe eval after smoke cleanup/isolation.

   Evidence: the smoke cleanup rules explicitly require rerunning
   `python3 -m memorycore.cli eval --public-safe` after cleanup or isolation
   (`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:141-152`; `docs/RUNBOOK.md:122-130`).

### Necessary But Not Blocking MVP If Clearly Labeled

- Local-only QMD live validation should be retained as a local acceptance lane,
  not folded into public-safe evals. The public runner must continue to skip it
  (`memorycore/eval.py:42-46`; `docs/SOURCES.md:66-75`).
- Synthetic/local-only LCM validation should remain separate unless a separate
  approval names a live host tool path (`docs/RUNBOOK.md:104-114`).
- Package install should remain a supporting release surface, not a blocker if
  module command remains the canonical compatibility path. README states the
  direct module command remains canonical for agents/scripts
  (`README.md:115-131`), while `pyproject.toml` provides a console script
  (`pyproject.toml:5-17`).

## Blocked Items

### Explicit Approval Blocker

- `MEMORYCORE_OPENCLAW_SMOKE` / EVAL-012 is blocked on explicit hard-stop lift
  and recorded pre-execution fields. The smoke plan says not to start if any
  pre-execution item is unknown (`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:71-84`).

### Integration Blocker

- Full EVAL-013 is blocked on EVAL-012 completion. The current public-safe
  validator represents OpenClaw as gated/not-run-by-design, not passed
  (`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:154-193`;
  `memorycore/eval.py:42-46`).

### Environment/Local State Blockers

- General live QMD readiness depends on explicit safe collection selection or
  existing public-safe fixture collection state. The source doc records exact
  live-local needs: public-safe/synthetic collection, indexed deterministic
  phrase, and a resolvable pointer verified through `qmd get`
  (`docs/SOURCES.md:37-45`).
- General live LCM readiness depends on host-injected tool functions and avoids
  committed private transcript IDs (`docs/SOURCES.md:96-111`).

### Design/Scope Blockers

- No broad backend control, mirroring, splitting, backup/migration, SaaS
  substrates, visualization, insight plugins, or REST/Pinecone-style interface
  should be allowed to delay v0.1. Roadmap marks most of those as later or
  explicitly out of v0.1 (`docs/ROADMAP.md:27-86`, `docs/ROADMAP.md:112-184`,
  `docs/ROADMAP.md:215-260`).

## Post-MVP / Optional Work

The following should be excluded from MVP completion criteria unless the MVP
definition changes:

- Hermes, Codex, ChatGPT, Claude app/plugin paths
  (`docs/MVP_SCOPE.md:318-335`).
- REST API beyond local need, Pinecone-style compatibility, broad third-party
  SaaS substrates, Notion/Drive/Excel/S3/NFS/CIFS adapters
  (`docs/MVP_SCOPE.md:318-335`; `docs/ROADMAP.md:112-163`).
- Backup/migration execution (`docs/MVP_SCOPE.md:318-335`;
  `docs/ROADMAP.md:165-184`).
- Mirroring and splitting policies (`docs/MVP_SCOPE.md:318-335`;
  `docs/ROADMAP.md:27-56`).
- Insight plugins and derived observations (`docs/MVP_SCOPE.md:318-335`;
  `docs/ROADMAP.md:215-241`).
- Context visualization and cost/token diagnostics (`docs/MVP_SCOPE.md:318-335`;
  `docs/ROADMAP.md:243-260`).
- Replacement database, reasoning engine, agent framework, sandbox, or owned
  message/summary/embedding store (`docs/ROADMAP.md:206-214`;
  `docs/MVP_SCOPE.md:318-335`).

## Stale Task/Doc Observations

These are observations only. This report did not edit task or doc files.

1. `docs/LIVE_BACKEND_BOUNDARIES.md` appears stale in its "Current Fixture
   Boundary" section. It says the current implementation is fixture-only and
   lists fixture-only adapters/CLI/MCP (`docs/LIVE_BACKEND_BOUNDARIES.md:13-26`),
   but later repo state and task files show live-local QMD support, host-injected
   LCM boundary, MCP server entrypoint, public-safe E2E, and packaging work have
   advanced (`tasks/todo.md:55-62`; `docs/SOURCES.md:46-86`;
   `docs/RUNBOOK.md:104-114`).

2. `README.md` current status still calls the project "staged as a public
   skeleton" (`README.md:105-113`). That remains partly fair, but it underplays
   the now-integrated MCP server entrypoint, package metadata, and public-safe
   E2E golden path visible in task/eval state.

3. `docs/MVP_EVAL_PLAN.md` still describes the MCP surface section as not
   starting an MCP server (`docs/MVP_EVAL_PLAN.md:505-516`), while Packet 07 and
   current validation show a real server entrypoint now exists and passes
   (`tasks/agent-packets/README.md:47-50`; command result above).

4. `docs/LIVE_BACKEND_BOUNDARIES.md` recommends
   `python3 scripts/validate_local_qmd_adapter.py --collection fixtures`
   (`docs/LIVE_BACKEND_BOUNDARIES.md:91-100`), but `docs/SOURCES.md` now records
   that the newer safe collection is `memorycore-public-fixtures`
   (`docs/SOURCES.md:46-64`).

5. `docs/RUNBOOK.md` has the same older local QMD command using
   `--collection fixtures` (`docs/RUNBOOK.md:41-67`). It also instructs not to
   create/reindex just to force the eval, which is good operational caution, but
   should be reconciled with the Packet 06 public fixture collection helper
   (`docs/SOURCES.md:46-64`).

## Shortest Credible MVP Completion Path

1. Freeze implementation and reconcile state.

   Produce one coordinator-owned state update that aligns `docs/LIVE_BACKEND_BOUNDARIES.md`,
   `docs/MVP_EVAL_PLAN.md`, `docs/RUNBOOK.md`, and `README.md` with the post
   second-wave state. Do not add new feature scope.

2. Run named non-OpenClaw local-only checks only if the environment is already
   prepared and public-safe.

   Candidate checks:

   - `python3 scripts/validate_local_lcm_adapter.py --synthetic`
   - `python3 scripts/validate_local_qmd_adapter.py --collection memorycore-public-fixtures`

   Do not create or mutate QMD/OpenClaw state during this step unless explicitly
   assigned. If local fixture state is absent, record `blocked` rather than
   forcing it.

3. Ask for or record explicit EVAL-012 approval.

   Required fields are approval source/timestamp, caller path, backend mode,
   entrypoint, audit path, cleanup action, and stop-condition reviewer
   (`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:71-84`).

4. Execute EVAL-012 fixture-only through the local MCP wrapper unless explicitly
   overridden.

   This matches the proposed first caller path in the smoke plan
   (`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:34-47`) and avoids gateway/runtime
   mutation.

5. Inspect and clean/isolate smoke artifacts.

   Confirm no snippets, content, citations, summaries, transcript text, account
   ids, or private runtime paths persist (`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:86-115`;
   `docs/RUNBOOK.md:122-132`).

6. Re-run `python3 -m memorycore.cli eval --public-safe`.

   The MVP can then be called a minimal functional kernel only if public-safe
   evals remain green and the OpenClaw run note shows search or verify succeeded
   with backend id, pointer metadata, verification state, and audit id.

## Highest-Leverage Next Actions

1. Create a coordinator-owned "MVP readiness ledger" that reconciles complete,
   blocked, and post-MVP items without changing implementation.
2. Update stale docs to match the current actual state, especially QMD collection
   name, MCP server entrypoint, and live-boundary wording.
3. Prepare the EVAL-012 run note with all required fields but do not run it until
   approval is explicit.
4. Run EVAL-012 fixture-only through local MCP wrapper once approved.
5. After EVAL-012, run public-safe eval, then produce the MVP completion verdict.

## What Would Be Irresponsible To Claim Today

- "The MVP is complete." The MVP success definition still requires OpenClaw in
  the same loop as CLI and MCP (`docs/MVP_SCOPE.md:404-416`), and OpenClaw smoke
  remains not-run-by-design (`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:26-33`).
- "MemoryCore has proven live production QMD and LCM backends." The public-safe
  runner reports QMD and LCM as fixture-only and skips live backend evals
  (`memorycore/eval.py:42-64`; command result above).
- "OpenClaw integration works." EVAL-012 is a prep template and has not run
  (`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:26-33`).
- "MemoryCore is a full memory fabric." Roadmap explicitly places broad
  nontraditional substrates and fabric-like behavior later than v0.1
  (`docs/ROADMAP.md:130-184`).
- "MemoryCore replaces LCM, QMD, or OpenClaw's context engine." MVP scope and
  roadmap explicitly exclude replacement database/context-engine behavior
  (`docs/MVP_SCOPE.md:162-168`, `docs/MVP_SCOPE.md:286-290`,
  `docs/ROADMAP.md:206-214`).

## Remaining-Work Estimate

This is an assessment estimate, not a schedule commitment.

- Public-safe implementation/eval skeleton: approximately 85-90% of the MVP
  support surface.
- Full MVP claim: approximately 65-75%, because the highest-value remaining
  proof is integration, not scaffolding.
- Remaining engineering effort before MVP verdict: small to medium if EVAL-012
  uses fixture-only local MCP wrapper and no gateway mutation.
- Remaining operational risk: medium, because stale docs and fixture/live
  overclaiming can mislead downstream agents even when code is passing.

## Confidence

Confidence: medium-high.

Reasons:

- High confidence in public-safe eval status because the consolidated eval and
  focused validators were run during this assessment.
- High confidence that OpenClaw smoke is the central MVP blocker because multiple
  primary docs independently state it remains gated/unrun.
- Medium confidence on local QMD/LCM live-local status because I did not run live
  local QMD collection validation or LCM synthetic validation in this read-only
  assessment. I relied on current docs/task state and avoided local state
  mutation as instructed.
- Medium confidence on stale-doc classification because the repo changed rapidly
  through packet integration; the cited contradictions should be reviewed by the
  coordinator before any docs are updated.

## Final Verdict

MemoryCore is not far from MVP, but the final distance is qualitative: it needs
one controlled OpenClaw caller proof, not another broad implementation wave.

The shortest credible path is: reconcile stale docs, preserve the passing
public-safe eval suite, record EVAL-012 approval fields, run fixture-only
OpenClaw smoke through the selected local MCP path, clean/isolate artifacts,
rerun public-safe evals, and then issue the MVP readiness verdict.
