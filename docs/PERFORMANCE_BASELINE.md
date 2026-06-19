# Performance Baseline

Status: scaffold.

## Current Baseline

Command:

```bash
python3 -m memorycore.cli eval --public-safe
```

Record:

- date
- git commit
- runtime duration
- passed eval count
- skipped eval count
- notable slow commands

## Target Budgets

Initial draft budgets:

- public-safe eval suite: under 5 seconds
- fixture CLI request: under 500 ms
- live QMD request: budget not set
- live LCM request: budget not set
- audit/provenance append: under 100 ms

## Notes

Budgets should be revised after live local adapters exist.

