# REPORT-02 - Architecture And Abstraction Assessment

Date: 2026-06-19
Agent: 02
Packet: `tasks/assessment-packets/ASSESS-02-architecture-abstraction.md`
Eval ID: `MEMORYCORE_ASSESS_ARCHITECTURE_ABSTRACTION`
Scope: read-only architecture assessment; no implementation/docs/schema/eval mutations.

## Executive Judgment

MemoryCore has a coherent architecture for a memory abstraction/control plane, but the product is not yet fully functional as memory virtualization over real backends.

The strongest implemented pieces are the shared request/result/error schemas, deterministic backend routing, fixture-backed QMD and Lossless-Claw normalization, verification-state normalization, content-sparse audit/provenance records, CLI parity, MCP-shaped parity, and a real MCP server entrypoint. These prove the contract and client-surface shape.

The main gap is that the default routed CLI/MCP product path is still fixture-only. QMD has an explicit live-local subprocess adapter path, and Lossless-Claw has a host-injected bridge path with synthetic validation, but those live/local paths are not yet integrated into the common router/CLI/MCP runtime selection model. OpenClaw integration remains intentionally gated and unrun.

Architecture readiness: **medium-high for contract/control-plane architecture; medium-low for live memory virtualization readiness.**

## Files Inspected

- `tasks/assessment-packets/ASSESS-02-architecture-abstraction.md`
- `docs/ARCHITECTURE.md`
- `docs/API_CONTRACT.md`
- `docs/LIVE_BACKEND_BOUNDARIES.md`
- `docs/MCP_HANDOFF.md`
- `docs/MVP_SCOPE.md`
- `docs/MVP_EVAL_PLAN.md`
- `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`
- `memorycore/registry_router.py`
- `memorycore/qmd_adapter.py`
- `memorycore/lcm_adapter.py`
- `memorycore/mcp_surface.py`
- `memorycore/mcp_server.py`
- `memorycore/cli.py`
- `memorycore/eval.py`
- `memorycore/provenance_ledger.py`
- `memorycore/audit_log.py`
- `memorycore/verification_state.py`
- `schemas/request.schema.json`
- `schemas/result.schema.json`
- `schemas/error.schema.json`
- `scripts/validate_e2e_golden_path.py`

## Commands Run

- `git status --short`
  - Result: clean before report write.
- `python3 -m memorycore.cli eval --public-safe`
  - Result: `status: ok`; 14 passed evals; skipped local-only evals: `MEMORYCORE_QMD_LIVE_BACKEND`, `MEMORYCORE_LCM_LIVE_BACKEND`, `MEMORYCORE_OPENCLAW_SMOKE`; backend availability reported as fixture-only for QMD and Lossless-Claw and not-run-hard-stop for OpenClaw.
- `python3 -m memorycore.mcp_server --check`
  - Result: `status: available`; API `mcp.server.fastmcp.FastMCP`; tools registered: `memorycore_search`, `memorycore_get`, `memorycore_verify`, `memorycore_health`; transports: `stdio`, `sse`, `streamable-http`.
- `python3 scripts/validate_mvp_router.py && python3 scripts/validate_mvp_mcp_surface.py && python3 scripts/validate_mvp_contract_security.py`
  - Result: `MEMORYCORE_ROUTER_OK`, `MEMORYCORE_MCP_SURFACE_OK`, `MEMORYCORE_CONTRACT_SECURITY_OK`.
- `python3 scripts/validate_local_lcm_adapter.py --synthetic`
  - Result: `MEMORYCORE_LCM_LIVE_BACKEND_OK`.
- `git status --short`
  - Result: clean before report write.

I did not run EVAL-012, OpenClaw smoke, QMD collection creation, or live backend mutation commands.

## Actual Architectural Boundary

MemoryCore's intended boundary is a memory control plane, not a backend store and not an MCP-only wrapper.

Evidence:

