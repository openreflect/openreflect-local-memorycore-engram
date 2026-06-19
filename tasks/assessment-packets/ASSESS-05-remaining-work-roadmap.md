# ASSESS-05 - Remaining Work And Roadmap

## Purpose

Assess how much work remains, what is blocked, what is post-MVP, and what the
shortest credible path is from the current repo to a real MVP.

## Ownership

- Write only: `tasks/assessment-reports/REPORT-05-remaining-work-roadmap.md`
- Read: roadmap, task state, eval plan, live backend boundaries, smoke plan,
  prior packet results, reviews.
- Do not touch: implementation, docs, schemas, evals, fixtures, task state,
  existing packets, git config, package files, CI.

## Context To Load

- `tasks/todo.md`
- `tasks/plan.md`
- `docs/ROADMAP.md`
- `docs/MVP_SCOPE.md`
- `docs/MVP_EVAL_PLAN.md`
- `docs/LIVE_BACKEND_BOUNDARIES.md`
- `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`
- `tasks/agent-packets/README.md`
- `docs/reviews/`
- `README.md`
- `pyproject.toml`

## Research Questions

- What is complete now?
- What remains for MVP?
- Which remaining items are blocked by explicit approval, environment, missing
  integration, or unresolved design?
- Which items are optional or post-MVP?
- Which task/docs appear stale after recent packet work?
- What is the shortest credible sequence to MVP completion?
- What are the highest-leverage next 3-5 actions after this assessment?
- What would be irresponsible to claim as complete today?

## Constraints

- Read-only assessment only.
- Do not update task files even if they appear stale.
- Do not run live OpenClaw smoke.
- Do not edit roadmap or plan files.
- Separate "necessary for MVP" from "nice to have" and "later product."

## End Eval

- Eval ID: `MEMORYCORE_ASSESS_REMAINING_WORK_ROADMAP`
- Command: not executable; report review by coordinator.
- Passing condition: report gives a sequenced remaining-work map with evidence,
  blockers, post-MVP exclusions, and shortest credible MVP path.
- Correct blocked condition: if task state cannot be reconciled, identify the
  conflicting files and provide competing interpretations.

## Reporting Contract

Return:

- report path written,
- files inspected,
- commands run,
- remaining-work estimate,
- blocker map,
- proposed MVP completion sequence,
- confidence level.
