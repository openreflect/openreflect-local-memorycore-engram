# Implementation Plan: Skills-Compatible MemoryCore MVP

## Overview

This plan adapts the existing MemoryCore MVP docs and eval scaffolding to the
installed agent-skills workflow. The goal is not more ceremony. The goal is to
make the repo easy for agents to operate incrementally: one spec, one plan, one
task list, one public-safe eval command, and clear gates before live-backend or
OpenClaw integration work.

## Architecture Decisions

- Keep `SPEC.md` as the skill-compatible entrypoint and preserve the richer
  product/eval docs under `docs/`.
- Treat existing `scripts/validate_*` files as the current test authority.
- Add a consolidated public-safe eval command before live-backend work.
- Keep fixture-only behavior visibly separate from live QMD, live Lossless-Claw,
  and OpenClaw smoke behavior.
- Do not introduce dependencies until a specific eval or packaging problem
  requires one.

## Task List

### Phase 1: Skill Workflow Surface

#### Task 1: Add canonical spec and task surfaces

**Description:** Add `SPEC.md`, `tasks/plan.md`, and `tasks/todo.md` so the
installed spec/planning/build skills can find the project requirements and
implementation state without guessing from arbitrary docs.

**Acceptance criteria:**

- [x] `SPEC.md` covers objective, commands, project structure, code style,
      testing strategy, boundaries, success criteria, and open questions.
- [x] `tasks/plan.md` defines dependency-ordered phases.
- [x] `tasks/todo.md` tracks the actionable task list.

**Verification:**

- [x] `test -f SPEC.md`
- [x] `test -f tasks/plan.md`
- [x] `test -f tasks/todo.md`

**Dependencies:** None.

**Files likely touched:**

- `SPEC.md`
- `tasks/plan.md`
- `tasks/todo.md`

**Estimated scope:** Small.

#### Task 2: Add a consolidated public-safe eval command

**Description:** Add one entrypoint that runs the existing public-safe validation
scripts and reports pass/fail/skipped status in a machine-readable shape.

**Acceptance criteria:**

- [x] `python3 -m memorycore.cli eval --public-safe` runs all current public-safe
      eval scripts.
- [x] Output includes passed eval ids, failed eval ids, skipped local-only eval
      ids, backend availability, fixture corpus status, and audit/provenance
      record count fields.
- [x] Existing individual validation scripts still pass.

**Verification:**

- [x] `python3 -m memorycore.cli eval --public-safe`
- [x] Existing README validation command sequence passes.

**Dependencies:** Task 1.

**Files likely touched:**

- `memorycore/cli.py`
- optional `memorycore/eval.py`
- `README.md`
- `SPEC.md`

**Estimated scope:** Medium.

### Checkpoint: Workflow Surface

- [x] Canonical spec/task files exist.
- [x] Public-safe eval suite has one command.
- [x] Repo remains public-safe.

### Phase 2: Real Backend Readiness

#### Task 3: Define QMD live adapter boundary

**Description:** Specify the first live QMD adapter path, including whether it
uses the existing local index or an isolated fixture collection.

**Acceptance criteria:**

- [x] QMD live mode is explicitly fixture-indexed or local-indexed.
- [x] The result contract remains identical to fixture mode.
- [x] Failure modes distinguish missing source, stale pointer, unavailable QMD,
      and unsupported verification.

**Verification:**

- [x] A local-only QMD plan or eval note exists.
- [x] Public-safe evals still pass.

**Dependencies:** Task 2.

**Files likely touched:**

- `docs/MVP_EVAL_PLAN.md`
- `memorycore/qmd_adapter.py`
- `scripts/validate_mvp_qmd_adapter.py` or a new local-only eval script

**Estimated scope:** Medium.

#### Task 4: Define Lossless-Claw live adapter boundary

**Description:** Specify the first LCM adapter path without committing private
transcript content or requiring public evals to depend on private conversation
ids.

**Acceptance criteria:**

- [x] LCM live mode is explicitly synthetic-store, mock-only, or local-only.
- [x] The result contract remains identical to fixture mode.
- [x] Unsupported verification does not overclaim freshness.

**Verification:**

- [x] A local-only LCM plan or eval note exists.
- [x] Public-safe evals still pass.

**Dependencies:** Task 2.

**Files likely touched:**

- `docs/MVP_EVAL_PLAN.md`
- `memorycore/lcm_adapter.py`
- `scripts/validate_mvp_lcm_adapter.py` or a new local-only eval script

**Estimated scope:** Medium.

### Phase 3: Agent Client Surface

#### Task 5: Prepare MCP server/tool handoff

**Description:** Move from MCP-shaped function contracts toward the selected
runtime surface while keeping fixture-only and live modes distinguishable.

**Acceptance criteria:**

- [x] Tool descriptors remain stable.
- [x] MCP results match CLI normalized shape.
- [x] Audit records remain content-sparse.
- [x] A real MCP server entrypoint can expose the MVP tools when the MCP SDK is available.

**Verification:**

