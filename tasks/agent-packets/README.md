# Agent Packets

Status: active planning scaffold.

These packets split the next MemoryCore work into five parallel lanes with
explicit ownership boundaries. Agents are not alone in the codebase: each packet
must preserve existing public-safe eval behavior, avoid reverting other lanes,
and coordinate through stable contracts instead of broad rewrites.

## Shared Baseline

Load first:

1. `SPEC.md`
2. `tasks/plan.md`
3. `tasks/todo.md`
4. `docs/AGENT_CONTEXT.md`
5. `docs/LIVE_BACKEND_BOUNDARIES.md`
6. this packet index

Verify before and after any implementation change:

```bash
python3 -m memorycore.cli eval --public-safe
```

Every packet is eval-driven. Each agent must name the packet's end eval in its
final result and state one of:

- `passed`
- `blocked`
- `not-run-by-design`

If the named end eval is not executable yet, the packet's job is to create the
smallest safe artifact that makes the eval executable later without weakening
the public-safe baseline.

## Packets

| Packet | Focus | End Eval | Primary Write Scope | Blocking Rule |
| --- | --- | --- | --- | --- |
| `PACKET-01-qmd-live-local.md` | QMD live-local adapter planning and first local-only eval shape | `MEMORYCORE_QMD_LIVE_BACKEND` | QMD adapter docs/scripts only | Do not touch LCM/MCP/OpenClaw code |
| `PACKET-02-lcm-host-bridge.md` | Lossless-Claw host-injected adapter plan | `MEMORYCORE_LCM_LIVE_BACKEND` | LCM adapter docs/scripts only | Do not import OpenClaw internals |
| `PACKET-03-mcp-handoff.md` | MCP server/tool handoff | `MEMORYCORE_MCP_SURFACE` | MCP surface docs/scripts only | Preserve CLI/MCP normalized equivalence |
| `PACKET-04-contracts-hardening.md` | API/security/observability/contracts | `MEMORYCORE_CONTRACT_SECURITY` | docs/schemas/tests for contracts | Do not change live adapter behavior |
| `PACKET-05-integration-e2e.md` | EVAL-012/EVAL-013 planning and run-note scaffolds | `MEMORYCORE_OPENCLAW_SMOKE` and `MEMORYCORE_E2E_GOLDEN_PATH` | smoke/e2e docs only | Do not run EVAL-012 |
| `PACKET-06-qmd-safe-collection.md` | Safe local QMD fixture collection for the blocked live-local eval | `MEMORYCORE_QMD_LIVE_BACKEND` | QMD fixture collection docs/scripts only | Do not use private memory collections |
| `PACKET-07-real-mcp-server.md` | Real MCP server entrypoint around the existing MCP contract | `MEMORYCORE_MCP_SERVER_ENTRYPOINT` and `MEMORYCORE_MCP_SURFACE` | MCP server module/docs/validator only | Do not change adapter semantics |
| `PACKET-08-public-safe-golden-path.md` | Public-safe CLI/MCP golden path without OpenClaw smoke execution | `MEMORYCORE_E2E_GOLDEN_PATH` | E2E fixtures/docs/validator only | Keep OpenClaw step skipped unless approved |
| `PACKET-09-packaging-install.md` | Fresh-checkout install and packaging path | `MEMORYCORE_PACKAGE_INSTALL` | packaging/CI/README install docs only | Do not introduce runtime deps without need |
| `PACKET-10-regression-review.md` | Independent review of integrated packet work | `MEMORYCORE_REGRESSION_REVIEW` | review docs and optional read-only validator | Do not rewrite implementation as part of review |

## Coordination Rules

- Keep public fixtures public-safe.
- Keep audit/provenance persistence content-sparse.
- Additive changes only unless a packet explicitly owns a breaking change plan.
- If a packet needs another packet's contract, update docs first and call it out
  in the packet result.
- Do not run live QMD, live Lossless-Claw, or OpenClaw smoke from a packet unless
  the packet explicitly says the required approval and local-only mode exist.
- A packet is not complete until its named end eval is passed, or the final
  result explains exactly why the eval is blocked or intentionally not run.
