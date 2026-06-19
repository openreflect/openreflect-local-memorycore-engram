# PACKET-10 - Regression Review

## Purpose

Run an independent review of the integrated packet work and identify bugs, missing tests, schema drift, private-data leakage risks, brittle assumptions, and stale task state.

## Ownership

- Primary files/modules: review output only.
- Supporting docs/scripts: `docs/reviews/REVIEW-2026-06-19-regression.md`, optional read-only helper script if useful.
- Do not touch: implementation modules, schemas, validators, packaging, or smoke docs except to add a review note.

## Context To Load

- `SPEC.md`
- `docs/API_CONTRACT.md`
- `docs/THREAT_MODEL.md`
- `docs/OBSERVABILITY.md`
- `docs/RUNBOOK.md`
- `tasks/plan.md`
- `tasks/todo.md`
- all `tasks/agent-packets/`
- `memorycore/`
- `schemas/`
- `scripts/validate_*.py`

## Work Items

- Review tests/validators first, then implementation and docs.
- Look specifically for public/private boundary leaks, audit/provenance content leaks, unsupported operation ambiguity, schema drift, and stale task status.
- Produce findings ordered by severity with file/line references.
- If no issues are found, say so clearly and name residual risk/test gaps.

## Constraints

- This is primarily a review lane; do not fix issues unless they are tiny documentation corrections and cannot conflict with other packets.
- Do not run live QMD, live Lossless-Claw, or OpenClaw smoke.
- Do not expose private paths, credentials, or transcript content in review output.
- You are not alone in the codebase; do not revert or overwrite parallel packet work.

## End Eval

- Eval ID: `MEMORYCORE_REGRESSION_REVIEW`
- Command: `python3 -m memorycore.cli eval --public-safe` plus any read-only review commands used.
- Passing condition: review document exists with severity-ordered findings and public-safe eval status.
- Correct blocked/skipped condition: blocked only if repo cannot be inspected or baseline eval cannot run; include exact command failure.

## Reporting Contract

Return:

- changed files
- review file path
- eval command and result
- findings by severity
- blockers
- assumptions
- remaining gaps