- `docs/MVP_SCOPE.md` defines the MVP as "the smallest functional control plane" proving source-backed context routing over real memory backends, with real routing, provenance, verification, client access, and failure behavior.
- `docs/MVP_SCOPE.md` explicitly excludes MemoryCore-owned message, summary, embedding, observation stores, compaction ownership, reindex orchestration, and broad substrate adapters.
- `docs/API_CONTRACT.md` defines the public contract as request in, normalized result out, structured error on failure across CLI, MCP-shaped calls, and future runtime callers.
- `docs/LIVE_BACKEND_BOUNDARIES.md` says the goal is moving from static contracts to real backend calls without changing the shared request/result shape or leaking private runtime state.
- `memorycore/registry_router.py` states that it deliberately stops at deterministic contract behavior and does not import or call QMD, Lossless-Claw, Burrow, OpenClaw, or live backends.

Assessment:

The architectural boundary is appropriately narrow: MemoryCore should normalize, route, verify, and expose memory, while backends continue to own their indexes, transcript stores, compaction, and maintenance workflows.

## Abstraction Model

The abstraction model has five layers:

1. **Request contract**
   - `schemas/request.schema.json` defines `request_id`, `client_surface`, `operation`, optional `intent`, optional `backend_hint`, query, pointer, and limit.
   - Supported operations are `search`, `get`, `verify`, and `health`.

2. **Routing contract**
   - `memorycore/registry_router.py` maps intents to operations and routes explicit backend requests or auto-selects a healthy backend by operation/intent.
   - File/corpus recall and transcript-continuity recall are represented as backend-default intents.

3. **Adapter normalization**
   - `memorycore/qmd_adapter.py` normalizes fixture-shaped QMD search/get and also defines explicit live-local `qmd` subprocess functions.
   - `memorycore/lcm_adapter.py` normalizes fixture-shaped Lossless-Claw results and defines host-injected bridge functions for `lcm_grep`, `lcm_expand_query`, and `lcm_describe`.

4. **Result/error/verification contract**
   - `schemas/result.schema.json` requires normalized result items to include `backend_id`, `pointer`, and `verification_state`.
   - `schemas/error.schema.json` defines stable recovery categories including validation, unsupported operation, missing backend, backend unavailable, backend timeout, backend error, pointer missing, verification unsupported, and unknown failure.
   - `memorycore/verification_state.py` normalizes states to `verified`, `stale`, `missing`, `unsupported`, or `unknown`.

5. **Client surfaces and audit/provenance**
   - `memorycore/cli.py` provides a fixture-only local developer surface.
   - `memorycore/mcp_surface.py` maps MCP-shaped tool calls to the same request path.
   - `memorycore/mcp_server.py` wraps the MCP surface in a real FastMCP server entrypoint.
   - `memorycore/audit_log.py` and `memorycore/provenance_ledger.py` persist pointer-first metadata while excluding snippets, content, citations, summaries, answers, and text.

## Conceptual vs Proven Status

### Conceptual Design

The high-level product goal is conceptually clear:

- one stable memory contract,
- backend routing,
- normalized result shape,
- provenance pointers,
- verification state,
- content-sparse audit/provenance,
- CLI/MCP/OpenClaw client surfaces.

This is strongest in:

- `docs/MVP_SCOPE.md`
- `docs/API_CONTRACT.md`
- `docs/LIVE_BACKEND_BOUNDARIES.md`
- `docs/MCP_HANDOFF.md`
- `docs/MVP_EVAL_PLAN.md`

### Fixture-Proven Behavior

The following is fixture-proven:

- request/result/error contracts,
- deterministic routing,
- QMD fixture normalization,
- LCM fixture normalization,
- verification-state handling,
- content-sparse audit records,
- content-sparse provenance records,
- CLI behavior over fixture data,
- MCP-shaped behavior over fixture data,
- CLI/MCP result equivalence,
- public-safe golden path for CLI/MCP fixture loops.

Evidence:

