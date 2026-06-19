# REPORT-04 - Risk, Governance, And Observability

Packet: `ASSESS-04-risk-governance-observability`
Eval ID: `MEMORYCORE_ASSESS_RISK_GOVERNANCE_OBSERVABILITY`
Status: complete
Date: 2026-06-19

## Executive Summary

MemoryCore currently provides a meaningful governance layer for memory access in
the public-safe MVP surface. Its strongest controls are not the existence of many
memory backends; they are the stable contract around backend selection,
verification state, structured failure, pointer-first provenance, and
content-sparse audit/observability.

The governance case is strongest for fixture-backed CLI/MCP-shaped behavior and
temporary public-safe audit/provenance artifacts. It is weaker for live
operation because QMD live-local, Lossless-Claw live bridge, and OpenClaw smoke
remain intentionally gated or local-only. That is the correct risk posture for
this stage, but it means MVP governance is proven for the control-plane contract,
not yet for full production memory virtualization.

## Commands Run

```bash
python3 scripts/validate_mvp_contract_security.py
```

Result: `MEMORYCORE_CONTRACT_SECURITY_OK`

```bash
python3 scripts/validate_mvp_audit_log.py
```

Result: `MEMORYCORE_AUDIT_LOG_OK`

```bash
python3 scripts/validate_mvp_provenance_ledger.py
```

Result: `MEMORYCORE_PROVENANCE_LEDGER_OK`

I did not run live QMD, live Lossless-Claw, or OpenClaw smoke. I did not inspect
private memory content or live transcript data.

## Files Inspected

- `docs/OBSERVABILITY.md`
- `docs/THREAT_MODEL.md`
- `docs/RISK_REGISTER.md`
- `docs/API_CONTRACT.md`
- `docs/SOURCES.md`
- `docs/RUNBOOK.md`
- `docs/reviews/REVIEW-2026-06-19.md`
- `docs/reviews/REVIEW-2026-06-19-regression.md`
- `memorycore/audit_log.py`
- `memorycore/provenance_ledger.py`
- `memorycore/verification_state.py`
- `scripts/validate_mvp_contract_security.py`
- `scripts/validate_mvp_audit_log.py`
- `scripts/validate_mvp_provenance_ledger.py`

## User-Control Assessment

MemoryCore gives the user/operator more control than a prompt-only or
many-tools harness because it turns memory behavior into inspectable contract
state:

- Backend selection is explicit through request fields, selected backend, and
  backend hints. The API contract defines request identity, client surface,
  operation, pointer identity, and backend hint semantics in
  `docs/API_CONTRACT.md:15-34`.
- Verification is explicit rather than implied. Result records must carry
  `verification_state`, and absence of live verification must become
  `unsupported` or `unknown`, not pretend-verified
  (`docs/API_CONTRACT.md:49-63`).
- Failures are structured for recovery. Errors carry stable code/category,
  content-sparse message/details, and optional verification state
  (`docs/API_CONTRACT.md:65-84`).
- Audit/provenance persistence is controlled separately from immediate response
  content. Returned `snippet`, `content`, and `citations` may be used to answer a
  current request, but are not safe to persist by default
  (`docs/API_CONTRACT.md:57-60`, `docs/API_CONTRACT.md:86-113`).
- CLI and MCP-shaped surfaces are meant to expose the same normalized model, so
  user/operator control does not depend on a single transport
  (`docs/API_CONTRACT.md:115-161`).

The current control surface is therefore a real control plane, but not yet a
full operator console. The repo proves contract-level control and sparse
records; it does not yet provide a user UI for enabling/disabling backends,
reviewing all audits, tuning ranking, or approving live memory operations.

## Observability Evidence

The observability design is explicit and content-sparse:

- It states that observability should explain what happened without storing
  memory content (`docs/OBSERVABILITY.md:5-6`).
- It names operational events: request received, backend selected/unavailable,
  result returned, verification attempted/unsupported, and error returned
  (`docs/OBSERVABILITY.md:8-16`).
- It prefers bounded operational fields such as request id, operation, backend
  id/mode, status, error category, pointer id, result count, verification state,
  elapsed time, timestamp, and eval id (`docs/OBSERVABILITY.md:18-35`).
- It forbids raw snippets, content, citations, summaries, answers, transcript
  text, source text, prompt text, credentials, tokens, account ids, local
  absolute paths where avoidable, and raw backend exception text by default
  (`docs/OBSERVABILITY.md:37-55`).
- It clarifies that observability output is not a transcript, answer cache, or
  prompt log (`docs/OBSERVABILITY.md:75-78`).

Executable evidence exists in `scripts/validate_mvp_contract_security.py`: it
defines allowed and forbidden observability fields
(`scripts/validate_mvp_contract_security.py:38-69`), checks that those fields
are documented (`scripts/validate_mvp_contract_security.py:244-249`), constructs
a valid sample event (`scripts/validate_mvp_contract_security.py:251-266`), and
rejects a bad event containing `content`
(`scripts/validate_mvp_contract_security.py:268-279`).

