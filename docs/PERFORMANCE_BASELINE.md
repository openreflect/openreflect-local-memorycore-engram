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
- live QMD status: under 5 seconds
- live QMD search/get against a small safe collection: under 10 seconds each
- live QMD timeout path: bounded by the caller's `--timeout-seconds` value
- live LCM request: budget not set
- audit/provenance append: under 100 ms

## Notes

The first QMD live-local adapter defaults to a 10 second subprocess timeout and
does not assume `qmd status` supports JSON output. Live-local eval timing should
be recorded only for explicitly safe collections; missing local prerequisites
should be reported as blocked, not treated as public-safe regressions.
