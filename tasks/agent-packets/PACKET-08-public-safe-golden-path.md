# PACKET-08 - Public-Safe Golden Path

## Purpose

Build the public-safe portion of the end-to-end golden path so the project can demonstrate a successful and failed request loop through CLI/MCP, audit, provenance, and verification without running the gated OpenClaw smoke.

## Ownership

- Primary files/modules: E2E fixtures/docs/validator.
- Supporting docs/scripts: optional `fixtures/e2e/`, optional `scripts/validate_e2e_golden_path.py`, `docs/RUNBOOK.md`, `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`, `docs/MIGRATION_PLAN.md`.
- Do not touch: QMD safe collection creation, real MCP server implementation, packaging metadata, live OpenClaw integration code.

## Context To Load

- `SPEC.md`
- `docs/MVP_EVAL_PLAN.md`
- `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`
- `tasks/agent-packets/PACKET-05-integration-e2e.md`
- `memorycore/cli.py`
- `memorycore/mcp_surface.py`
- `memorycore/audit_log.py`
- `memorycore/provenance_ledger.py`

## Work Items

- Define a public-safe EVAL-013 path that runs successful and failed requests through existing CLI and MCP-shaped calls.
- Add fixtures or validator logic that checks audit/provenance records are inspectable and content-sparse.
- Keep the OpenClaw step explicitly skipped/not-run-by-design unless the hard stop is lifted.
- Wire the validator into documentation, and optionally into the public-safe eval runner if it is fully fixture-only.

## Constraints

- Do not run EVAL-012.
- Do not persist private snippets, content, citations, summaries, transcript text, prompts, or credentials.
- If OpenClaw is mentioned, it must be represented as gated/not-run in this packet.
- You are not alone in the codebase; do not revert or overwrite parallel packet work.

## End Eval

- Eval ID: `MEMORYCORE_E2E_GOLDEN_PATH`
- Command: preferred `python3 scripts/validate_e2e_golden_path.py`; also run `python3 -m memorycore.cli eval --public-safe`.
- Passing condition: public-safe CLI/MCP success and failure loops pass with sparse audit/provenance records and OpenClaw step clearly gated.
- Correct blocked/skipped condition: if the validator cannot be made fully public-safe, document why and keep the public-safe suite green.

## Reporting Contract

Return:

- changed files
- success/failure loop covered
- eval command and result
- OpenClaw smoke status
- blockers
- assumptions
- remaining gaps
