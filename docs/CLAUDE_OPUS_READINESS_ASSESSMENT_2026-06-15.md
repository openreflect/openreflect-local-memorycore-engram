# Claude Opus Readiness Assessment

Date: 2026-06-15
Reviewer: Claude Code CLI
Requested model: `claude-opus-4-8`
Mode: read-only assessment

## Runtime Note

Claude reported:

> Claude Code CLI, model `claude-opus-4-8` (Claude Opus 4.x family). This was a read-only review — no files were edited.

## Readiness Verdict

Claude's blunt verdict:

**Not ready to build the singular product. Approximately 20% ready.**

Breakdown:

- Vision/spec maturity: approximately 75%.
- Implementation readiness: approximately 10%.
- Weighted overall: approximately 20% toward "a team could start building the real product with confidence."

Claude's core read:

The spec describes what to build well, but does not yet define behavior precisely enough to implement. There are no interface contracts, request/response schemas, context-assembly algorithms, summarization policies, model/runtime ownership decisions, migration runner, or golden-path test harness.

## What Is Strong

- The feature inventory in `research/memory-stack-feature-spec-2026-06-15.md` is the strongest artifact. It is source-grounded and maps daily memory capabilities across QMD, Lossless-Claw, Honcho, and OpenClaw.
- The product thesis is coherent: source evidence must outrank summaries, and summaries must outrank inference.
- The storage model is directionally sound: SQLite/WAL/FTS5 aligns with the existing systems.
- The provenance contract is the real differentiator.
- The phased milestones are a usable sequencing skeleton.

## Blocking Gaps

- No interface contracts for MCP tools, HTTP endpoints, or SDK methods.
- The current JSON schema is a toy compared with the table model in the software spec.
- Context assembly is undefined beyond a rough ordering.
- Summarization and compaction are under-specified, especially compared with Lossless-Claw's summary DAG.
- The reasoning pipeline names observation types but does not define extraction prompts, contracts, batching, or confidence rules.
- Model/runtime ownership is unresolved.
- No migration runner exists.
- Existing stores are not imported or reconciled.
- Test strategy is limited to one validator plus prose exit criteria.

## Major Architectural Risks

1. **Replace-vs-orchestrate contradiction.** The feature inventory argues for keeping QMD, Lossless-Claw, and Honcho authoritative in their respective layers. The software spec argues for one singular replacement substrate. These are different products.
2. **Reimplementing all three mature systems is a multi-quarter trap.** QMD hybrid search, Lossless-Claw compaction, and Honcho derivation are each substantial.
3. **Single-process MVP may fight async reasoning and SQLite write contention.**
4. **Derived-claim provenance is the hardest unsolved part.** File hash verification is easy; proving an inductive observation remains current across changing sources is research-grade.
5. **Embedding model decisions and re-embedding costs are unresolved.**
6. **Stable peer identity is under-specified**, risking Honcho-style memory fragmentation.

## Recommended MVP Boundary

Claude recommends cutting the MVP down to a provenance-anchored retrieval core.

In scope:

- SQLite store: `memory_records`, `source_artifacts`, `collections`, plus session/message ingest tables.
- File collection ingestion.
- FTS5 lexical search.
- `get` with line ranges.
- Git commit and content-hash provenance on every record.
- `verify` returning current, stale, or unsupported.
- CLI plus contract-complete MCP tools for `memory_search`, `memory_get`, `memory_verify`, and `memory_status`.
- Doctor/status command.

Out of scope:

- Summarization.
- Observation/reasoning.
- Vector search.
- Context packet assembly.
- Peer cards.
- UI.
- HTTP API.

Claude's judgment: ship the smallest thing that proves provenance-backed retrieval with verifiable drilldown before attempting to replace the harder memory systems.

## Recommended Phases

1. **Phase 0: decisions and contracts.** Resolve replace-vs-orchestrate. Write JSON schemas for every MCP tool and reconcile the public schema with the internal table model.
2. **Phase 1: store and provenance spine.** Implement schema, migration runner, CRUD, content-hash/git capture, and `verify`.
3. **Phase 2: corpus retrieval.** Add collections, file ingestion, FTS5 search, `get`, and doctor. This is the shippable MVP.
4. **Phase 3: transcript continuity.** Only if replacing Lossless-Claw. Start with deterministic extractive summaries and concrete token budgeting.
5. **Phase 4: reasoned observations.** Add async queue and source-linked explicit/deductive observations.
6. **Phase 5: vector/hybrid and evidence bundles.** Add semantic retrieval and derived-claim staleness tooling.

Claude specifically recommends moving provenance forward into Phase 1 because it is the reason the product exists and cannot be bolted on later.

## First Engineering Tasks

1. Write a schema reconciliation doc that defines one canonical record shape.
2. Write `schemas/mcp/*.json` contracts for `memory_search`, `memory_get`, `memory_verify`, and `memory_status`.
3. Implement SQLite migration runner and Phase 1 tables.
4. Implement ingestion for one file collection with content-hash and git-commit capture.
5. Implement FTS5 search and `get` with line ranges.
6. Implement `verify`.
7. Build a golden-path behavioral test for ingest -> search -> get -> verify.

## Blocking Questions

1. Is MemoryCore a ground-up replacement for QMD, Lossless-Claw, and Honcho, or a unifying facade/orchestrator over them?
2. Should implementation be Python or TypeScript/Bun?
3. Who owns embeddings, summarization, and reranking in standalone mode?
4. Are vectors in MVP?
5. Are summaries model-generated or deterministic/extractive in v0.1?
6. Does MVP import Alice's existing live QMD/Honcho/LCM stores, or start clean?
7. Does provenance auto-commit on every ingest batch or use operator-approved checkpoints?
8. Is the provenance bundle format custom JSON, git-native patch/report, or both?

## Bottom Line

Claude's bottom line:

The artifact is an excellent design study and a near-empty codebase. The most important unblock is not code. It is deciding whether MemoryCore replaces the current systems or orchestrates them. After that, write interface contracts and ship the provenance-anchored retrieval MVP before touching summarization or reasoning.
