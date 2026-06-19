# ASSESS-04 - Risk, Governance, And Observability

## Purpose

Assess whether MemoryCore gives users and operators meaningful observability,
control, safety, and governance over memory behavior. This lane should explain
why this is more than prompts or a model choosing tools.

## Ownership

- Write only: `tasks/assessment-reports/REPORT-04-risk-governance-observability.md`
- Read: risk, threat model, observability, audit/provenance, contracts, reviews.
- Do not touch: implementation, docs, schemas, evals, fixtures, task state,
  existing packets, git config, package files, CI.

## Context To Load

- `docs/OBSERVABILITY.md`
- `docs/THREAT_MODEL.md`
- `docs/RISK_REGISTER.md`
- `docs/API_CONTRACT.md`
- `docs/SOURCES.md`
- `docs/RUNBOOK.md`
- `docs/reviews/`
- `memorycore/audit_log.py`
- `memorycore/provenance_ledger.py`
- `memorycore/verification_state.py`
- `scripts/validate_mvp_contract_security.py`
- `scripts/validate_mvp_audit_log.py`
- `scripts/validate_mvp_provenance_ledger.py`

## Research Questions

- What can a user/operator observe today?
- What control does MemoryCore provide over backend choice, verification, audit,
  and failure handling?
- Does the project enforce content-sparse audit/provenance behavior?
- What privacy and prompt-injection risks are explicitly addressed?
- What safety/governance claims are proven by evals versus only documented?
- How does MemoryCore improve user control compared with prompt instructions or
  a harness with many memory tools?
- What risks remain before MVP?

## Constraints

- Read-only assessment only.
- You may run validation scripts if they do not mutate repo state.
- Do not edit threat/risk/observability docs.
- Do not inspect private memory content or use live transcript data.

## End Eval

- Eval ID: `MEMORYCORE_ASSESS_RISK_GOVERNANCE_OBSERVABILITY`
- Command: optional read-only validators:
  `python3 scripts/validate_mvp_contract_security.py`,
  `python3 scripts/validate_mvp_audit_log.py`,
  `python3 scripts/validate_mvp_provenance_ledger.py`
- Passing condition: report cites governance claims, implemented controls,
  validator evidence, and remaining risks.
- Correct blocked condition: if validators cannot run, cite the exact error and
  assess from source files.

## Reporting Contract

Return:

- report path written,
- files inspected,
- commands run,
- strongest governance findings,
- risk gaps,
- user-control assessment,
- confidence level.
