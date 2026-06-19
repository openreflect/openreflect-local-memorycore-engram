# Regression Review - 2026-06-19

Packet: `PACKET-10-regression-review`
End eval: `MEMORYCORE_REGRESSION_REVIEW`
Status: review complete; public-safe eval passed at review time.

## Scope

Review stance only. I reviewed validators first, then implementation and docs.
No live QMD, live Lossless-Claw, or OpenClaw smoke was run.

## Commands And Results

```bash
python3 -m memorycore.cli eval --public-safe
```

Result: passed. The consolidated runner returned `status: ok`, 14 passed eval
ids, and no failed eval ids. `MEMORYCORE_E2E_GOLDEN_PATH` was included in the
public-safe runner and passed. Skipped local-only eval ids were:
`MEMORYCORE_QMD_LIVE_BACKEND`, `MEMORYCORE_LCM_LIVE_BACKEND`, and
`MEMORYCORE_OPENCLAW_SMOKE`.

```bash
python3 - <<'PY'
from memorycore.mcp_surface import call_tool
for args in [
    {'query':'alpha-river-contract-fixture','limit':0},
    {'query':'alpha-river-contract-fixture','limit':51},
    {'query':'alpha-river-contract-fixture','backend':'mock_unhealthy'},
    {'query':'alpha-river-contract-fixture','intent':'source_get'},
    {'query':'alpha-river-contract-fixture','extra':'ignored'},
]:
    try:
        result = call_tool('memorycore_search', args)
        print(args, '=>', result.get('status'), result.get('error', {}).get('category'), result.get('selected_backend'))
    except Exception as exc:
        print(args, 'EXC', type(exc).__name__, str(exc))
PY
```

Result: confirmed MCP wrapper calls accept out-of-schema arguments. `limit: 0`,
`limit: 51`, and an extra unknown argument returned `ok`; `backend:
mock_unhealthy` was routed despite not being in the MCP descriptor enum.

```bash
python3 - <<'PY'
import json, warnings
from pathlib import Path
from jsonschema import Draft202012Validator
warnings.filterwarnings('ignore', message='jsonschema.RefResolver is deprecated.*', category=DeprecationWarning)
from jsonschema.validators import RefResolver
from memorycore.lcm_adapter import normalize_lcm_search, normalize_lcm_describe
root=Path.cwd(); schema_path=root/'schemas/result.schema.json'; schema=json.loads(schema_path.read_text()); v=Draft202012Validator(schema, resolver=RefResolver(base_uri=schema_path.as_uri(), referrer=schema))
req={'request_id':'req_probe_lcm','client_surface':'test','operation':'search','intent':'transcript_continuity_recall','backend_hint':'lossless_claw','query':'synthetic'}
res=normalize_lcm_search(req, {'mode':'probe','results':[{'summary_id':'sum_only','snippet':'x'}]})
print('search_errors', [e.message for e in v.iter_errors(res)])
reqv={'request_id':'req_probe_lcm_verify','client_surface':'test','operation':'verify','intent':'source_verify','pointer':{'backend_id':'lossless_claw','pointer_id':'sum_only'}}
resv=normalize_lcm_describe(reqv, {'summary_id':'sum_only','exists':True})
print('verify_errors', [e.message for e in v.iter_errors(resv)])
PY
```

Result: confirmed partial LCM host-shaped outputs can produce result payloads
that fail `schemas/result.schema.json` because optional pointer fields and score
are emitted with `None` values.

```bash
python3 - <<'PY'
import json, warnings
from pathlib import Path
from jsonschema import Draft202012Validator
warnings.filterwarnings('ignore', message='jsonschema.RefResolver is deprecated.*', category=DeprecationWarning)
from jsonschema.validators import RefResolver
from memorycore.qmd_adapter import live_local_qmd_status
root=Path.cwd(); schema_path=root/'schemas/result.schema.json'; schema=json.loads(schema_path.read_text()); v=Draft202012Validator(schema, resolver=RefResolver(base_uri=schema_path.as_uri(), referrer=schema))
res=live_local_qmd_status('req_probe_qmd', qmd_bin='memorycore-qmd-not-installed')
print(res['error'])
print([e.message for e in v.iter_errors(res)])
PY
```

Result: QMD unavailable error currently validates against the result schema for
the `backend_unavailable` case.

## Findings

### Medium - MCP runtime accepts arguments outside the advertised tool schema

`memorycore/mcp_surface.py` advertises strict MCP input schemas with enum,
minimum, maximum, and `additionalProperties: False` constraints
(`memorycore/mcp_surface.py:18`, `memorycore/mcp_surface.py:34`,
`memorycore/mcp_surface.py:60`). The actual `call_tool` path does not validate
against those schemas before building a request (`memorycore/mcp_surface.py:81`,
`memorycore/mcp_surface.py:103`, `memorycore/mcp_surface.py:110`,
`memorycore/mcp_surface.py:112`). The CLI path has the same limit gap because
`--limit` is typed as `int` but not range-checked (`memorycore/cli.py:73`,
`memorycore/cli.py:77`), while the canonical request schema requires `limit`
from 1 to 50 (`schemas/request.schema.json:38`).

Impact: MCP clients that do not enforce descriptors, direct in-process callers,
and CLI users can send invalid limits or unknown fields and still get successful
results. That weakens the advertised contract and leaves invalid requests out of
audit/error coverage.

