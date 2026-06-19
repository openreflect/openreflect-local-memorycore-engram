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

## End Eval

Named end evals:

- `MEMORYCORE_OPENCLAW_SMOKE`
- `MEMORYCORE_E2E_GOLDEN_PATH`

Executable targets:

```bash
# Only after explicit hard-stop lift:
# EVAL-012 command/path to be recorded in the run note.

# After EVAL-012 and public-safe route are ready:
# EVAL-013 command/path to be recorded in the golden-path artifact.
```

The OpenClaw smoke eval passes when:

- approval source and timestamp are recorded before execution;
- caller path, backend mode, entrypoint, audit file, cleanup action, and
  stop-condition reviewer are recorded;
- the caller can inspect backend id, pointer metadata, verification state, and
  audit id;
- no private content persists in audit/provenance records.

The E2E golden-path eval passes when:

- CLI, MCP, and approved OpenClaw path prove the same successful request loop;
- at least one failed request loop is inspectable in audit/provenance output;
- public-safe evals still pass after any smoke artifacts are cleaned or isolated.

Current status: both end evals are `not-run-by-design` until the EVAL-012 hard
stop is explicitly lifted. This packet must not mark either eval passed unless
it actually executes under the documented approval conditions.

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
- end eval names and status
- smoke/e2e readiness state
- exact verification commands and results
- explicit statement that EVAL-012 was not run
