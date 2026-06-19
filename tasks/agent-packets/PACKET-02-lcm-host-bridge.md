# Packet 02: Lossless-Claw Host Bridge

Owner role: host-tool adapter agent.

## Mission

Prepare the Lossless-Claw adapter bridge as a host-injected boundary rather than
a public dependency or direct OpenClaw import.

## Context To Load

- `SPEC.md`
- `docs/LIVE_BACKEND_BOUNDARIES.md`
- `docs/SOURCES.md`
- `docs/adr/0004-lcm-host-injected-adapter-boundary.md`
- `memorycore/lcm_adapter.py`
- `scripts/validate_mvp_lcm_adapter.py`
- `fixtures/lcm/`

## Primary Write Scope

- `docs/SOURCES.md`
- `docs/RISK_REGISTER.md`
- `docs/RUNBOOK.md`
- `memorycore/lcm_adapter.py`
- new local-only script if needed: `scripts/validate_local_lcm_adapter.py`

Do not edit:

- `memorycore/qmd_adapter.py`
- `memorycore/mcp_surface.py`
- OpenClaw smoke execution artifacts

## Deliverables

1. Define a minimal Python interface for host-injected LCM functions.
2. Specify how `lcm_grep`, `lcm_describe`, and `lcm_expand_query` map to
   MemoryCore request/result fields.
3. Clarify verification semantics for summary IDs, message IDs, and unavailable
   host tools.
4. Draft or implement a synthetic/local-only eval that does not require private
   transcript IDs.
5. Preserve fixture adapter behavior.

## End Eval

Named end eval: `MEMORYCORE_LCM_LIVE_BACKEND`.

Executable target:

```bash
python3 scripts/validate_local_lcm_adapter.py --synthetic
```

The end eval passes when:

- it uses a synthetic host bridge or isolated test store, not private
  conversation data;
- grep/describe/expand-query shaped host results normalize into the shared
  MemoryCore result contract;
- absent summary/message, unavailable host tool, timeout, and unsupported
  freshness states return structured outcomes;
- successful recall is not counted as freshness verification unless the host
  bridge proves the referenced summary/message exists;
- `python3 -m memorycore.cli eval --public-safe` still reports
  `MEMORYCORE_LCM_LIVE_BACKEND` as skipped unless explicitly running local-only
  evals.

If this eval cannot be executed, the packet result must state `blocked` and
include the missing prerequisite.

## Acceptance Criteria

- Public-safe eval still passes.
- No public test depends on private LCM summaries or messages.
- Successful recall is not treated as freshness proof unless the host confirms
  the cited summary/message still exists.
- Tool-unavailable and timeout cases return structured errors or unknown state.

## Verification

```bash
python3 scripts/validate_mvp_lcm_adapter.py
python3 -m memorycore.cli eval --public-safe
```

Local-only verification, only when synthetic bridge exists:

```bash
python3 scripts/validate_local_lcm_adapter.py --synthetic
```

## Result Format

Return:

- changed files
- end eval name and status
- exact verification commands and results
- host bridge assumptions
- whether this packet is ready for implementation, review, or blocked
