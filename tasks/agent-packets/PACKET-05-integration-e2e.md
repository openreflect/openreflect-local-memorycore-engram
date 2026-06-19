# Packet 05: Gated OpenClaw Smoke And E2E Golden Path

Owner role: integration planning agent.

## Mission

Prepare EVAL-012 and EVAL-013 artifacts so integration can proceed later, while
respecting the current hard stop. This packet must not execute OpenClaw smoke.

## Context To Load

- `SPEC.md`
- `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`
- `docs/MIGRATION_PLAN.md`
- `docs/RUNBOOK.md`
- `docs/LIVE_BACKEND_BOUNDARIES.md`
- `tasks/plan.md`
- `tasks/todo.md`

## Primary Write Scope

- `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`
- new run-note template if needed under `docs/`
- `docs/MIGRATION_PLAN.md`
- `docs/RUNBOOK.md`
- `tasks/plan.md`
- `tasks/todo.md`

Do not edit:

- live QMD adapter implementation
- live LCM adapter implementation
- MCP tool implementation unless coordinating a documented dependency

## Deliverables

1. Confirm the EVAL-012 hard-stop checklist is complete as a template but not
   executed.
2. Draft EVAL-013 golden-path acceptance criteria for successful and failed
   request loops.
3. Specify cleanup rules for smoke artifacts.
4. Identify which caller path should be proposed first: local MCP wrapper,
   plugin shim, or another named runtime path.
5. Update planner docs only if the packet changes task order or dependencies.

## Acceptance Criteria

- No OpenClaw runtime config is mutated.
- No EVAL-012 run note claims execution.
- Public-safe eval still passes.
- EVAL-013 can be implemented later without private content.

## Verification

```bash
python3 -m memorycore.cli eval --public-safe
```

Do not run:

```bash
# EVAL-012 smoke remains blocked until explicit approval.
```

## Result Format

Return:

- changed files
- smoke/e2e readiness state
- exact verification commands and results
- explicit statement that EVAL-012 was not run

