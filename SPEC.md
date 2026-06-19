# Spec: OpenReflect Local MemoryCore Engram MVP

## Objective

Build the smallest functional MemoryCore control plane that proves
source-backed memory routing over real backends without becoming a replacement
memory store.

The MVP answers one question:

```text
Given a memory request, can MemoryCore select an appropriate backend, retrieve
source-backed context, explain where it came from, verify whether it is fresh,
and expose that result through an agent-usable interface?
```

Primary users are local AI-agent runtimes, operators, and developers who need
memory answers with inspectable provenance rather than opaque recall.

Success means QMD, Lossless-Claw, CLI, MCP, and a first OpenClaw caller path can
prove the same narrow loop: search or get context, return a provenance pointer,
verify freshness where supported, and leave public-safe audit/provenance records.

## Tech Stack

- Language: Python 3.12-compatible standard-library-first implementation.
- Data format: JSON and JSONL for fixtures, request/result contracts, audit, and
  provenance records.
- Validation: deterministic public-safe scripts under `scripts/`.
- Initial client surfaces: CLI and MCP-shaped local tool functions.
- Initial backends: QMD and Lossless-Claw, with public fixtures and later
  local-only live integration paths.

## Commands

Current public-safe validation commands:

```bash
python3 scripts/validate_memory_record.py examples/memory-record.example.json
python3 scripts/validate_mvp_packet_a.py
python3 scripts/validate_mvp_packet_b.py
python3 scripts/validate_mvp_packet_c.py
python3 scripts/validate_mvp_router.py
python3 scripts/validate_mvp_qmd_adapter.py
python3 scripts/validate_mvp_lcm_adapter.py
python3 scripts/validate_mvp_provenance_ledger.py
python3 scripts/validate_mvp_verification_state.py
python3 scripts/validate_mvp_audit_log.py
python3 scripts/validate_mvp_cli.py
python3 scripts/validate_mvp_mcp_surface.py
```

Target consolidated command:

```bash
python3 -m memorycore.cli eval --public-safe
```

The consolidated command should report passed eval ids, failed eval ids,
skipped local-only eval ids, backend availability, fixture corpus status, and
audit/provenance record counts created during the run.

## Project Structure

```text
memorycore/       Runtime/library modules for contracts, routing, adapters,
                  audit, provenance, CLI, and MCP-shaped tools.
scripts/          Deterministic public-safe validation scripts.
schemas/          JSON schemas for backend, request, result, error, and memory
                  record contracts.
fixtures/         Public-safe backend, request, error, QMD, LCM, MCP, and corpus
                  fixtures.
examples/         Public-safe example memory records.
docs/             Product scope, architecture, roadmap, eval plan, and smoke
                  plans.
tasks/            Skill-compatible implementation plan and task status.
research/         Supporting research notes.
prompts/          Prompt artifacts used by validation or review workflows.
```

## Code Style

Prefer small, explicit, standard-library Python modules. Keep public fixtures and
runtime contracts readable by agents and humans.

```python
def route_request(request: dict[str, Any], registry: BackendRegistry) -> dict[str, Any]:
    operation = request.get("operation")
    intent = request.get("intent")

    if operation == "health":
        return {
            "request_id": request["request_id"],
            "operation": operation,
            "status": "ok",
            "results": registry.list_health(),
        }
```

Conventions:

- Return structured dictionaries with stable `status`, `operation`, `results`,
  and `error` fields.
- Prefer explicit error categories over exceptions at client boundaries.
- Do not store private snippets, content, citations, summaries, or transcript
  text in audit/provenance logs by default.
- Keep fixture-only code visibly labelled as fixture-only.
- Keep adapters backend-native; MemoryCore routes and verifies pointers, it does
  not own backend data planes.

## Testing Strategy

The repository currently uses deterministic validation scripts as the test
surface. Each MVP capability must have at least one public-safe eval before
dependent layers build on it.

Test levels:

- Contract evals for schemas, request/result shapes, and error categories.
- Adapter evals against public-safe static QMD and Lossless-Claw fixtures.
- Persistence evals for audit and provenance JSONL records.
- CLI and MCP-surface evals for local developer and agent access.
- Local-only live-backend evals for QMD and Lossless-Claw, excluded from public
  fixtures.
- OpenClaw integration smoke only after its documented hard stop is lifted.

Expected near-term improvement:

- Add one consolidated public-safe eval entrypoint.
- Optionally bridge the existing validation scripts into `pytest` later, without
  replacing the simple script path.

## Boundaries

Always:

- Keep public repo content synthetic and public-safe.
- Preserve provenance pointer identity and verification state.
- Return structured failures instead of empty successful results.
- Run the full public-safe eval suite before commits that affect behavior.
- Separate fixture-only evals from live-backend evals.

Ask first:

- Starting the OpenClaw integration smoke.
- Mutating OpenClaw gateway/runtime configuration.
- Calling live QMD or Lossless-Claw paths that may touch private memory.
- Adding dependencies.
- Changing the public/private repository boundary.

Never:

- Commit private memory exports, transcript databases, local index files, account
  ids, credentials, private paths, or environment-specific logs.
- Persist raw private snippets, content, citations, summaries, or transcript text
  into audit/provenance records by default.
- Treat mock fixture success as proof that the MVP is live-backend functional.
- Let MemoryCore replace QMD, Lossless-Claw, or other backend data planes.

## Success Criteria

- Public-safe evals pass through one canonical command.
- CLI can search, get, verify, and show recent audit records in JSON.
- MCP-shaped tools return the same normalized result shape as CLI JSON.
- QMD adapter can move from fixture output to a local live-backend path without
  changing the shared result contract.
- Lossless-Claw adapter can move from fixture output to a local or synthetic
  live-backend path without committing private transcript content.
- Audit and provenance records remain pointer-first and content-sparse.
- OpenClaw can perform at least one fixture-only `search` or `verify` operation
  through an explicitly chosen caller path after the EVAL-012 hard stop is
  deliberately lifted.

## Open Questions

- Which OpenClaw caller path should EVAL-012 use first: local MCP wrapper,
  OpenClaw plugin shim, or another named runtime path?
- Should the first live QMD eval use the existing local QMD index or an isolated
  test collection over `fixtures/corpus/`?
- Does the local Lossless-Claw tool path support an isolated synthetic test
  store, or should MVP LCM integration remain mock/local-only until that exists?
- Should the consolidated eval entrypoint stay inside `memorycore.cli`, or move
  to a dedicated `memorycore.eval` module with the CLI delegating to it?
