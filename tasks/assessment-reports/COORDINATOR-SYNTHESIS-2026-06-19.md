# Coordinator Synthesis - MemoryCore Assessment

Date: 2026-06-19
Mode: read-only synthesis of five assessment agents
Reports compared:

- `REPORT-01-product-scope-mvp.md`
- `REPORT-02-architecture-abstraction.md`
- `REPORT-03-eval-evidence-current-state.md`
- `REPORT-04-risk-governance-observability.md`
- `REPORT-05-remaining-work-roadmap.md`

## Executive Answer

All five agents converged on the same central conclusion: MemoryCore is a
strong public-safe control-plane kernel, but it is not yet a fully claimable
MVP under the project's own definition because live/backend/OpenClaw proof is
still gated or local-only.

The current project is best described as contract-complete, fixture-proven, and
locally scaffolded for live backend work. It is not yet a complete memory
virtualization product over real backends.

The shortest path to MVP is not another broad feature wave. It is controlled
acceptance: reconcile stale docs, preserve public-safe green evals, record
EVAL-012 approval fields, run fixture-only OpenClaw smoke through the selected
caller path, clean/isolate artifacts, and rerun public-safe evals.

Coordinator readiness estimate:

- MVP readiness: 65-75%.
- Broader memory virtualization/product-goal readiness: 40-50%.
- Confidence: medium-high.

## Cross-Agent Consensus

### 1. Product Definition

All reports agree that MemoryCore is a memory control plane, not a replacement
database, MCP bundle, prompt strategy, or generic connector marketplace.

The product value is a stable memory contract across backends: route, normalize,
preserve provenance, expose verification state, and make memory behavior
inspectable.

### 2. MVP Is Not Complete Yet

All reports agree the project cannot honestly claim full MVP completion while
EVAL-012/OpenClaw smoke remains hard-gated and unrun.

The source-defined MVP requires QMD, Lossless-Claw, OpenClaw, and MCP to prove
the loop end to end. Public-safe CLI/MCP fixture success is necessary but not
sufficient.

### 3. Public-Safe Eval Surface Is Strong

Reports 01, 02, 03, and 05 independently cite the same public-safe eval result:

- `python3 -m memorycore.cli eval --public-safe`
- status: `ok`
- passed evals: 14
- failed evals: 0
- skipped local-only/live evals:
  - `MEMORYCORE_QMD_LIVE_BACKEND`
  - `MEMORYCORE_LCM_LIVE_BACKEND`
  - `MEMORYCORE_OPENCLAW_SMOKE`

This proves the public-safe control-plane skeleton: schemas, routing, fixture
adapters, provenance, verification state, audit, CLI, MCP surface, contract
security, and CLI/MCP golden path.

### 4. Live Proof Is The Boundary

All reports draw the same line:

- QMD and Lossless-Claw are fixture-only in the public-safe runner.
- QMD has a local fixture collection path, but it is local-only.
- LCM has a synthetic host-bridge path, but it is local-only/synthetic.
- OpenClaw smoke is explicitly `not-run-by-design`.

This is a healthy safety boundary, but it limits MVP claims.

### 5. Governance Is A Real Differentiator

Report 04 emphasizes that MemoryCore is not just better memory access for the
model. It is memory governance for the human/operator.

The strongest governance controls are:

- explicit backend selection,
- verification state,
- structured failures,
- pointer-first provenance,
- content-sparse audit,
- retrieved content treated as data, not instructions.

This is the clearest answer to why MemoryCore should not be replaced by prompts
or a model harness with many memory tools.

## Differences In Emphasis

### Product/MVP Lane

Report 01 gives the clearest product framing and readiness scores:

- about 70% to source-defined MVP,
- about 45% to broader memory virtualization/product goal.

It stresses that the current repo is a strong public-safe MVP candidate, not a
completed MVP.

### Architecture Lane

Report 02 is stricter architecturally:

- contract/control-plane architecture is medium-high readiness,
- live memory virtualization readiness is medium-low.

It points out that the default CLI/MCP path is still fixture-backed, while live
adapter functions are not yet fully selected by the shared runtime mode.

### Eval Lane

Report 03 is the cleanest evidence boundary:

