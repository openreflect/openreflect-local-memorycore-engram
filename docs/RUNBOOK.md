# Runbook

Status: scaffold.

## Public-Safe Eval

Run:

```bash
python3 -m memorycore.cli eval --public-safe
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

Do not run EVAL-012 unless `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md` has an
approved run note with the required fields.

## Cleanup Rules

- Remove temporary audit/provenance files after fixture evals unless the eval
  explicitly requires retained evidence.
- Do not commit generated private runtime state.
- Keep run notes public-safe unless explicitly local-only.

