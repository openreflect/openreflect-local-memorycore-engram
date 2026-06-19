# Packet 03: MCP Server And Tool Handoff

Owner role: agent-client surface agent.

## Mission

Move the current MCP-shaped function contract toward a real MCP handoff plan
without breaking CLI/MCP normalized equivalence.

## Context To Load

- `SPEC.md`
- `docs/API_CONTRACT.md`
- `docs/AGENT_CONTEXT.md`
- `memorycore/mcp_surface.py`
- `memorycore/cli.py`
- `scripts/validate_mvp_mcp_surface.py`
- `fixtures/mcp/`

## Primary Write Scope

- `memorycore/mcp_surface.py`
- `scripts/validate_mvp_mcp_surface.py`
- `docs/API_CONTRACT.md`
- `docs/RUNBOOK.md`
- optional new doc: `docs/MCP_HANDOFF.md`

Do not edit:

- QMD live adapter internals
- LCM host bridge internals
- EVAL-012 run note execution status

## Deliverables

1. Specify the MCP tool descriptors for search, get, verify, and health.
2. Prove MCP-shaped calls return the same normalized core result fields as CLI.
3. Document any transport wrapper differences.
4. Keep audit/provenance content-sparse.
5. Identify what is still missing before a real MCP server entrypoint exists.

## End Eval

Named end eval: `MEMORYCORE_MCP_SURFACE`.

Executable target:

```bash
python3 scripts/validate_mvp_mcp_surface.py
```

The end eval passes when:

- search, get, verify, and health tool descriptors are stable;
- MCP-shaped calls normalize to the same core result shape as CLI requests;
- transport wrapper differences are documented;
- no audit/provenance path persists private snippets by default;
- the consolidated public-safe eval includes and passes this eval.

## Acceptance Criteria

- `validate_mvp_mcp_surface.py` passes.
- `python3 -m memorycore.cli eval --public-safe` passes.
- CLI/MCP divergence is documented and limited to wrapper details.
- Tool descriptors are stable enough for agents to call without guessing.

## Verification

```bash
python3 scripts/validate_mvp_mcp_surface.py
python3 -m memorycore.cli eval --public-safe
```

## Result Format

Return:

- changed files
- end eval name and status
- MCP tools and argument shapes
- exact verification commands and results
- remaining handoff gaps
