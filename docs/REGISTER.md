# Product Register — Engram / MemoryCore (EN-)

QTrellis register. Rules: ~/.claude/skills/qtrellis/SKILL.md
Stable = UCXM has no − and no ?. Scores are lazy and must carry reasons.

## Register

| ID | Item (≤5 words) | From | Status | UCXM | Proof | Note |
|----|-----------------|------|--------|------|-------|------|
| EN-001 | Fixture-first public skeleton | — | built | | docs/adr/0001-fixture-first-public-skeleton.md | theme: Trust; founding decision |
| EN-002 | Content-sparse persistence contract | EN-001 | built | | docs/adr/0002-content-sparse-audit-provenance.md | pointers at rest, never prose |
| EN-003 | Request result error contracts | EN-001 | built | | schemas/request.schema.json | shared shape for all surfaces |
| EN-004 | Backend registry and router | EN-003 | built | | memorycore/registry_router.py | intent routing, health-aware |
| EN-005 | Verification state vocabulary | EN-002 | built | | memorycore/verification_state.py | verified/stale/missing/unsupported/unknown |
| EN-006 | Provenance pointer ledger | EN-002 | built | | memorycore/provenance_ledger.py | pointer-first records |
| EN-007 | Content-sparse audit log | EN-002 | built | | memorycore/audit_log.py | deny-listed private fields |
| EN-008 | QMD adapter with live-local | EN-004 | built | | memorycore/qmd_adapter.py | ADR-0003 allowlisted CLI boundary |
| EN-009 | LCM host-bridge adapter | EN-004 | built | | memorycore/lcm_adapter.py | ADR-0004; fixture plus bridge protocol |
| EN-010 | CLI developer surface | EN-003 | built | | memorycore/cli.py | search get verify health audit eval |
| EN-011 | MCP surface and server | EN-003 | built | | memorycore/mcp_server.py | FastMCP stdio/sse/http |
| EN-012 | Public-safe eval runner | EN-001 | built | | memorycore/eval.py | 20 validators, CI on push |
| EN-013 | Caching memory router | — | built | | memorycore/cache_router.py | theme: Cache; SQLite as provenance anchor |
| EN-014 | OpenClaw cache API tools | EN-013 | built | | docs/CACHE_API_OPENCLAW.md | remember recall cache_search flush |
| EN-015 | Live-local backend mode switch | EN-008 | built | | scripts/validate_mvp_live_mode.py | MEMORYCORE_BACKEND_MODE; fixture default |
| EN-016 | Transient content write-through | EN-013 | built | | docs/adr/0005-transient-content-write-through.md | proven against real QMD 2026-07-04 |
| EN-017 | Public repo with CI | EN-001 | built | | .github/workflows/ci.yml | github.com/openreflect org, leak check run |
| EN-018 | Real backend-proof verification | GAP-001 | built | +00+ | scripts/validate_mvp_real_verify.py | U: core freshness promise; M: deterministic CLI read-back; proven on real index 2026-07-05 |
| EN-019 | LCM callback write transport | RISK-001 | built | +000 | scripts/validate_mvp_callback_delivery.py | U: unlocks transcript writes; delivery instruction + confirm tool, simulated executor validated |
| EN-020 | JSONL local file backend | EN-013 | built | | scripts/validate_mvp_jsonl_backend.py | zero-dependency third backend; memory_type local, write-through + hash verify in every mode; git-native provenance candidate |
| EN-021 | Attributed multi-backend recall | EN-013 | concept | | docs/CACHING_MEMORY_ROUTER.md | router becomes synthesizer: fan-out reads, attributed merge; design merge contract before OG-003 envelope freezes |
| RISK-001 | LCM bridge cannot cross MCP | EN-009 | superseded | | docs/AGENT_CONTEXT.md | resolved by EN-019 callback decision |
| RISK-002 | Failed write-through drops content | EN-016 | concept | | docs/adr/0005-transient-content-write-through.md | by design; spool fallback if painful |
| RISK-003 | OpenClaw smoke awaits approval | EN-011 | superseded | | docs/evals/EVAL-012_OPENCLAW_SMOKE_RUN_NOTE.md | hard stop lifted 2026-07-17; staged glasshouse execution recorded in run note |
| RISK-004 | OpenClaw stock memory-core collision | EN-011 | concept | | docs/evals/EVAL-012_OPENCLAW_SMOKE_RUN_NOTE.md | OpenClaw 2026.7.1 ships stock plugin id memory-core; naming/brand overlap with MemoryCore |
| EN-022 | Delivery executor plugin scaffold | EN-019 | concept | | docs/evals/EVAL-012_OPENCLAW_SMOKE_RUN_NOTE.md | glasshouse-only tool-plugin skeleton (memorycore_deliver); ingest stubbed pending context-engine binding |
| EN-023 | EVAL-012 OpenClaw smoke passed | EN-011 | built | | docs/evals/EVAL-012_OPENCLAW_SMOKE_RUN_NOTE.md | live OpenClaw agent drove 4-call fixture set 2026-07-17; audits corroborated; MVP verdict complete |
| EN-024 | Local provenance viewer | IDEA-008 | built | | memorycore/viewer.py | memory receipts dashboard: verification badges, backend attribution, per-record receipt drilldown, audit trail; content-sparse; `memorycore viewer` |
| EN-025 | Alice customer-zero adoption | EN-023 | concept | | docs/REGISTER.md | step 1 (2026-07-17): memorycore attached as MCP server to the working Claude Code session; OpenClaw config untouched; observe real usage before deeper integration |
| EN-026 | Operator console audited controls | EN-024 | built | | scripts/validate_mvp_operator_console.py | backend on/off, routing matrix (mirroring via multi-check), mode switch, flush/verify-all/forget; config entries not code constants; reserved classes for future systems; declared-no-adapter degrades honestly; every action audited as operator_ui |
| EN-027 | Content reveal live hash proof | EN-026 | built | | scripts/validate_mvp_operator_console.py | live-server only, on-demand, hash computed in front of the operator, reads receipted as content_access; snapshots stay content-free |
| EN-028 | Console search and filters | EN-024 | built | | memorycore/viewer.py | memory table text search + state/backend/type filters, client-side |
| EN-029 | Audit explorer filters | EN-024 | built | | memorycore/viewer.py | filter trail by operation, client surface, backend, text; deeper history |
| EN-030 | Activity trend charts | EN-024 | built | | memorycore/viewer.py | memories over time + audit activity sparklines, dataviz-validated |
| EN-031 | Config history timeline | EN-026 | built | | memorycore/viewer.py | render operator_ui config receipts as who-changed-what-when view |
| EN-032 | Declare backend form | EN-026 | built | | scripts/validate_mvp_operator_console.py | populate reserved classes from the UI; new entries start disabled |
| EN-033 | Evidence pack export | EN-024 | built | | scripts/validate_mvp_operator_console.py | one-click content-sparse pack: record receipt + related audit + integrity hash; FR-012 in local clothes |
| GAP-001 | Verify echoes caller assertion | EN-005 | superseded | | memorycore/cli.py | closed by EN-018; fixture echo remains contract-only |
| GAP-002 | No flush retry deadletter | EN-013 | concept | | docs/AGENT_CONTEXT.md | failed records dead-end forever |
| GAP-003 | Request ids collide | EN-011 | concept | | docs/MCP_HANDOFF.md | req_mcp_search every call |
| GAP-004 | No remember idempotency policy | EN-013 | concept | | docs/AGENT_CONTEXT.md | timestamp in id duplicates repeats |
| GAP-005 | SQLite WAL not enabled | EN-013 | concept | | docs/AGENT_CONTEXT.md | concurrent MCP plus CLI writers |
| GAP-006 | Content search misses local memories | EN-020 | superseded | | scripts/validate_mvp_jsonl_backend.py | closed by cache_search jsonl content fan-out with attribution (first EN-021 slice) |
| GAP-007 | Verify tool description misleads clients | EN-018 | superseded | | memorycore/mcp_surface.py | closed: description now states jsonl record verify is real every mode |
| EN-034 | Steel console E2E sweep | EN-026 | built | | scripts/validate_local_console_e2e.mjs | 25 checks through a real browser over CDP: every control, filter, reveal+hash, pack, declare, forget; local-only eval; found and fixed declare-form wipe on live re-render |
| EN-035 | gbrain knowledge backend | EN-013 | built | | scripts/validate_mvp_gbrain_adapter.py | fourth backend, first knowledge_brain occupant (garrytan/gbrain, npm 1.3.1): capture-receipt contract (slug+hash), knowledge memory type routed, fixture-proven; live capture shell-out is the next inch |
| GAP-009 | Interrupted controls leave dirty state | EN-026 | superseded | | memorycore/viewer.py | closed by audited reset_config escape hatch (issue #1) |
| GAP-010 | Table search ignores memory content | EN-028 | superseded | | memorycore/viewer.py | closed by live content-search merge with badge and honest empty state (issue #2) |
| GAP-008 | Stale MCP server after upgrade | EN-026 | concept | | docs/REGISTER.md | long-lived server processes run pre-upgrade code; config honored per-call but modules load per-process; found live 2026-07-18 when a disabled backend accepted a write from the stale session server; mitigation: restart/reconnect servers after upgrades, consider version stamp in results |

## Ideas

| ID | Item (≤5 words) | From | Status | UCXM | Proof | Note |
|----|-----------------|------|--------|------|-------|------|
| IDEA-001 | Git-native provenance engine | EN-006 | idea | | | commits diffs blame evidence bundles |
| IDEA-002 | Re-verification TTL policy | GAP-001 | idea | | | verified stamps should degrade |
| IDEA-003 | LCM ingest write-through | EN-016 | idea | | | needs RISK-001 transport decision |
| IDEA-004 | Honcho peer memory adapter | EN-004 | idea | | | peer/session reasoning backend |
| IDEA-005 | gbrain knowledge adapter | EN-004 | idea | | | graduated to EN-035 |
| IDEA-006 | Memory fabric substrates | EN-004 | idea | | | Notion Drive S3 spreadsheets |
| IDEA-007 | HTTP API and SDK | EN-003 | idea | | | REST surface, typed primitives |
| IDEA-008 | Operator UI provenance drilldown | EN-006 | idea | | | summary DAG viewer, doctor |
| IDEA-009 | Mirroring splitting policy config | EN-013 | idea | | | flush policies beyond routing map |
| IDEA-010 | Backup migration dry-run | EN-013 | idea | | | export pointers, verify hashes |
| IDEA-011 | pytest bridge | EN-012 | idea | | | wrap validators for pytest runners |
| IDEA-012 | Cost token diagnostics | EN-012 | idea | | | per-backend contribution views |
| IDEA-013 | Register IDs as provenance anchors | EN-006 | idea | | | memory records cite EN rows |
| IDEA-014 | Indexing transcript reasoning engines | — | idea | | | separate product layer per spec |
| IDEA-015 | Fan-out parallel recall | EN-021 | idea | | | one query, all capable backends |
| IDEA-016 | Attributed merge contract | EN-021 | idea | | | per-item backend, pointer, verification, relevance |
| IDEA-017 | Cross-backend identity mapping | EN-021 | idea | | | mirrored records recognized as one memory |
| IDEA-018 | Pending-state toasts | EN-026 | idea | | | built: immediate working toast replaced by result (issue #3) |
| IDEA-019 | Receipt-backed backend benchmarking | EN-007 | idea | | | per-backend latency, verification pass rate, staleness rate, flush failures from lived audit traffic; comparative scorecards across memory systems |
| IDEA-020 | Agent-driven backend discovery | EN-032 | idea | | | LLM scans npm/GitHub for memory-shaped systems, classifies into backend classes, proposes declarations for operator approval |
| IDEA-021 | Agent-assisted adapter onboarding | EN-035 | idea | | | agent drafts adapter contract, fixtures, and validator from a discovered system's write model — the gbrain loop, automated |
