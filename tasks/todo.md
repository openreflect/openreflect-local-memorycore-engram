# MemoryCore MVP Task List

- [x] Task 1: Add canonical spec and task surfaces
  - Acceptance: `SPEC.md`, `tasks/plan.md`, and `tasks/todo.md` exist and map
    the existing MVP docs into the installed skills workflow.
  - Verify: `test -f SPEC.md && test -f tasks/plan.md && test -f tasks/todo.md`
  - Files: `SPEC.md`, `tasks/plan.md`, `tasks/todo.md`

- [x] Task 2: Add a consolidated public-safe eval command
  - Acceptance: `python3 -m memorycore.cli eval --public-safe` runs all current
    public-safe eval scripts and reports passed, failed, skipped, backend,
    fixture, audit, and provenance fields.
  - Verify: `python3 -m memorycore.cli eval --public-safe`
  - Files: `memorycore/cli.py`, optional `memorycore/eval.py`, `README.md`,
    `SPEC.md`

- [x] Task 3: Define QMD live adapter boundary
  - Acceptance: first live QMD mode is explicit, contract-compatible, and
    public/private safe.
  - Verify: public-safe evals pass and local-only QMD boundary is documented.
  - Files: `docs/LIVE_BACKEND_BOUNDARIES.md`, `docs/MVP_EVAL_PLAN.md`

- [x] Task 4: Define Lossless-Claw live adapter boundary
  - Acceptance: first LCM live/synthetic/mock mode is explicit and does not
    overclaim verification.
  - Verify: public-safe evals pass and local-only LCM boundary is documented.
  - Files: `docs/LIVE_BACKEND_BOUNDARIES.md`, `docs/MVP_EVAL_PLAN.md`

- [ ] Task 5: Prepare MCP server/tool handoff
  - Acceptance: MCP-shaped calls keep CLI-compatible normalized results and
    content-sparse audit records.
  - Verify: `python3 scripts/validate_mvp_mcp_surface.py`
  - Files: `memorycore/mcp_surface.py`, MCP eval/docs

- [x] Task 6: Scaffold discipline artifacts
  - Acceptance: context, API, sources, risk, review, threat model,
    observability, runbook, CI, ADR, performance, and migration docs exist as
    thin public-safe starting points.
  - Verify: `test -f docs/API_CONTRACT.md && test -f docs/THREAT_MODEL.md && test -f .github/workflows/ci.yml`
  - Files: `docs/AGENT_CONTEXT.md`, `docs/API_CONTRACT.md`, `docs/SOURCES.md`,
    `docs/RISK_REGISTER.md`, `docs/reviews/REVIEW-2026-06-19.md`,
    `docs/THREAT_MODEL.md`, `docs/OBSERVABILITY.md`, `docs/RUNBOOK.md`,
    `docs/PERFORMANCE_BASELINE.md`, `docs/MIGRATION_PLAN.md`, `docs/adr/`,
    `.github/workflows/ci.yml`

- [ ] Task 7: Execute EVAL-012 only after hard-stop lift
  - Acceptance: approval source, caller path, backend mode, entrypoint, audit
    path, cleanup action, and stop-condition reviewer are recorded before run.
  - Verify: completed EVAL-012 run note and public-safe evals still pass.
  - Files: `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`, run note, approved shim

- [ ] Task 8: End-to-end public-safe golden path
  - Acceptance: CLI, MCP, and approved OpenClaw path prove successful and failed
    request loops with inspectable audit/provenance.
  - Verify: `python3 -m memorycore.cli eval --public-safe` plus EVAL-013 result.
  - Files: scripts, docs, selected runtime/client modules
