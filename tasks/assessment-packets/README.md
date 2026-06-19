# MemoryCore Assessment Packets

Status: active read-only assessment scaffold.

These packets split the MemoryCore project assessment across five independent
agents. This phase is not implementation. Agents must inspect the project,
collect evidence, and write reports only.

## Shared Rule

Do not mutate the codebase. Do not edit implementation, schemas, docs, evals,
task state, fixtures, package files, CI, or existing packet files.

Allowed write scope is limited to each agent's assigned report path under:

```text
tasks/assessment-reports/
```

Agents may run read-only commands and validation commands that do not modify
repo files. They may cite command output, but they must not run live OpenClaw
smoke or mutate live backend state.

## Shared Sources

Load these before writing conclusions:

1. `SPEC.md`
2. `README.md`
3. `docs/PRD.md`
4. `docs/MVP_SCOPE.md`
5. `docs/MVP_EVAL_PLAN.md`
6. `docs/ARCHITECTURE.md`
7. `docs/ROADMAP.md`
8. `docs/LIVE_BACKEND_BOUNDARIES.md`
9. `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`
10. `tasks/plan.md`
11. `tasks/todo.md`
12. `tasks/agent-packets/README.md`

Optional supporting sources:

- `docs/API_CONTRACT.md`
- `docs/MCP_HANDOFF.md`
- `docs/OBSERVABILITY.md`
- `docs/RISK_REGISTER.md`
- `docs/SOURCES.md`
- `docs/THREAT_MODEL.md`
- `docs/RUNBOOK.md`
- `docs/reviews/`
- `memorycore/`
- `scripts/validate_*.py`
- `schemas/`

## Assessment Packets

| Packet | Focus | Report Path |
| --- | --- | --- |
| `ASSESS-01-product-scope-mvp.md` | Product scope, MVP definition, and product-goal fit | `tasks/assessment-reports/REPORT-01-product-scope-mvp.md` |
| `ASSESS-02-architecture-abstraction.md` | Architecture, backend abstraction, and memory virtualization design | `tasks/assessment-reports/REPORT-02-architecture-abstraction.md` |
| `ASSESS-03-eval-evidence-current-state.md` | Eval evidence, current implementation state, and proof gaps | `tasks/assessment-reports/REPORT-03-eval-evidence-current-state.md` |
| `ASSESS-04-risk-governance-observability.md` | Risk, governance, safety, observability, and user control | `tasks/assessment-reports/REPORT-04-risk-governance-observability.md` |
| `ASSESS-05-remaining-work-roadmap.md` | Remaining work, blockers, sequencing, and shortest MVP path | `tasks/assessment-reports/REPORT-05-remaining-work-roadmap.md` |

## Required Report Shape

Every report must include:

- Executive answer in 5 bullets or fewer.
- Evidence table or bullet list with file paths and command names.
- Current-state findings separated from inference.
- MVP readiness judgment.
- Product-goal proximity judgment.
- Remaining gaps or blockers.
- Contradictions or ambiguities found in project materials.
- Confidence level and why.

## Comparison Goal

The coordinator will compare the five reports for:

- agreement,
- disagreement,
- missing evidence,
- overstated claims,
- MVP boundary drift,
- product-goal drift,
- shortest credible path to completion.
