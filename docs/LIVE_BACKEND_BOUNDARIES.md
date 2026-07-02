# Live Backend Boundaries

Date: 2026-06-19
Status: Planning boundary

This document defines where the public fixture implementation ends and where
live backend integration begins.

The goal is to let implementation agents move from static contracts to real
backend calls without changing MemoryCore's shared request/result shape or
leaking private runtime state into the public repository.

## Current Fixture Boundary

The current implementation is fixture-only:

- `memorycore/qmd_adapter.py` normalizes static QMD-shaped JSON.
- `memorycore/lcm_adapter.py` normalizes static Lossless-Claw-shaped JSON.
- `memorycore/cli.py` routes requests to fixture outputs.
- `memorycore/mcp_surface.py` exposes MCP-shaped local calls over the same
  fixture path.
- `python3 -m memorycore.cli eval --public-safe` runs only public-safe fixture
  evals.

Fixture success proves contract stability. It does not prove live backend
functionality.

## QMD Live Boundary

### Source Contact

Local QMD is available on this machine:

```bash
~/.npm-global/bin/qmd
```

Observed CLI capabilities from `qmd --help`:

- `qmd query <query>` for hybrid search with expansion and reranking.
- `qmd search <query>` for BM25 keyword search.
- `qmd get <file>[:line] [-l N]` for source retrieval.
- `qmd status` for index and collection health.
- `qmd mcp` for MCP stdio serving.
- JSON output is available for query/search/get style commands through
  `--json`.

### First Live Mode

Use a local-only QMD adapter mode that shells out to the `qmd` CLI. Do not make
the public eval suite depend on the operator's private QMD index.

Recommended implementation shape:

```text
fixture mode:
  static fixtures/qmd/*.json

live-local mode:
  qmd query --json --collection <collection> <query>
  qmd get --json <pointer>
  qmd status --json if available, otherwise parse status conservatively
```

### Pointer Rules

QMD pointers should preserve:

- `backend_id: "qmd"`
- `pointer_id`: QMD file path or QMD source reference
- `source_uri`: same as pointer id unless QMD returns a richer URI
- optional line information when QMD returns it

MemoryCore must not copy private source content into provenance or audit records.
Search/get results may carry snippets/content in the immediate response, but
audit/provenance persistence remains pointer-first and content-sparse.

### Verification Rules

For the first live mode:

- `get` succeeds for the pointer: `verified`
- `get` reports no such source: `missing`
- QMD unavailable or command failure: structured backend error or `unknown`
- freshness beyond pointer resolution: `unknown` unless QMD exposes a source hash
  or index freshness signal

Do not report `verified` for stale-index freshness unless the adapter can prove
the source pointer resolves against current local source state.

### Eval Boundary

Add a local-only eval after the public runner exists:

```bash
python3 scripts/validate_local_qmd_adapter.py --collection fixtures
```

That script should be skipped by `python3 -m memorycore.cli eval --public-safe`
unless a future public fixture index can be created deterministically.

## Lossless-Claw Live Boundary

### Source Contact

Lossless-Claw is a host/runtime tool path, not a package dependency for the
public MemoryCore skeleton. The public repo should not import OpenClaw internals
or assume a private transcript store exists.

### First Live Mode

Use host-injected adapter functions rather than direct runtime imports.

Recommended implementation shape:

```text
fixture mode:
  static fixtures/lcm/*.json

live-local mode:
  caller supplies functions equivalent to:
    lcm_grep(query, scope)
    lcm_expand_query(query or summary ids, prompt)
    lcm_describe(summary id)
```

The adapter should normalize host tool results into the existing shared result
contract. If no host tool bridge is provided, the backend health should report
unavailable instead of silently falling back to fixture data.

### Pointer Rules

Lossless-Claw pointers should preserve available fields:

- `backend_id: "lossless_claw"`
- `pointer_id`: summary id or message id
- `summary_id`
- `message_id`
- `conversation_id`
- recall mode when available

Public evals must never depend on a private conversation id or committed
transcript content.

### Verification Rules

For the first live mode:

- summary/message can be described or resolved: `verified`
- summary/message is absent: `missing`
- tool cannot prove freshness: `unsupported`
- tool path unavailable or timeout: structured backend error or `unknown`

Do not treat a successful recall answer as freshness verification unless the
tool path confirms the referenced summary/message still exists.

### Eval Boundary

Add a local-only eval after a host bridge exists:

```bash
python3 scripts/validate_local_lcm_adapter.py --synthetic
```

Preferred source is an isolated synthetic LCM test store. If that does not
exist, keep live LCM validation manual/local-only and continue using public
fixtures for contract tests.

## OpenClaw Smoke Boundary

EVAL-012 remains gated by `docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`.

Do not start the smoke until these are recorded:

- approval source and timestamp lifting the hard stop,
- caller path,
- backend mode,
- exact entrypoint,
- audit file path,
- cleanup action,
- stop-condition reviewer.

Fixture-only OpenClaw smoke should run before live-backend OpenClaw smoke.

## Implementation Order

1. Keep public fixture evals green.
2. Add QMD live-local adapter behind an explicit mode.
3. Add a local-only QMD eval that is skipped by public-safe evals.
4. Add Lossless-Claw host-injected adapter boundary.
5. Add a synthetic/local-only LCM eval when the host path supports it.
6. Run EVAL-012 fixture-only after the hard stop is deliberately lifted.
7. Only then consider live-backend OpenClaw smoke.

## Non-Goals

- No QMD reindex orchestration in the adapter.
- No Lossless-Claw compaction ownership.
- No OpenClaw gateway mutation from public evals.
- No private transcript or memory export committed to this repository.
- No audit/provenance persistence of raw private snippets, content, citations,
  summaries, or transcript text by default.
