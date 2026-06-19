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

## Packets

| Packet | Focus | Primary Write Scope | Blocking Rule |
| --- | --- | --- | --- |
| `PACKET-01-qmd-live-local.md` | QMD live-local adapter planning and first local-only eval shape | QMD adapter docs/scripts only | Do not touch LCM/MCP/OpenClaw code |
| `PACKET-02-lcm-host-bridge.md` | Lossless-Claw host-injected adapter plan | LCM adapter docs/scripts only | Do not import OpenClaw internals |
| `PACKET-03-mcp-handoff.md` | MCP server/tool handoff | MCP surface docs/scripts only | Preserve CLI/MCP normalized equivalence |
| `PACKET-04-contracts-hardening.md` | API/security/observability/contracts | docs/schemas/tests for contracts | Do not change live adapter behavior |
| `PACKET-05-integration-e2e.md` | EVAL-012/EVAL-013 planning and run-note scaffolds | smoke/e2e docs only | Do not run EVAL-012 |

## Coordination Rules

- Keep public fixtures public-safe.
- Keep audit/provenance persistence content-sparse.
- Additive changes only unless a packet explicitly owns a breaking change plan.
- If a packet needs another packet's contract, update docs first and call it out
  in the packet result.
- Do not run live QMD, live Lossless-Claw, or OpenClaw smoke from a packet unless
  the packet explicitly says the required approval and local-only mode exist.

