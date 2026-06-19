# Runbook

Status: scaffold.

## Public-Safe Eval

From a fresh checkout, install the package in editable mode:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e ".[eval]"
```

Run the canonical module command:

```bash
python3 -m memorycore.cli eval --public-safe
```

The editable install also provides an equivalent console script:

```bash
memorycore eval --public-safe
```

Expected baseline:

- overall status: `ok`
- public-safe evals pass
- live/local-only evals are skipped and named

## If Public-Safe Eval Fails

1. Read the failed eval id.
2. Run the underlying command reported by the eval runner.
3. Inspect the matching fixture, schema, or module.
4. Fix the smallest failing contract.
5. Re-run the consolidated eval.

## If A Live Eval Is Requested

Check `docs/LIVE_BACKEND_BOUNDARIES.md` first.

For the local-only QMD eval, run only when the named collection is known to be
public-safe or synthetic:

```bash
python3 scripts/validate_local_qmd_adapter.py --collection fixtures
```

Expected outcomes:

- `MEMORYCORE_QMD_LIVE_BACKEND_OK`: live-local status, search, get, missing
  pointer, unavailable-QMD, command-error, and timeout handling passed.
- `MEMORYCORE_QMD_LIVE_BACKEND_BLOCKED`: QMD or the requested collection is
  unavailable. Do not create, reindex, or mutate QMD collections just to force
  the eval.
- `MEMORYCORE_QMD_LIVE_BACKEND_INVALID`: the local adapter contract changed or
  the safe collection did not contain expected searchable content.

The local-only QMD eval is deliberately excluded from:

```bash
python3 -m memorycore.cli eval --public-safe
```

Do not run EVAL-012 unless `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md` has an
approved run note with the required fields.

Recommended first caller path for a future approved EVAL-012 run: local MCP
wrapper in fixture-only mode. Do not mutate OpenClaw runtime or gateway config
as part of the first smoke.

## If EVAL-013 Is Requested

Check the EVAL-013 planning section in
`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md` first.

Run the public-safe CLI/MCP subset with:

```bash
python3 scripts/validate_e2e_golden_path.py
python3 -m memorycore.cli eval --public-safe
```

Expected public-safe outcomes:

- `MEMORYCORE_E2E_GOLDEN_PATH_OK`
- CLI and MCP-shaped success loops return pointer metadata, verification state,
  and audit ids.
- CLI and MCP-shaped failed loops expose `VERIFICATION_UNSUPPORTED` and
  `verification_unsupported`.
- Temporary audit/provenance records are content-sparse and deleted when the
  validator exits.
- OpenClaw smoke remains `not-run-by-design`.

Do not run the OpenClaw caller leg of EVAL-013 until:

- EVAL-012 has an approved, completed, public-safe run note.
- The approved OpenClaw caller path is named.
- The hard stop on OpenClaw/Burrow integration execution has been lifted.

## If MEMORYCORE_LCM_LIVE_BACKEND Is Requested

Run only the synthetic/local-only bridge eval unless a separate approval names
a live host tool path:

```bash
python3 scripts/validate_local_lcm_adapter.py --synthetic
```

The eval must use synthetic summary/message IDs and must not call private
Lossless-Claw transcript stores.

## MCP Surface Handoff Check

Run `python3 scripts/validate_mvp_mcp_surface.py` before changing MCP tool
descriptors or the CLI/MCP wrapper mapping. The check compares MCP-shaped calls
with equivalent CLI calls after removing only `request_id` and `audit_id`.

## Cleanup Rules

- Remove temporary audit/provenance files after fixture evals unless the eval
  explicitly requires retained evidence.
- Do not commit generated private runtime state.
- Keep run notes public-safe unless explicitly local-only.
- For EVAL-012 and EVAL-013 artifacts, record whether each audit/provenance file
  was deleted or isolated, and re-run
  `python3 -m memorycore.cli eval --public-safe` afterward.
- Do not retain snippets, content, citations, summaries, transcript text,
  account ids, or private runtime paths in committed run notes.
