# PACKET-06 - QMD Safe Fixture Collection

## Purpose

Unblock the QMD live-local eval by defining or creating a public-safe local QMD collection that contains only committed fixture corpus content. The goal is to prove the QMD adapter against real local QMD behavior without querying private memory collections.

## Ownership

- Primary files/modules: QMD fixture collection scripts/docs only.
- Supporting docs/scripts: `docs/RUNBOOK.md`, `docs/SOURCES.md`, `docs/PERFORMANCE_BASELINE.md`, `scripts/validate_local_qmd_adapter.py`, optional new `scripts/create_qmd_fixture_collection.py`.
- Do not touch: LCM adapter, MCP surface/server, OpenClaw smoke docs, contract/security schemas unless a narrow compatibility note is required.

## Context To Load

- `SPEC.md`
- `docs/MVP_EVAL_PLAN.md`
- `docs/LIVE_BACKEND_BOUNDARIES.md`
- `tasks/agent-packets/PACKET-01-qmd-live-local.md`
- `scripts/validate_local_qmd_adapter.py`
- `memorycore/qmd_adapter.py`
- `fixtures/corpus/`

## Work Items

- Determine the safest way to create or reference a QMD collection using only `fixtures/corpus/`.
- Add a small repeatable command or documented runbook step for creating/updating that collection if QMD supports it.
- Run `scripts/validate_local_qmd_adapter.py` against the safe collection if it exists; otherwise make the blocked condition explicit and reproducible.
- Capture one public-safe QMD search/get source-contact sample if the collection can be created locally.

## Constraints

- Do not query `memory` or any private collection.
- Do not persist private snippets, transcript text, summaries, prompts, or credentials.
- Keep public-safe eval behavior unchanged: `MEMORYCORE_QMD_LIVE_BACKEND` must remain skipped by `python3 -m memorycore.cli eval --public-safe`.
- You are not alone in the codebase; do not revert or overwrite parallel packet work.

## End Eval

- Eval ID: `MEMORYCORE_QMD_LIVE_BACKEND`
- Command: `python3 scripts/validate_local_qmd_adapter.py --collection <safe-public-fixture-collection>`
- Passing condition: validator returns `MEMORYCORE_QMD_LIVE_BACKEND_OK` using only fixture corpus content.
- Correct blocked/skipped condition: `MEMORYCORE_QMD_LIVE_BACKEND_BLOCKED` with exact missing QMD capability, missing collection, or unsupported create/index command evidence.

## Reporting Contract

Return:

- changed files
- safe collection name/path
- eval command and result
- whether QMD collection creation was run or only documented
- blockers
- assumptions
- remaining gaps
