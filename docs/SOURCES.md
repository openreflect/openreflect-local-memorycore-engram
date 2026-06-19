# Sources

Status: source-contact baseline started.

This file tracks primary sources used to justify MemoryCore behavior.

## Source Categories

- QMD CLI behavior and query grammar
- Lossless-Claw host-tool behavior
- MCP interface assumptions
- OpenClaw caller path assumptions
- Public-safe fixture design

## QMD

Current source evidence captured before live adapter implementation:

- `command -v qmd` resolved the local CLI as available.
- `qmd --help` documents:
  - `qmd query <query>` for hybrid search with expansion and reranking.
  - `qmd search <query>` for BM25 keyword search.
  - `qmd get <file>[:line] [-l N]` for source retrieval.
  - `qmd status` for index and collection health.
  - `--json` for query/search/get style output.
  - `-c, --collection <name>` for collection-scoped search.
- `qmd status --json` was not assumed to be JSON-stable; observed local output
  was plain text status, so the first live-local adapter treats status as a
  health command with content-sparse snippet output and unknown freshness.
- `qmd search --json -c fixtures alpha-river-contract-fixture` returns a
  structured nonzero command failure if the local `fixtures` collection is not
  configured. The local eval reports this as blocked rather than creating or
  mutating QMD collections.
- `qmd get qmd://fixtures/corpus/project-alpha.md --json` returns a nonzero
  missing-document failure when the pointer is absent.

Exact live-local source-contact still needed for a passing local eval:

- An existing public-safe or synthetic local QMD collection named by
  `--collection`.
- One indexed markdown source containing the deterministic phrase
  `alpha-river-contract-fixture`, or a revised local-only query known to exist
  in that collection.
- One resolvable QMD pointer returned by search, verified through `qmd get`.

Adapter mode boundary:

- Fixture mode remains the public-safe default and uses only
  `fixtures/qmd/*.json` through `normalize_qmd_search()` and
  `normalize_qmd_get()`.
- Live-local mode is opt-in and uses `live_local_qmd_status()`,
  `live_local_qmd_search()`, and `live_local_qmd_get()` with explicit QMD CLI
  subprocess calls, collection scoping, and timeouts.
- `python3 -m memorycore.cli eval --public-safe` must continue to report
  `MEMORYCORE_QMD_LIVE_BACKEND` as skipped.

Live-local behavior records:

- unavailable QMD binary: `backend_unavailable`, verification `unknown`
- missing collection: `backend_unavailable`, verification `unknown`
- missing pointer: `pointer_missing`, verification `missing`
- nonzero command error: `unknown_failure`, verification `unknown`
- timeout: `unknown_failure`, verification `unknown`
- successful search: pointer-backed results, freshness `unknown`
- successful get: pointer resolution `verified`; broader source freshness remains
  out of scope until QMD exposes a hash or freshness signal

## Lossless-Claw

Current source evidence to capture before live adapter implementation:

- available host tool names and input/output shapes
- behavior of grep/describe/expand-query style calls
- verification limits for summary-backed versus message-backed evidence

Current adapter boundary assumption:

- MemoryCore receives a host-injected Python object with callable methods named
  `lcm_grep`, `lcm_describe`, and `lcm_expand_query`.
- `lcm_grep` maps to MemoryCore `search` and should return
  `results[]` items containing any available `summary_id`, `message_id`,
  `conversation_id`, `snippet`, and `score`.
- `lcm_expand_query` maps to MemoryCore `get` and should return an `answer`
  plus citation records. A successful answer preserves recall provenance but
  does not prove freshness by itself.
- `lcm_describe` maps to MemoryCore `verify` and is the first bridge operation
  allowed to report `verified` pointer presence. Missing pointers return
  `pointer_missing`; unavailable tools and timeouts return structured backend
  errors with `verification_state: unknown`.
- Local-only validation uses synthetic IDs such as `sum_synthetic_lcm_001` and
  must not use private transcript, summary, message, or conversation IDs.

## MCP

Current source evidence to capture before server implementation:

- expected tool registration shape
- request/response serialization rules
- local tool error behavior

## OpenClaw

OpenClaw integration remains gated by
`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`.
