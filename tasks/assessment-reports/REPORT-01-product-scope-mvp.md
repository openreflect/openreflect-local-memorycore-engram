# REPORT-01 - Product Scope And MVP Assessment

Date: 2026-06-19
Agent: 01
Packet: `tasks/assessment-packets/ASSESS-01-product-scope-mvp.md`
Report path: `tasks/assessment-reports/REPORT-01-product-scope-mvp.md`
Eval ID: `MEMORYCORE_ASSESS_PRODUCT_SCOPE_MVP`

## Executive Summary

MemoryCore is best defined as a local-first memory control plane for
source-backed agent context. Its job is not to replace QMD, Lossless-Claw, or
future memory systems. Its job is to route memory requests across those
systems, normalize results, preserve provenance pointers, expose verification
state, and provide agent/user-facing surfaces for safe inspection and control.

The current repository is strong as a public-safe MVP scaffold and contract
kernel. Public-safe evals pass, CLI/MCP-shaped loops work over fixtures, audit
and provenance are content-sparse, and product boundaries are documented.

However, by the project's own MVP definition, the full MVP is not complete yet.
The MVP requires proof over real memory backends and an OpenClaw caller path.
Current eval output reports QMD and Lossless-Claw as `fixture-only`, OpenClaw as
`not-run-hard-stop`, and skips `MEMORYCORE_QMD_LIVE_BACKEND`,
`MEMORYCORE_LCM_LIVE_BACKEND`, and `MEMORYCORE_OPENCLAW_SMOKE`.

Readiness judgment: 70% to credible MVP, 45% to the broader product goal of
memory virtualization and abstraction.

## Files Inspected

- `tasks/assessment-packets/ASSESS-01-product-scope-mvp.md`
- `docs/PRD.md`
- `docs/MVP_SCOPE.md`
- `docs/ROADMAP.md`
- `SPEC.md`
- `README.md`
- `tasks/plan.md`
- `tasks/todo.md`
- `docs/MVP_EVAL_PLAN.md`
- `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`
- `docs/LIVE_BACKEND_BOUNDARIES.md`
- repository file inventory via `find . -maxdepth 3 -type f`
- recent commit history via `git log --oneline -12`

## Commands Run

```bash
pwd && git status --short && sed -n '1,240p' tasks/assessment-packets/ASSESS-01-product-scope-mvp.md
find . -maxdepth 3 -type f | sort | sed -n '1,240p'
git log --oneline -12
sed -n '1,240p' docs/PRD.md && sed -n '1,240p' docs/MVP_SCOPE.md
sed -n '1,260p' docs/ROADMAP.md && sed -n '1,260p' SPEC.md
sed -n '1,260p' README.md && sed -n '1,320p' docs/MVP_EVAL_PLAN.md
sed -n '1,300p' tasks/plan.md && sed -n '1,260p' tasks/todo.md
nl -ba docs/MVP_SCOPE.md | sed -n '1,260p'
nl -ba docs/PRD.md | sed -n '1,220p' && nl -ba docs/ROADMAP.md | sed -n '1,240p'
nl -ba SPEC.md | sed -n '1,240p' && nl -ba tasks/todo.md | sed -n '1,220p'
nl -ba docs/MVP_EVAL_PLAN.md | sed -n '1,360p'
nl -ba docs/MVP_SCOPE.md | sed -n '248,420p'
nl -ba docs/MVP_EVAL_PLAN.md | sed -n '360,760p'
nl -ba docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md | sed -n '1,260p'
nl -ba docs/LIVE_BACKEND_BOUNDARIES.md | sed -n '1,260p'
python3 -m memorycore.cli eval --public-safe
test -e tasks/assessment-reports/REPORT-01-product-scope-mvp.md; echo $?
git status --short -- tasks/assessment-reports/REPORT-01-product-scope-mvp.md tasks/assessment-reports
```

## Product Definition

### Evidence