- `python3 -m memorycore.cli eval --public-safe` passed 14 evals.
- `memorycore/eval.py` lists public-safe evals for packet contracts, router, QMD adapter, LCM adapter, provenance ledger, verification state, audit log, CLI, MCP surface, contract security, and E2E golden path.
- `scripts/validate_e2e_golden_path.py` explicitly validates CLI and MCP success/failure loops while stating it does not start MCP server, call OpenClaw, call live QMD/LCM, or run EVAL-012.

### Local-Only Proof

The following local-only proof exists:

- QMD live-local adapter functions exist in `memorycore/qmd_adapter.py`, using subprocess calls to `qmd status`, `qmd search --json`, and `qmd multi-get --json`.
- LCM host-injected adapter functions exist in `memorycore/lcm_adapter.py`, using a supplied bridge for `lcm_grep`, `lcm_expand_query`, and `lcm_describe`.
- `python3 scripts/validate_local_lcm_adapter.py --synthetic` passed with `MEMORYCORE_LCM_LIVE_BACKEND_OK`.
- Prior repo state includes a local QMD fixture collection artifact under `.memorycore/qmd-public-fixtures/`, but I did not mutate or recreate it in this assessment.

Important limitation:

The public-safe eval runner still reports `MEMORYCORE_QMD_LIVE_BACKEND` and `MEMORYCORE_LCM_LIVE_BACKEND` as skipped local-only evals. Local-only adapter proof is not the same as the default product path using live backends.

### Live Integration

Live integration is not complete.

Evidence:

- `memorycore/cli.py` states the CLI currently operates on public-safe fixture data only and does not call QMD, Lossless-Claw, Burrow, OpenClaw, or any live runtime.
- `memorycore/mcp_surface.py` states the MCP tool surface is fixture-only and does not start an MCP server or call OpenClaw, Burrow, QMD, or Lossless-Claw.
- `memorycore/mcp_server.py` binds the fixture-only MCP surface and explicitly does not call live QMD, Lossless-Claw, Burrow, OpenClaw, or private stores.
- `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md` says `MEMORYCORE_OPENCLAW_SMOKE` is not-run-by-design and the hard stop remains active until approval source and timestamp are recorded.
- `python3 -m memorycore.cli eval --public-safe` reports QMD and Lossless-Claw backend availability as fixture-only and OpenClaw as not-run-hard-stop.

## Does The Code Implement A Memory Abstraction Layer?

Answer: **partly, but not fully over real backends yet.**

It implements a real abstraction contract:

- canonical schemas,
- deterministic routing,
- adapter normalization,
- MCP and CLI client surfaces,
- stable errors,
- verification states,
- sparse audit/provenance.

It does not yet implement a fully operational abstraction layer in the default path because:

- `memorycore/cli.py` routes to fixture JSON files, not live adapters.
- `memorycore/mcp_surface.py` delegates to `_execute_request` from the fixture-only CLI path.
- `memorycore/mcp_server.py` wraps that same fixture-only MCP surface.
- Live QMD and host-injected LCM functions are present but not selected by the shared router/CLI/MCP runtime mode.
- OpenClaw has no executed integration smoke.

The current architecture is therefore best described as:

> A contract-complete, fixture-proven memory abstraction skeleton with local-only backend proofs and a real MCP server wrapper, but not yet an end-to-end live memory virtualization product.

## Backend Detail Hiding

Backend-specific detail is mostly hidden at the contract boundary, but leaks remain by design in pointer metadata.

Good abstraction:

- QMD and LCM both normalize into `request_id`, `operation`, `status`, `selected_backend`, `results`, pointer objects, and `verification_state`.
- `result.schema.json` permits QMD-style pointers (`source_uri`) and LCM-style pointers (`summary_id`, `message_id`, `conversation_id`) under one pointer object.
- Audit/provenance code stores backend ids and pointer fields without storing response content.

Intentional leakage:

- Pointer semantics remain backend-native: QMD uses file/source references; Lossless-Claw uses summary/message/conversation ids.
- This is acceptable for an MVP because provenance must preserve backend-native identifiers.

Risk:

