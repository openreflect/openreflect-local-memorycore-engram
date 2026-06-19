# Packet 04: Contracts, Security, Observability, And Review

Owner role: quality and hardening agent.

## Mission

Turn the scaffold discipline artifacts into actionable guardrails without
touching live backend implementation.

## Context To Load

- `SPEC.md`
- `docs/API_CONTRACT.md`
- `docs/THREAT_MODEL.md`
- `docs/OBSERVABILITY.md`
- `docs/RISK_REGISTER.md`
- `docs/reviews/REVIEW-2026-06-19.md`
- `schemas/`
- `scripts/validate_*`

## Primary Write Scope

- `docs/API_CONTRACT.md`
- `docs/THREAT_MODEL.md`
- `docs/OBSERVABILITY.md`
- `docs/RISK_REGISTER.md`
- `docs/reviews/REVIEW-2026-06-19.md`
- `schemas/*.json`
- validation scripts that check contract/security behavior

Do not edit:

- live QMD/LCM implementation behavior
- MCP server behavior except to request contract alignment
- OpenClaw smoke execution artifacts

## Deliverables

1. Define stable request/result/error contract invariants.
2. Add or propose public-safe leak checks for audit/provenance records.
3. Fill the review scaffold with concrete findings or explicitly state no issue.
4. Define observable event fields and forbidden fields.
5. Identify schema gaps before live adapters expand.

## Acceptance Criteria

- Public-safe eval still passes.
- Any schema change has matching fixtures and validation updates.
- Threat model distinguishes retrieved content from instructions.
- Audit/provenance rules explicitly forbid private snippets by default.

## Verification

```bash
python3 -m memorycore.cli eval --public-safe
```

Additional checks should be listed in the result if added.

## Result Format

Return:

- changed files
- review findings by severity
- new or proposed validation checks
- exact verification commands and results