Gap: there is no general runtime event stream implementation in the inspected
surface. Observability is currently a documented/event-shape contract plus
validator guardrail, while audit/provenance provide the concrete persisted
metadata paths.

## Content-Sparse Audit And Provenance Evidence

Audit records are implemented as metadata and pointer summaries:

- `memorycore/audit_log.py` states that records store request/result metadata
  and pointer ids only, never answer or source text
  (`memorycore/audit_log.py:1-5`).
- Audit record fields include request id, client surface, operation, normalized
  intent, selected backend, result count, pointer ids, verification state, error
  state, timestamp, status, and audit id (`memorycore/audit_log.py:18-35`).
- The public-safe guard rejects private result fields: `snippet`, `content`,
  `citations`, `summary`, `answer`, and `text`
  (`memorycore/audit_log.py:15`, `memorycore/audit_log.py:53-57`).

Provenance records are also pointer-first:

- `memorycore/provenance_ledger.py` states that the ledger intentionally does
  not persist snippets, content, citations, or private source text
  (`memorycore/provenance_ledger.py:1-5`).
- Pointer fields are limited to backend/pointer/source ids and LCM-style
  summary/message/conversation ids (`memorycore/provenance_ledger.py:15-22`).
- Successful result records store request id, backend id, operation, pointer,
  verification state, timestamp, result index, status, and generated ledger id
  (`memorycore/provenance_ledger.py:25-40`).
- Error records store structured error code/category rather than raw exception
  text (`memorycore/provenance_ledger.py:42-59`).

Executable evidence:

- `scripts/validate_mvp_audit_log.py` validates required audit fields, audit id
  prefix, canonical verification state, public-safe constraints, QMD and LCM
  pointer ids, unsupported verify, unavailable backend, validation error, and
  temporary JSONL readback (`scripts/validate_mvp_audit_log.py:39-145`).
- `scripts/validate_mvp_provenance_ledger.py` confirms QMD search creates one
  ledger record per result, no `snippet` or `content` is stored, LCM pointers
  preserve `summary_id`, LCM verification remains `unknown`, missing pointers
  create structured error ledger records, and temporary readback works
  (`scripts/validate_mvp_provenance_ledger.py:38-92`).
- `scripts/validate_mvp_contract_security.py` rejects forbidden fields
  recursively (`scripts/validate_mvp_contract_security.py:108-117`), checks QMD
  and LCM audit/provenance persistence (`scripts/validate_mvp_contract_security.py:186-220`),
  and confirms an explicit `snippet` leak is rejected
  (`scripts/validate_mvp_contract_security.py:222-227`).

## Safety And Governance Findings

### Strong Finding 1 - MemoryCore makes prompt-injection boundaries explicit

The threat model identifies retrieved content as untrusted data, not
instructions (`docs/THREAT_MODEL.md:23-38`). It specifically says retrieved
content must not change backend selection, verification state, tool
permissions, write paths, or external-action policy
(`docs/THREAT_MODEL.md:34-35`). This directly addresses the weakness of a
prompt-only memory harness: the memory result is not allowed to become the
governing instruction.

`MEMORYCORE_CONTRACT_SECURITY` validates that this rule is present in the
contract/threat docs by checking phrases such as "immediate response data only",
"not instructions", "retrieved content is data", and "untrusted data"
(`scripts/validate_mvp_contract_security.py:230-241`).

### Strong Finding 2 - Verification misrepresentation is explicitly controlled

The threat model says unsupported or unknown freshness must not be presented as
verified and defines `unsupported`, `unknown`, `missing`, and `verified`
conditions (`docs/THREAT_MODEL.md:60-71`). The implementation maps pointer
missing to `missing`, verification unsupported to `unsupported`, and backend
timeout/error/unavailable to `unknown`
(`memorycore/verification_state.py:12-41`).

This is a meaningful governance control because stale or unverified memory is a
high-risk failure mode in multi-backend memory systems.

### Strong Finding 3 - Live integration is gated instead of quietly overclaimed

The runbook requires public-safe evals to pass while live/local-only evals are
skipped and named (`docs/RUNBOOK.md:27-31`). It says the local-only QMD eval is
excluded from public-safe evals (`docs/RUNBOOK.md:62-66`), EVAL-012 requires an
approved run note before execution (`docs/RUNBOOK.md:68-73`), the OpenClaw leg
of EVAL-013 must wait for approved EVAL-012 completion and hard-stop lift
(`docs/RUNBOOK.md:98-102`), and LCM live-backend validation must use synthetic
IDs unless a separate approval names a live host path (`docs/RUNBOOK.md:104-114`).

This is good governance: it prevents fixture confidence from being confused
with live readiness.

