# PACKET-07 - Real MCP Server Entrypoint

## Purpose

Turn the current MCP-shaped in-process surface into a real server entrypoint that an MCP-capable client can launch, while preserving the existing CLI/MCP normalized result contract.

## Ownership

- Primary files/modules: `memorycore/mcp_server.py` or equivalent MCP server entrypoint, MCP server validator.
- Supporting docs/scripts: `docs/MCP_HANDOFF.md`, `docs/API_CONTRACT.md`, `docs/RUNBOOK.md`, optional `scripts/validate_mcp_server_entrypoint.py`.
- Do not touch: QMD/LCM adapter semantics, OpenClaw smoke execution, packaging metadata unless absolutely required and coordinated with Packet 09.

## Context To Load

- `SPEC.md`
- `docs/MCP_HANDOFF.md`
- `docs/API_CONTRACT.md`
- `tasks/agent-packets/PACKET-03-mcp-handoff.md`
- `memorycore/mcp_surface.py`
- `scripts/validate_mvp_mcp_surface.py`

## Work Items

- Select the smallest MCP server entrypoint strategy available without unnecessary dependencies.
- Implement or scaffold a launchable server wrapper around the existing `memorycore.mcp_surface` descriptors and `call_tool` path.
- Add a validator that proves the server entrypoint can expose the expected tools or correctly reports dependency-blocked status.
- Document launch command, transport assumptions, error serialization, and remaining real-client gaps.

## Constraints

- Preserve existing `MEMORYCORE_MCP_SURFACE` behavior.
- Keep CLI/MCP normalized equivalence; wrapper-only fields may differ, result semantics may not.
- Do not make live QMD, live Lossless-Claw, Burrow, OpenClaw, or private memory calls.
- You are not alone in the codebase; do not revert or overwrite parallel packet work.

## End Eval

- Eval ID: `MEMORYCORE_MCP_SERVER_ENTRYPOINT`
- Command: preferred `python3 scripts/validate_mcp_server_entrypoint.py`; also run `python3 scripts/validate_mvp_mcp_surface.py`.
- Passing condition: server entrypoint is importable/launchable enough to expose the four MVP tools and preserve the existing MCP surface contract.
- Correct blocked/skipped condition: blocked with exact missing MCP server library, transport choice, or packaging dependency reason while `MEMORYCORE_MCP_SURFACE` still passes.

## Reporting Contract

Return:

- changed files
- server launch/import path
- eval command and result
- selected dependency strategy
- blockers
- assumptions
- remaining gaps