- public-safe evals are green,
- local-only LCM synthetic eval passes,
- MCP server entrypoint passes,
- E2E golden path passes for the fixture CLI/MCP subset,
- live QMD and OpenClaw were not run.

This report is the strongest guard against overclaiming.

### Governance Lane

Report 04 adds the user-control argument:

- current governance is well supported for contract/audit/provenance surfaces,
- full product-level user control remains unbuilt,
- observability is mostly contract plus persisted metadata, not a full UI or
  operations console yet.

### Roadmap Lane

Report 05 is the clearest operational plan:

- remaining MVP work is controlled acceptance,
- central blocker is EVAL-012,
- broad roadmap items should not distract v0.1.

It also found stale-doc drift around QMD collection naming, MCP server entrypoint
status, and fixture-only wording.

## Contradictions And Drift

The agents found no fatal contradiction in product direction. They did find
state drift from rapid implementation:

- Some docs still describe the current implementation as fixture-only, while
  task state and recent work now include a real MCP server entrypoint,
  packaging path, public-safe E2E validator, local QMD fixture collection path,
  and synthetic LCM validation.
- Some docs still reference a QMD collection named `fixtures`, while newer
  state uses `memorycore-public-fixtures`.
- Some eval-plan wording says the MCP surface does not start an MCP server,
  while Packet 07 added a real MCP server entrypoint check.

This drift is not a product blocker, but it is an operator-risk blocker before
declaring MVP readiness.

## What Is Done

Done enough to count:

- public-safe schemas/contracts,
- deterministic router,
- QMD fixture adapter,
- LCM fixture adapter,
- provenance ledger,
- verification state contract,
- content-sparse audit log,
- CLI surface,
- MCP-shaped surface,
- real MCP server entrypoint check,
- package/install path,
- public-safe CLI/MCP golden path,
- contract/security validators,
- regression review and fixes,
- explicit live backend boundaries,
- explicit OpenClaw smoke gate.

## What Is Not Done

Not done under the source-defined MVP:

- approved EVAL-012/OpenClaw smoke,
- OpenClaw caller leg of EVAL-013,
- default product path proven over live QMD and live Lossless-Claw,
- final reconciled MVP readiness ledger,
- stale-doc cleanup,
- productized user control/observability surface.

## MVP Verdict

The MVP is close but not complete.

The current state is a strong MVP release candidate for the contract/control
plane kernel. It becomes a claimable MVP only after the OpenClaw caller path is
proved under the gated smoke plan and the public-safe eval suite remains green
after cleanup.

## Product-Goal Verdict

MemoryCore is materially aligned with the broader product goal, but still early.

It has the right core primitives:

- backend abstraction,
- stable request/result/error contracts,
- routing,
- provenance,
- verification,
- audit,
- CLI/MCP surfaces.

It does not yet have the broader product surface:

- many backend substrates,
- policy-managed mirroring/splitting,
- backup/migration workflows,
- user-facing observability/control UI,
- Hermes/Codex/ChatGPT/Claude integrations,
- production-grade live backend orchestration.

The product direction is correct; the implemented surface is still v0.1 kernel
work.

## Shortest Credible Next Path

1. Reconcile stale docs without adding features.
2. Produce an MVP readiness ledger with done/partial/blocked/post-MVP state.
3. Confirm local-only QMD/LCM checks only where already safe and prepared.
4. Prepare the EVAL-012 run note fields:
   - approval source/timestamp,
   - caller path,
   - backend mode,
   - entrypoint,
   - audit path,
   - cleanup action,
   - stop-condition reviewer.
5. Run fixture-only EVAL-012 through the selected local caller path after
   approval.
6. Inspect and clean/isolate artifacts.
7. Rerun `python3 -m memorycore.cli eval --public-safe`.
8. Issue a final MVP verdict from evidence.

## Coordinator Confidence

Confidence: medium-high.

Why:

- Five independent lanes converged on the same central blocker.
- Multiple agents ran or cited the same public-safe eval evidence.
- Reports were constrained to read-only evidence collection.
- The remaining uncertainty is not broad architecture; it is the controlled
  OpenClaw/live-backend acceptance boundary.

Residual risk:

- Rapid doc/task drift can mislead later agents if not reconciled.
- Local-only QMD/LCM status should not be overgeneralized into production live
  backend readiness.
- Product-goal readiness remains an informed estimate, not a measured eval.
