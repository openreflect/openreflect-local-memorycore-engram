# MVP Readiness Ledger

Date: 2026-07-14 (originally 2026-06-23)
Status: Evidence ledger; per-item state now also tracked in `docs/REGISTER.md`

This ledger reconciles the current MVP state without changing implementation or
running gated evals. It is a coordination artifact for deciding whether the
MemoryCore MVP is complete, partially complete, blocked, or still outside the
MVP boundary.

## Current Verdict

MemoryCore is a working local control plane with one backend proven live,
not yet a complete OpenClaw MVP.

The implementation proves normalized contracts, routing, verification states,
provenance/audit behavior, CLI/MCP surfaces, and — beyond the original kernel —
a caching memory router (SQLite as provenance anchor), live-local QMD reads,
transient content write-through into a dedicated collection, real
backend-proof verification with stamp updates (all three proven against the
operator's real QMD index), and the ADR-0006 callback delivery contract for
LCM transcript writes validated with a simulated executor.

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
| Caching memory router and cache API | Complete for fixture and live-local QMD | `memorycore/cache_router.py`, `docs/CACHE_API_OPENCLAW.md`, `scripts/validate_mvp_cache_router.py`, `scripts/validate_mvp_cache_api.py` | LCM leg gated on EVAL-012 executor. |
| Live-local QMD reads, write-through, real verify | Proven on operator's real index (2026-07-04/05) | `scripts/validate_mvp_live_mode.py`, `scripts/validate_mvp_write_through.py`, `scripts/validate_mvp_real_verify.py`, `docs/adr/0005-transient-content-write-through.md` | Local proof is not production QMD readiness. |
| LCM callback delivery contract | Complete fixture-first with simulated executor | `docs/adr/0006-lcm-callback-write-transport.md`, `scripts/validate_mvp_callback_delivery.py` | OpenClaw-side executor plugin and describe-verify gated on EVAL-012. |
| Public repo, CI, product register | Complete | github.com/openreflect/openreflect-local-memorycore-engram, `.github/workflows/ci.yml`, `docs/REGISTER.md` | Keep register and docs reconciled per commit. |
| Public-safe golden path | Partial | `scripts/validate_e2e_golden_path.py`, EVAL-013 notes in `docs/MVP_EVAL_PLAN.md` | OpenClaw caller leg remains gated on EVAL-012. |
| OpenClaw integration smoke | Blocked by design | `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`, `docs/evals/EVAL-012_OPENCLAW_SMOKE_RUN_NOTE.md` | Requires explicit hard-stop lift, approval source/timestamp, caller path, backend mode, entrypoint, audit path, cleanup action, and stop-condition reviewer. |
| Final MVP verdict | Blocked | Assessment reports and this ledger | Requires approved EVAL-012 result plus green public-safe eval route afterward. |

## Not MVP Claims Yet

- OpenClaw integration works.
- The MVP is complete.
- Live LCM delivery works (the contract is validated only against a
  simulated executor).
- Local live-QMD proof generalizes to production deployments.
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