- The request schema pointer definition only allows `backend_id`, `pointer_id`, and `source_uri`, while the result schema pointer allows `summary_id`, `message_id`, and `conversation_id`. That asymmetry may become a problem for LCM get/verify requests that need richer pointer input through canonical request validation.

## Routing As Policy Infrastructure

Routing is currently policy infrastructure, not prompt behavior.

Evidence:

- `registry_router.py` maps intents to expected operations.
- Explicit backend requests are honored when present.
- Backend health and capabilities are checked.
- Unsupported verify operations produce `verification_unsupported` and `unsupported`.
- `validate_mvp_router.py` passed.

Limitations:

- Auto-selection is simple first-healthy-candidate routing, not ranking, fanout, scoring, or cost-aware policy.
- Routing currently selects a backend, but the default execution path still uses fixture files after routing.
- There is not yet a configurable runtime backend mode such as fixture, qmd_live_local, lcm_host_bridge, or openclaw_smoke.

Judgment:

The router is enough for MVP policy proof, but insufficient for production memory virtualization until it can select actual backend execution modes.

## Provenance And Verification

Provenance and verification are first-class architectural concepts.

Evidence:

- `docs/MVP_SCOPE.md` includes real provenance pointers and real verification checks as core MVP requirements.
- `docs/API_CONTRACT.md` requires provenance pointer fields and verification state in successful results.
- `provenance_ledger.py` builds pointer-first result records with backend id, pointer, verification state, status, timestamp, and stable ledger id.
- `audit_log.py` records request/result metadata, selected backend, pointer ids, verification state, error category/code, and status while rejecting private result fields.
- `verification_state.py` centralizes normalization and maps backend timeout/error/unavailable to `unknown`.

Limitations:

- Audit and provenance records are built by CLI/MCP surfaces and validators; live backend paths are not yet wired through the full persisted audit/provenance loop in the default runtime.
- The MCP handoff doc says the current MCP surface does not append provenance ledger records directly; it returns normalized pointers that downstream provenance code can record.
- Verification is pointer-resolution/freshness state, not truth checking; that is correctly scoped but should stay explicit.

## Is This Collapsing Into "MCP For Memory Tools"?

No, not conceptually. Some implementation risk remains.

Why not:

- The central contract is request/result/error/provenance/verification, not MCP.
- CLI and MCP are treated as equivalent client surfaces over the same normalized model.
- MCP docs explicitly distinguish MCP transport wrapper details from core result fields.
- The MCP server delegates to `memorycore.mcp_surface.call_tool`, which delegates into the MemoryCore request path.

Risk:

- Because the only real external-facing server entrypoint today is MCP and it is fixture-only, observers may mistake the current artifact for an MCP wrapper until live backend routing and OpenClaw integration are proven.
- To avoid that collapse, the next architecture step should make backend mode selection explicit below CLI/MCP, not inside MCP-specific code.

## Contradictions And Design Risks

1. **Fixture-only docs conflict with newer local-only implementation**
   - `docs/LIVE_BACKEND_BOUNDARIES.md` says the current implementation is fixture-only.
   - `qmd_adapter.py` now includes live-local subprocess functions.
   - `lcm_adapter.py` now includes host-injected bridge functions.
   - This is not a fatal contradiction, but docs should distinguish "default routed product path is fixture-only" from "adapter-level local-only proofs exist."

2. **MVP definition requires real backends, but public-safe evals intentionally skip them**
   - `docs/MVP_SCOPE.md` says MVP means real backends, real routing, real provenance, real verification, and real client access.
   - `memorycore/eval.py` reports QMD/LCM as fixture-only in public-safe mode and skips live QMD, live LCM, and OpenClaw smoke.
   - Current state therefore cannot honestly be called MVP-complete.

3. **Live adapter paths are not wired into normal runtime routing**
   - `qmd_adapter.py` and `lcm_adapter.py` contain local/live boundary functions.
   - `cli.py` and `mcp_surface.py` still call fixture normalization via `_execute_request`.
   - This leaves a gap between adapter proof and product behavior.