Evidence: the probe above returned `ok` for `limit: 0`, `limit: 51`, and an
unknown `extra` argument.

Suggested next step: add request/tool argument validation at the MCP wrapper and
CLI boundary, and extend `scripts/validate_mvp_mcp_surface.py` and
`scripts/validate_mvp_cli.py` with negative cases.

Integration resolution: fixed after review. `memorycore.mcp_surface.call_tool`
now validates required fields, unknown fields, type, enum, and integer
min/max constraints against the advertised tool schema before building a
request. The CLI now range-checks search limits and constrains search intent
and verify state at the argument boundary. The original probe now blocks the
invalid calls instead of returning `ok`.

### Medium - LCM host normalization can emit schema-invalid `None` fields

`normalize_lcm_search` always includes `summary_id`, `message_id`,
`conversation_id`, and `score` fields even when the host output does not provide
them (`memorycore/lcm_adapter.py:124`, `memorycore/lcm_adapter.py:127`,
`memorycore/lcm_adapter.py:128`, `memorycore/lcm_adapter.py:129`,
`memorycore/lcm_adapter.py:132`). `normalize_lcm_describe` similarly includes
possibly absent `summary_id`, `message_id`, and `conversation_id`
(`memorycore/lcm_adapter.py:182`, `memorycore/lcm_adapter.py:183`,
`memorycore/lcm_adapter.py:210`, `memorycore/lcm_adapter.py:213`,
`memorycore/lcm_adapter.py:214`, `memorycore/lcm_adapter.py:215`).

The result schema allows those fields only as strings when present
(`schemas/result.schema.json:69`, `schemas/result.schema.json:73`,
`schemas/result.schema.json:77`, `schemas/result.schema.json:115`), so partial
but plausible host outputs produce schema-invalid normalized results.

Impact: live/synthetic LCM bridges may pass local functional checks but fail the
canonical result contract once host results omit optional metadata. This is most
likely to appear when a host bridge returns only a summary id or only a message
id.

Evidence: the schema probe above produced errors for `None is not of type
'string'` and `None is not of type 'number'`.

Suggested next step: omit optional pointer and score fields when absent, and add
a validator case with partial host output.

Integration resolution: fixed after review. `memorycore.lcm_adapter` now omits
optional pointer fields and score values when the host result does not provide
them. The partial-host schema probe now returns no result-schema errors.

### Medium - Local-only live error categories are ahead of the error schema

The canonical error schema currently allows `validation`, `unsupported_operation`,
`missing_backend`, `backend_unavailable`, `pointer_missing`,
`verification_unsupported`, and `unknown_failure` only
(`schemas/error.schema.json:11`). Local-only adapters already emit
`backend_timeout` and `backend_error`: QMD timeout uses `backend_timeout`
(`memorycore/qmd_adapter.py:273`, `memorycore/qmd_adapter.py:349`), LCM timeout
uses `backend_timeout` (`memorycore/lcm_adapter.py:66`), and host bridge
exceptions use `backend_error` (`memorycore/lcm_adapter.py:68`,
`memorycore/lcm_adapter.py:252`). The verification helper also recognizes
`backend_timeout` (`memorycore/verification_state.py:22`).

Impact: as live-local evals become contract-gated, timeout and host-error
results can be operationally correct but schema-invalid. This is exactly the
kind of schema drift the threat model names as a pre-live-expansion risk.

Suggested next step: either add these categories to `schemas/error.schema.json`
with docs and fixtures, or normalize live-local timeout/host exceptions into an
existing schema category.

Integration resolution: fixed after review. `backend_timeout` and
`backend_error` are now schema-defined categories with Packet A/B/C validator
coverage and public-safe error fixtures.

### Low - Task state around MCP handoff is stale or ambiguous

`tasks/todo.md` still marks Task 5 as incomplete and says its verification is
`python3 scripts/validate_mvp_mcp_surface.py` (`tasks/todo.md:29`,
`tasks/todo.md:32`). `tasks/plan.md` likewise leaves all Task 5 acceptance and
verification boxes unchecked (`tasks/plan.md:156`, `tasks/plan.md:162`), but
`MEMORYCORE_MCP_SURFACE` is included in the consolidated runner and passed
(`memorycore/eval.py:36`). Separately, Packet 07 defines the real server
entrypoint as a later eval (`tasks/agent-packets/PACKET-07-real-mcp-server.md:38`).

Impact: agents can misread Task 5 as still needing the in-process MCP surface
work, or as blocked on the real server entrypoint. That creates coordination
risk across Packet 03 and Packet 07.

Suggested next step: split task state explicitly: mark the in-process MCP
surface handoff complete if accepted, and leave the real MCP server entrypoint
tracked under Packet 07.

Integration resolution: fixed after review. `tasks/todo.md` and `tasks/plan.md`
now mark the MCP handoff complete and separately record the second-wave packet
integration state.

## Blocker Status

No blocker for PACKET-10. Baseline public-safe eval passed. Findings do not
require implementation changes in the review lane.

## Remaining Gaps

- I did not run live QMD, live Lossless-Claw, or OpenClaw smoke.
- I ran the public-safe E2E golden path only through the consolidated eval.
- There is no `tests/` directory; regression coverage is currently the
  deterministic `scripts/validate_*.py` surface.
- Parallel packet work was active during review, so any files outside this
  review document should be treated as owned by other lanes unless separately
  assigned.