`docs/PRD.md` defines MemoryCore as "a local-first memory control plane for
source-backed context" that routes memory work, preserves provenance, verifies
freshness, and exposes context shaping through usable app/plugin surfaces
(`docs/PRD.md:6-11`).

The PRD names early users as AI builders, operators managing multiple memory
systems, researchers/founders comparing memory substrates, and OpenReflect /
Empathos developers (`docs/PRD.md:18-36`).

The core product shape includes chat/app inspection, plugins for Hermes,
OpenClaw, and Codex, an MCP surface, and a narrow local API for search, get,
verify, route, mirror, split, backup, and migration workflows
(`docs/PRD.md:38-52`).

The roadmap says v0.1 is "a backend memory control plane: more than a switch,
less than a replacement memory store" (`docs/ROADMAP.md:6-8`).

### Inference

The simplest accurate definition is:

MemoryCore is a control plane that lets agents and users ask for memory through
one stable contract while backend systems keep owning their native data. It is
not an MCP bundle, not a generic connector marketplace, not a vector database,
and not a replacement memory store.

## Top Three Product Features In User Language

### Evidence

The PRD goals include routing requests by capability, policy, provenance,
freshness, cost, and privacy; preserving source pointers and verification state;
supporting QMD and Lossless-Claw; providing OpenClaw integration and MCP; and
making context shaping inspectable (`docs/PRD.md:69-81`).

The MVP scope requires real routing decisions, provenance pointers,
verification checks, client access, and clear failure behavior
(`docs/MVP_SCOPE.md:11-22`).

### Inference

The top three features in user language are:

1. One memory interface for multiple memory systems.
2. Source-backed answers with provenance and verification state.
3. User/operator control over memory behavior through audit, routing, backend
   health, and stable agent-facing surfaces.

## MVP Definition

### Evidence

`docs/MVP_SCOPE.md` defines the MVP as "the smallest functional control plane
that proves source-backed context routing over real memory backends"
(`docs/MVP_SCOPE.md:6-10`).

The MVP thesis asks whether MemoryCore can select an appropriate backend,
retrieve source-backed context, explain where it came from, verify freshness,
and expose the result through an agent-usable interface
(`docs/MVP_SCOPE.md:24-35`).

The MVP succeeds if QMD, Lossless-Claw, OpenClaw, and MCP prove that loop
end-to-end (`docs/MVP_SCOPE.md:34-35`).

`SPEC.md` repeats the same narrow loop and says success means QMD,
Lossless-Claw, CLI, MCP, and a first OpenClaw caller path can prove search/get,
provenance pointer return, freshness verification where supported, and
public-safe audit/provenance records (`SPEC.md:3-22`).

`docs/MVP_SCOPE.md` says the MVP is complete when a user or agent can ask for
file or transcript memory, have MemoryCore select QMD or Lossless-Claw,
receive backend identity and pointers, verify pointers, inspect audit, and use
the loop from CLI, MCP, and OpenClaw (`docs/MVP_SCOPE.md:404-416`).

### Inference

The MVP is not "a nice fixture demo." The MVP is a narrow but real product
kernel:

- QMD and Lossless-Claw represented as initial memory backends.
- A deterministic router.
- A normalized request/result/error contract.
- Provenance pointer ledger and audit log.
- Verification-state contract.
- CLI and MCP agent surfaces.
- One approved OpenClaw caller path.
- Public/private safety boundaries.

## Current State Evidence

### Strongly Satisfied

- Product thesis and boundary are documented in PRD, MVP scope, roadmap, and
  spec (`docs/PRD.md:6-11`, `docs/ROADMAP.md:6-8`, `SPEC.md:3-22`).
- Backend registry, routing, QMD/LCM adapter contracts, provenance, verification,
  audit, CLI, MCP surface, contract security, and public-safe golden path all
  pass in the public-safe eval runner.
