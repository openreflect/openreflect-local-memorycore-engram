# Migration Plan

Status: scaffold.

## Migration Path

1. Fixture-only public skeleton
2. Local-only live QMD adapter
3. Local-only Lossless-Claw adapter
4. MCP server/tool handoff
5. Gated OpenClaw integration smoke
6. End-to-end public-safe golden path

## Compatibility Rules

- Prefer additive contract changes.
- Keep fixture mode working while live mode is introduced.
- Keep CLI and MCP outputs equivalent.
- Do not remove fields without updating schemas, fixtures, evals, and docs.

## Rollback Rules

- Live adapter failures must fall back to structured unavailable/degraded states.
- Public-safe evals must stay runnable without live backends.
- EVAL-012 artifacts must be removable without damaging fixture mode.