4. **Request pointer schema may be too narrow for LCM verification**
   - `request.schema.json` pointer accepts only backend id, pointer id, and source URI.
   - `result.schema.json` pointer supports summary/message/conversation ids.
   - LCM host verification accepts summary/message fields internally, so the canonical request schema may need additive pointer fields before real LCM callers are comfortable.

5. **MCP server exists but real client smoke is still missing**
   - `mcp_server.py --check` proves dependency and tool registration.
   - `docs/MCP_HANDOFF.md` still lists real MCP client compatibility smoke, session/cancellation mapping, audit/provenance path policy, and production startup health behavior as remaining gaps.

6. **OpenClaw remains gated**
   - This is correct operational discipline, but product-goal claims should not count OpenClaw integration as proven.

## Architecture Readiness Judgment

### Contract Architecture

Readiness: **High**

Reason:

- Schemas exist and pass validators.
- Error categories are stable enough for recovery.
- CLI/MCP equivalence is tested.
- Audit/provenance safety is tested.
- Public-safe golden path is green.

### Backend Abstraction

Readiness: **Medium**

Reason:

- QMD and LCM have normalized shapes.
- QMD local subprocess path exists.
- LCM host bridge path exists and synthetic eval passes.
- But default routing still executes fixtures, not live backend mode.

### Memory Virtualization Over Real Backends

Readiness: **Low to Medium**

Reason:

- Local-only backend proofs exist, but live backend operation is not the normal client path.
- OpenClaw integration is not run.
- Backend mode selection is not yet a first-class runtime setting.

### Agent-Facing Surface

Readiness: **Medium-High**

Reason:

- CLI and MCP-shaped surfaces are green.
- MCP server entrypoint is available and registers four tools.
- Real MCP client smoke and production handoff details remain open.

### Governance/Observability Architecture

Readiness: **Medium-High**

Reason:

- Audit/provenance records are content-sparse and inspectable.
- Verification state is explicit.
- The architecture supports user/operator control.
- Production observability and live audit/provenance path policy remain incomplete.

## Required Next Architectural Steps

1. **Introduce explicit backend execution modes**
   - Example: `fixture`, `qmd_live_local`, `lcm_host_bridge`, `openclaw_smoke`.
   - This should be below CLI/MCP so both surfaces use the same backend policy.

2. **Wire QMD live-local path into a controlled runtime path**
   - Keep public-safe evals fixture-only.
   - Add local-only operator command/path that routes through MemoryCore, not only direct adapter validator calls.

3. **Wire LCM host bridge into the same controlled runtime path**
   - Use host injection only.
   - Do not import private OpenClaw/LCM internals into the public package.

4. **Add canonical request pointer support for LCM-native fields**
   - Additive schema change if needed: `summary_id`, `message_id`, `conversation_id`.

5. **Run real MCP client smoke**
   - After launch/install policy is settled.
   - Should remain fixture-only first.

6. **Run EVAL-012 only after hard-stop lift**
   - First as fixture-only OpenClaw caller path.
   - Only later consider live-backend OpenClaw smoke.

## Confidence Level

Confidence: **High for the architecture assessment; medium for local-only live-backend conclusions.**

Rationale:

- The contract, router, CLI, MCP surface, schemas, audit/provenance, and eval state were inspected directly.
- Public-safe eval and targeted validators were run successfully.
- I did not run QMD live-local validation or OpenClaw smoke during this assessment to avoid mutating live/backend state or crossing the packet boundary.
- Some local QMD capability is inferred from code and existing repository artifacts rather than revalidated in this run.

## Final Verdict

MemoryCore is architecturally pointed in the right direction. It is not merely an MCP wrapper and not merely a prompt substitute. It has the right control-plane primitives for memory virtualization: routing, normalization, provenance, verification, sparse audit, and client-surface equivalence.

The honest current state is that MemoryCore is **contract-complete and fixture-proven**, with **adapter-level local-only backend proofs**, but **not yet live-integrated as a full memory virtualization layer**. The remaining architectural work is mostly integration and runtime-mode selection, not rethinking the core abstraction.
