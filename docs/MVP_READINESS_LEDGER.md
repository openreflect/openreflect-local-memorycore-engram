# MVP Readiness Ledger

Date: 2026-06-23
Status: Draft evidence ledger

This ledger reconciles the current MVP state without changing implementation or
running gated evals. It is a coordination artifact for deciding whether the
MemoryCore MVP is complete, partially complete, blocked, or still outside the
MVP boundary.

## Current Verdict

MemoryCore is a credible fixture-first MVP kernel, not a complete OpenClaw MVP.

The implementation currently proves normalized contracts, routing, adapter
fixtures, verification states, provenance/audit behavior, CLI behavior, MCP
surface behavior, local-only backend boundaries, packaging, and public-safe
golden-path scaffolding.

The MVP completion claim remains blocked until EVAL-012 is explicitly approved
and run, and until the public-safe eval route is green after cleanup or artifact
isolation.

## Ledger

| Area | State | Evidence | Remaining Gate |
| --- | --- | --- | --- |
| Product frame and MVP scope | Complete for MVP planning | `docs/MVP_SCOPE.md`, `docs/PRD.md`, `docs/ROADMAP.md`, `SPEC.md` | Keep stale wording reconciled as implementation changes. |
| Request/result/error contracts | Complete for fixture MVP | `schemas/request.schema.json`, `schemas/result.schema.json`, `schemas/error.schema.json`, `fixtures/requests/`, `fixtures/errors/` | None for fixture MVP. |
| Backend registry and router | Complete for fixture MVP | `memorycore/registry_router.py`, `scripts/validate_mvp_router.py` | None for fixture MVP. |
| QMD adapter boundary | Complete for mocked and local-safe boundary | `memorycore/qmd_adapter.py`, `docs/LIVE_BACKEND_BOUNDARIES.md`, `docs/adr/0003-qmd-cli-live-adapter-boundary.md` | Do not treat local fixture readiness as production QMD readiness. |
| Lossless-Claw adapter boundary | Complete for mocked and host-injected boundary | `memorycore/lcm_adapter.py`, `docs/LIVE_BACKEND_BOUNDARIES.md`, `docs/adr/0004-lcm-host-injected-adapter-boundary.md` | Do not persist or publish private transcript content. |
| Verification state model | Complete for fixture MVP | `memorycore/verification_state.py`, `scripts/validate_mvp_verification_state.py` | None for fixture MVP. |
| Audit and provenance | Complete for content-sparse MVP behavior | `memorycore/audit_log.py`, `memorycore/provenance_ledger.py`, `docs/adr/0002-content-sparse-audit-provenance.md` | Inspect retained smoke artifacts after any integration run. |
| CLI surface | Complete for public-safe MVP kernel | `memorycore/cli.py`, `memorycore/eval.py`, `README.md` | Re-run public-safe evals after EVAL-012 cleanup or artifact isolation. |
| MCP surface and server entrypoint | Complete for local public-safe handoff | `memorycore/mcp_surface.py`, `memorycore/mcp_server.py`, `docs/MCP_HANDOFF.md` | EVAL-012 must select the actual OpenClaw caller path before execution. |
| Public-safe golden path | Partial | `scripts/validate_e2e_golden_path.py`, EVAL-013 notes in `docs/MVP_EVAL_PLAN.md` | OpenClaw caller leg remains gated on EVAL-012. |
| OpenClaw integration smoke | Blocked by design | `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`, `docs/evals/EVAL-012_OPENCLAW_SMOKE_RUN_NOTE.md` | Requires explicit hard-stop lift, approval source/timestamp, caller path, backend mode, entrypoint, audit path, cleanup action, and stop-condition reviewer. |
| Final MVP verdict | Blocked | Assessment reports and this ledger | Requires approved EVAL-012 result plus green public-safe eval route afterward. |

## Not MVP Claims Yet

- OpenClaw integration works.
- The MVP is complete.
- Production live QMD and Lossless-Claw backends are proven.
- Public-safe fixture confidence is equivalent to live backend readiness.

## Shortest Remaining Path

1. Keep this ledger and stale task/docs wording reconciled with current code.
2. Prepare the EVAL-012 run note fields, but do not run the smoke until the hard
   stop is explicitly lifted.
3. After approval, run fixture-only EVAL-012 through the selected local caller
   path.
4. Inspect and clean or isolate audit/provenance artifacts.
5. Re-run `python3 -m memorycore.cli eval --public-safe`.
6. Issue the final MVP verdict from observed evidence.