### Strong Finding 4 - Prior governance regressions were found and resolved

The regression review found medium issues in MCP argument enforcement, LCM
optional field normalization, and live-local error category/schema drift
(`docs/reviews/REVIEW-2026-06-19-regression.md:88-175`). It records integration
resolutions for all three (`docs/reviews/REVIEW-2026-06-19-regression.md:113-118`,
`docs/reviews/REVIEW-2026-06-19-regression.md:148-150`,
`docs/reviews/REVIEW-2026-06-19-regression.md:173-175`). This matters because it
shows the project has already used review/eval feedback to harden governance
claims rather than merely documenting them.

## Risks And Safety Gaps Before MVP

### Medium Risk - Observability is not yet a full operational product surface

The observability contract is strong, but the inspected implementation does not
yet show a durable user-facing observability stream, dashboard, review command,
or policy UI. Audit/provenance JSONL helpers exist, but an operator still needs
tooling to inspect, filter, compare, and act on them across real sessions.

MVP implication: acceptable for a developer/control-plane MVP, not sufficient
for a productized user-control experience.

### Medium Risk - Live backend governance is partially proven, not fully proven

The risk register itself warns that fixture evals can overstate live backend
readiness (`docs/RISK_REGISTER.md:7-13`). Sources document opt-in QMD
live-local behavior and skipped public-safe live evals
(`docs/SOURCES.md:66-86`), while Lossless-Claw live bridge behavior remains an
adapter-boundary assumption with synthetic/local-only validation
(`docs/SOURCES.md:96-111`).

MVP implication: governance claims should be framed as "public-safe contract
proved; live integrations gated or local-only," not "all memory backends are
governed in production."

### Medium Risk - Staleness and freshness remain hard problems

The risk register calls out stale backend indexes and ambiguous LCM verification
(`docs/RISK_REGISTER.md:23-36`). Sources state that successful QMD search has
freshness `unknown`, and even successful QMD get verifies pointer resolution
while broader source freshness remains out of scope until QMD exposes a hash or
freshness signal (`docs/SOURCES.md:77-86`). LCM expand-query preserves recall
provenance but does not prove freshness by itself (`docs/SOURCES.md:103-105`).

MVP implication: the current system avoids overclaiming, which is good, but it
does not yet solve end-to-end freshness assurance.

### Medium Risk - Prompt-injection controls are contract-level, not end-to-end prompt assembly

The threat model and contract correctly define retrieved content as untrusted
data. The validator proves the rule is documented. However, I did not find a
full prompt-assembly layer that enforces placement, quoting, or sandboxing of
retrieved content for all downstream agents.

MVP implication: good enough for MemoryCore as a memory control plane, but a
caller integration MVP still needs a concrete prompt-assembly policy test.

### Low Risk - Schema/versioning governance is early

The API contract says no external versioning scheme exists yet and recommends
additive changes with breaking changes marked in the migration plan
(`docs/API_CONTRACT.md:163-166`). The review notes possible future work adding
JSON Schema `$id` values (`docs/reviews/REVIEW-2026-06-19.md:79-86`).

MVP implication: not blocking for a local MVP, but important before public API
stability claims.

## Comparison Against Prompt-Only Or Many-Tool Harness

Compared with a prompt that tells the model when to use QMD, LCM, or another
backend, MemoryCore provides enforceable structure in four places:

- Backend behavior is hidden behind adapters and normalized result contracts
  (`docs/API_CONTRACT.md:8-13`).
- Prompt-injection boundaries are declared outside the model's momentary
  attention (`docs/THREAT_MODEL.md:23-38`).
- Audit/provenance persistence is denied access to content-bearing fields by
  implementation and validators (`memorycore/audit_log.py:15`,
  `scripts/validate_mvp_contract_security.py:186-227`).
- Verification states and structured failures are represented as data the caller
  can inspect, not as narrative confidence (`docs/API_CONTRACT.md:61-84`,
  `memorycore/verification_state.py:12-41`).

This is the main governance distinction: prompts can ask the model to behave;
MemoryCore makes a large part of the behavior observable, testable, and
repeatable.

## Confidence Level

Confidence: medium-high for public-safe MVP governance.

Reasons:

- High confidence that the public-safe audit, provenance, contract-security, and
  documented observability guardrails currently pass their validators.
- High confidence that content-sparse persistence is implemented for the
  inspected audit/provenance helpers.
- Medium confidence for live-backend governance because live QMD/LCM/OpenClaw
  execution was intentionally not run in this lane.
- Medium confidence for product-level user control because the contract is good,
  but a user-facing control/observability surface is not yet present in the
  inspected evidence.

## Blockers

No blocker for this assessment lane.

The main limitation is scope: this report is based on public-safe source files
and validators only. It does not certify live backend behavior, private-memory
handling, OpenClaw smoke behavior, or a production user-control UI.