- [x] `python3 scripts/validate_mvp_mcp_surface.py`
- [x] `python3 scripts/validate_mcp_server_entrypoint.py`
- [x] `python3 -m memorycore.cli eval --public-safe`

**Dependencies:** Task 2.

**Files likely touched:**

- `memorycore/mcp_surface.py`
- `scripts/validate_mvp_mcp_surface.py`
- docs for runtime invocation

**Estimated scope:** Medium.

#### Task 6: Scaffold discipline artifacts

**Description:** Add thin public-safe scaffold docs for context loading,
contracts, source evidence, risks, review, threat model, observability, runbook,
performance, migration, ADRs, and CI.

**Acceptance criteria:**

- [x] Agent context, API, source, risk, review, threat model, observability,
      runbook, performance, migration, ADR, and CI artifacts exist.
- [x] Artifacts are explicitly marked as scaffolds rather than completed review
      or hardening work.
- [x] CI runs the consolidated public-safe eval command.

**Verification:**

- [x] `test -f docs/API_CONTRACT.md && test -f docs/THREAT_MODEL.md && test -f .github/workflows/ci.yml`
- [x] `python3 -m memorycore.cli eval --public-safe`

**Dependencies:** Task 2.

**Files touched:**

- `docs/AGENT_CONTEXT.md`
- `docs/API_CONTRACT.md`
- `docs/SOURCES.md`
- `docs/RISK_REGISTER.md`
- `docs/reviews/REVIEW-2026-06-19.md`
- `docs/THREAT_MODEL.md`
- `docs/OBSERVABILITY.md`
- `docs/RUNBOOK.md`
- `docs/PERFORMANCE_BASELINE.md`
- `docs/MIGRATION_PLAN.md`
- `docs/adr/`
- `.github/workflows/ci.yml`

**Estimated scope:** Completed scaffold.

#### Task 7: Execute EVAL-012 only after hard-stop lift

**Description:** Run the first OpenClaw integration smoke only after the
documented preconditions are satisfied and recorded.

**Acceptance criteria:**

- [x] Pre-execution checklist exists as a template and does not claim execution.
- [x] Proposed first caller path is local MCP wrapper unless blocked or
      explicitly overridden.
- [x] Cleanup rules for temporary smoke artifacts are documented.
- [ ] Approval source and timestamp are recorded.
- [ ] Caller path, backend mode, entrypoint, audit file, cleanup action, and
      stop-condition reviewer are recorded before execution.
- [ ] OpenClaw caller can inspect backend id, pointer metadata, verification
      state, and audit id.
- [ ] No private snippets/content/citations/summaries/transcript text persist in
      audit records.

**Verification:**

- [ ] Completed EVAL-012 run note in `docs/` or another agreed location.
- [ ] Public-safe evals still pass after smoke artifacts are cleaned or isolated.

**Dependencies:** Tasks 2, 5, and 6; explicit hard-stop lift.

**Files likely touched:**

- `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`
- EVAL-012 run note
- selected integration shim, if approved

**Estimated scope:** Medium.

### Phase 4: MVP Assembly

#### Task 8: End-to-end public-safe golden path

**Description:** Assemble EVAL-013 so CLI, MCP, and the selected OpenClaw smoke
path prove the same minimal successful and failed request loop.

**Acceptance criteria:**

- [x] Golden-path acceptance criteria are drafted.
- [x] CLI can search/get/verify/audit in the public-safe fixture path.
- [x] MCP-shaped calls can search/get/verify/health in the public-safe fixture path.
- [ ] OpenClaw can perform at least search or verify.
- [x] One successful and one failed request are both inspectable in
      audit/provenance from public-safe CLI and MCP-shaped caller paths.
- [x] Failed request loop exposes stable error status, category, and code.
- [x] Cleanup or isolation of golden-path artifacts is recorded.
- [x] Public-safe evals require no private content.

**Verification:**

- [x] `python3 -m memorycore.cli eval --public-safe`
- [x] `python3 scripts/validate_e2e_golden_path.py`

**Dependencies:** Tasks 3, 4, 5, and 6 for the public-safe CLI/MCP path;
completed approved EVAL-012 remains required for the OpenClaw leg.

**Files likely touched:**

- `scripts/`
- `docs/MVP_EVAL_PLAN.md`
- runtime/client surface modules

**Estimated scope:** Large; split before implementation.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Fixture success is mistaken for live-backend success | High | Label fixture mode everywhere and keep live evals separate. |
| Private memory leaks into public repo audit/provenance files | High | Keep audit/provenance content-sparse and test for private result fields. |
| OpenClaw smoke mutates runtime config too early | High | Honor the EVAL-012 hard stop and require pre-execution checklist completion. |
| Skills process adds ceremony without velocity | Medium | Keep task files short, executable, and tied to existing evals. |
| Adding dependencies bloats the public skeleton | Medium | Prefer standard library until a concrete test or packaging need appears. |

## Open Questions

- Should the first live QMD test use the existing QMD index or an isolated
  fixture collection?
- Which OpenClaw caller path should EVAL-012 use first?
- Should public-safe evals remain custom scripts only, or also be exposed through
  `pytest`?