- The public-safe eval command returned `status: ok`, no failed eval IDs, and
  14 passed eval IDs:
  `ENGRAM_MEMORY_RECORD`, `MEMORYCORE_PACKET_A`,
  `MEMORYCORE_PACKET_B`, `MEMORYCORE_PACKET_C`,
  `MEMORYCORE_ROUTER`, `MEMORYCORE_QMD_ADAPTER`,
  `MEMORYCORE_LCM_ADAPTER`, `MEMORYCORE_PROVENANCE_LEDGER`,
  `MEMORYCORE_VERIFICATION_STATE`, `MEMORYCORE_AUDIT_LOG`,
  `MEMORYCORE_CLI`, `MEMORYCORE_MCP_SURFACE`,
  `MEMORYCORE_CONTRACT_SECURITY`, and `MEMORYCORE_E2E_GOLDEN_PATH`.
- The eval output reported `audit_records_created: 0` and
  `provenance_records_created: 0`, matching the content-sparse public-safe
  fixture approach.
- `tasks/todo.md` marks Tasks 1, 2, 3, 4, 5, 5a, 5b, 5c, 5d, and 6 complete
  (`tasks/todo.md:3-73`).

### Partially Satisfied

- QMD live boundary is defined and local QMD availability is documented, but
  public-safe eval output still reports QMD as `fixture-only`
  (`docs/LIVE_BACKEND_BOUNDARIES.md:28-101`; eval output).
- Lossless-Claw live boundary is defined around host-injected tool functions,
  but public-safe eval output still reports Lossless-Claw as `fixture-only`
  (`docs/LIVE_BACKEND_BOUNDARIES.md:102-168`; eval output).
- MCP is stronger than a shape-only contract because a real server entrypoint
  exists in the repo inventory, but the MVP source docs still define the MCP
  evidence mainly through CLI/MCP fixture and contract evals; full external MCP
  client proof should be verified by the architecture/eval lanes.
- EVAL-013 public-safe golden path is passing for CLI/MCP, but its OpenClaw leg
  is gated by EVAL-012 (`docs/MVP_EVAL_PLAN.md:592-633`,
  `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:154-193`).

### Not Satisfied / Blocked

- OpenClaw integration smoke has not run. The smoke plan status is "Draft, not
  executed" and says `MEMORYCORE_OPENCLAW_SMOKE` is `not-run-by-design`
  (`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:1-32`).
- EVAL-012 requires an approval source, caller path, backend mode, exact
  entrypoint, audit path, cleanup action, and stop-condition reviewer before
  execution (`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md:71-84`).
- The public-safe eval command explicitly skipped
  `MEMORYCORE_QMD_LIVE_BACKEND`, `MEMORYCORE_LCM_LIVE_BACKEND`, and
  `MEMORYCORE_OPENCLAW_SMOKE`.
- The task list keeps Task 7 open for EVAL-012 and Task 8 open for the full
  CLI/MCP/OpenClaw golden path (`tasks/todo.md:75-92`).

## MVP Readiness Judgment

Score: 70%

Rationale:

- The contract/control-plane kernel is mostly built and well tested through
  public-safe deterministic evals.
- The public-safe CLI/MCP loop is credible enough to demonstrate the shape of
  the product.
- The repo has strong safety posture: fixture-only public evals, no raw private
  content in audit/provenance by default, and explicit live-boundary docs.
- But the project's own MVP definition requires real backend proof and an
  OpenClaw caller path. Those are not complete.
- Public-safe success must not be counted as live-backend MVP completion because
  `SPEC.md` explicitly says not to treat mock fixture success as proof that the
  MVP is live-backend functional (`SPEC.md:153-160`).

MVP verdict:

MemoryCore is near the MVP boundary but not across it. It is currently a strong
public-safe MVP candidate / release candidate for the control-plane contract,
not yet the full MVP as defined by project documents.

## Product-Goal Proximity Judgment

Score: 45%

Rationale:

