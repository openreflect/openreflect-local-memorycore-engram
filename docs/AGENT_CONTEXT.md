# Agent Context

Status: scaffold.

This file is the first-load map for agents working on MemoryCore.

## Load Order

1. `SPEC.md`
2. `tasks/plan.md`
3. `tasks/todo.md`
4. `docs/MVP_EVAL_PLAN.md`
5. `docs/LIVE_BACKEND_BOUNDARIES.md`
6. `docs/API_CONTRACT.md`
7. `docs/THREAT_MODEL.md`

## Current Verification Command

```bash
python3 -m memorycore.cli eval --public-safe
```

## Working Rules

- Keep public artifacts fixture-only and content-sparse unless a task explicitly
  says otherwise.
- Do not run EVAL-012 until the hard stop in
  `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md` is lifted and recorded.
- Treat QMD and Lossless-Claw live paths as local-only until their boundaries
  have executable tests.
- Prefer small vertical slices with an eval before expanding scope.

## Key Runtime Modules

- `memorycore/registry_router.py` owns backend selection and normalized routing.
- `memorycore/qmd_adapter.py` normalizes QMD-shaped fixture responses.
- `memorycore/lcm_adapter.py` normalizes Lossless-Claw-shaped fixture responses.
- `memorycore/provenance_ledger.py` records pointer/provenance metadata.
- `memorycore/audit_log.py` records content-sparse audit events.
- `memorycore/mcp_surface.py` exposes MCP-shaped local calls.
- `memorycore/cli.py` exposes the current operator surface.

