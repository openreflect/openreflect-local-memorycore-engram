# Packet 01: QMD Live-Local Adapter

Owner role: backend adapter agent.

## Mission

Prepare the first local-only QMD live adapter slice while preserving the current
public fixture adapter and public-safe eval suite.

## Context To Load

- `SPEC.md`
- `docs/LIVE_BACKEND_BOUNDARIES.md`
- `docs/SOURCES.md`
- `docs/adr/0003-qmd-cli-live-adapter-boundary.md`
- `memorycore/qmd_adapter.py`
- `scripts/validate_mvp_qmd_adapter.py`
- `fixtures/qmd/`

## Primary Write Scope

- `docs/SOURCES.md`
- `docs/PERFORMANCE_BASELINE.md`
- `docs/RUNBOOK.md`
- `memorycore/qmd_adapter.py`
- new local-only script if needed: `scripts/validate_local_qmd_adapter.py`
- optional local-only fixture notes under `docs/`

Do not edit:

- `memorycore/lcm_adapter.py`
- `memorycore/mcp_surface.py`
- OpenClaw smoke docs except for cross-reference requests

## Deliverables

1. Document exact QMD source-contact evidence needed for live-local mode.
2. Define the adapter mode boundary: fixture mode versus live-local mode.
3. Draft or implement `validate_local_qmd_adapter.py` so it is clearly excluded
   from `--public-safe`.
4. Preserve the existing normalized result contract.
5. Record timeout, stderr, missing pointer, stale pointer, and unavailable-QMD
   behavior.

## Acceptance Criteria

- Public-safe eval still passes.
- QMD fixture behavior is unchanged unless intentionally extended.
- Live-local behavior cannot run accidentally from public-safe evals.
- No private QMD snippets are persisted into audit/provenance logs.

## Verification

```bash
python3 scripts/validate_mvp_qmd_adapter.py
python3 -m memorycore.cli eval --public-safe
```

Local-only verification, only when explicitly safe:

```bash
python3 scripts/validate_local_qmd_adapter.py --collection fixtures
```

## Result Format

Return:

- changed files
- exact verification commands and results
- unresolved live-QMD questions
- whether this packet is ready for implementation, review, or blocked

