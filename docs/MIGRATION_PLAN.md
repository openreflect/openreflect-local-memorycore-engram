# Migration Plan

Status: scaffold.

## Migration Path

1. Fixture-only public skeleton
2. Local-only live QMD adapter
3. Local-only Lossless-Claw adapter
4. MCP server/tool handoff
5. Gated OpenClaw integration smoke
6. End-to-end public-safe golden path

## OpenClaw Caller Path Recommendation

For EVAL-012, propose the local MCP wrapper first. It keeps the first OpenClaw
smoke close to the MCP-shaped MemoryCore contract, supports fixture-only
execution, and should not require OpenClaw gateway/runtime configuration
mutation.

Escalate to an OpenClaw plugin shim only if the local MCP wrapper is blocked or
Mitchell explicitly selects that path.

## Compatibility Rules

- Prefer additive contract changes.
- Keep fixture mode working while live mode is introduced.
- Keep CLI and MCP outputs equivalent.
- Do not remove fields without updating schemas, fixtures, evals, and docs.

## Rollback Rules

- Live adapter failures must fall back to structured unavailable/degraded states.
- Public-safe evals must stay runnable without live backends.
- EVAL-012 artifacts must be removable without damaging fixture mode.
- EVAL-013 must still pass the public-safe eval route after smoke/golden-path
  artifacts are cleaned or isolated.

## EVAL Gates

- `MEMORYCORE_OPENCLAW_SMOKE`: `not-run-by-design` until the EVAL-012 hard stop
  is explicitly lifted and the run note records approval, caller path, backend
  mode, entrypoint, audit path, cleanup action, and reviewer.
- `MEMORYCORE_E2E_GOLDEN_PATH`: `not-run-by-design` until EVAL-012 has an
  approved public-safe result and CLI, MCP, and the selected OpenClaw path can
  prove matching successful and failed request loops.