The broader product goal is bigger than v0.1. The roadmap describes a future
"memory fabric" where different substrates such as spreadsheets, Notion,
Google Drive, S3 objects, QMD documents, LCM transcript messages, and Honcho
observations get common control-plane treatment (`docs/ROADMAP.md:130-163`).

The repo is close to proving the core abstraction pattern:

- backend capability descriptions,
- routing,
- provenance pointer preservation,
- verification state,
- audit,
- CLI/MCP surfaces.

But many product-level capabilities are deliberately post-MVP:

- Hermes and Codex plugin paths,
- ChatGPT/Claude app packaging,
- REST and Pinecone-style compatibility,
- Notion/Drive/spreadsheet/S3/filesystem substrate adapters,
- backup/migration execution,
- mirroring/splitting,
- insight plugins,
- visualizations,
- cost/token diagnostics
  (`docs/MVP_SCOPE.md:318-335`; `docs/PRD.md:106-130`).

Therefore, the project is conceptually aligned with memory virtualization and
abstraction, but only the first control-plane slice is implemented.

## MVP Boundary Versus Later Roadmap

### MVP

- QMD and Lossless-Claw as initial read/search/get/verify backends.
- Registry/capability probing.
- Deterministic routing.
- Provenance and audit.
- Verification contract.
- CLI and MCP agent surfaces.
- Initial OpenClaw integration path.

### Later Roadmap

- Hermes/Codex/ChatGPT/Claude plugin packaging.
- REST/Pinecone-compatible adoption surfaces.
- Nontraditional substrates such as Notion, Drive, spreadsheets, object stores,
  and filesystem shares.
- Mirroring/splitting.
- Backup/migration execution.
- Insight plugins and derived observations.
- Visualization and cost/context diagnostics.

## Blockers And Ambiguities

1. OpenClaw integration is the primary MVP blocker.
   EVAL-012 is explicitly not run and requires hard-stop lift plus run-note
   metadata before execution.

2. Real backend status is nuanced.
   The repo contains local-only boundary plans and local-only scripts, but the
   canonical public-safe eval output still reports QMD and Lossless-Claw as
   `fixture-only`. This assessment did not run local-only live backend evals to
   avoid touching live backend state.

3. "MVP" can be interpreted two ways.
   If MVP means "public-safe contract kernel," it is close to complete. If MVP
   means the source-defined product MVP, it still needs QMD/LCM live proof and
   OpenClaw proof.

4. Product name/frame has two layers.
   README still frames the repository as OpenReflect-Local-MemoryCore-Engram
   and a git-native provenance substrate. PRD/MVP docs frame MemoryCore as a
   broader memory control plane. These are compatible if Engram is treated as
   the local provenance substrate for MemoryCore, but the product narrative
   should eventually be tightened.

## Recommended Shortest Path To MVP

1. Keep public-safe evals green.
2. Run or confirm the local-only QMD fixture collection eval and capture the
   exact result in a report/run note.
3. Run or confirm the local-only/synthetic Lossless-Claw eval and capture the
   exact result in a report/run note.
4. Lift the EVAL-012 hard stop explicitly, choose the local MCP wrapper caller
   path unless overridden, and run the fixture-only OpenClaw smoke.
5. Re-run `python3 -m memorycore.cli eval --public-safe`.
6. Mark MVP complete only if CLI, MCP, QMD, Lossless-Claw, and OpenClaw all
   satisfy the narrow loop with content-sparse audit/provenance.

## Confidence

Confidence level: High for product/MVP definition and current public-safe eval
status. Medium for live-backend readiness because this lane intentionally did
not run local-only live QMD or LCM checks and did not inspect every adapter
implementation line.

## Final Assessment

MemoryCore is a well-scoped and increasingly real control-plane product. Its
distinct value is not "more memory tools"; it is enforcing a stable memory
contract below the model: routing, backend identity, provenance, verification,
audit, and safety.

The current codebase has crossed the hard part of product shape and contract
discipline. What remains for MVP is narrower but important: source-contact
proof over real/local backends and an approved OpenClaw caller path.
