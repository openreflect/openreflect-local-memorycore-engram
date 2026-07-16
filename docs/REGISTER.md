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
| EN-020 | JSONL local file backend | EN-013 | concept | | docs/CACHING_MEMORY_ROUTER.md | zero-dependency default backend; append-only, git-trackable, git-native provenance candidate; third backend proves abstraction |
| RISK-001 | LCM bridge cannot cross MCP | EN-009 | superseded | | docs/AGENT_CONTEXT.md | resolved by EN-019 callback decision |
| RISK-002 | Failed write-through drops content | EN-016 | concept | | docs/adr/0005-transient-content-write-through.md | by design; spool fallback if painful |
| RISK-003 | OpenClaw smoke awaits approval | EN-011 | deferred | | docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md | EVAL-012 hard stop; operator lifts |
| GAP-001 | Verify echoes caller assertion | EN-005 | superseded | | memorycore/cli.py | closed by EN-018; fixture echo remains contract-only |
| GAP-002 | No flush retry deadletter | EN-013 | concept | | docs/AGENT_CONTEXT.md | failed records dead-end forever |
| GAP-003 | Request ids collide | EN-011 | concept | | docs/MCP_HANDOFF.md | req_mcp_search every call |
| GAP-004 | No remember idempotency policy | EN-013 | concept | | docs/AGENT_CONTEXT.md | timestamp in id duplicates repeats |
| GAP-005 | SQLite WAL not enabled | EN-013 | concept | | docs/AGENT_CONTEXT.md | concurrent MCP plus CLI writers |

## Ideas

| ID | Item (≤5 words) | From | Status | UCXM | Proof | Note |
|----|-----------------|------|--------|------|-------|------|
| IDEA-001 | Git-native provenance engine | EN-006 | idea | | | commits diffs blame evidence bundles |
| IDEA-002 | Re-verification TTL policy | GAP-001 | idea | | | verified stamps should degrade |
| IDEA-003 | LCM ingest write-through | EN-016 | idea | | | needs RISK-001 transport decision |
| IDEA-004 | Honcho peer memory adapter | EN-004 | idea | | | peer/session reasoning backend |
| IDEA-005 | gbrain knowledge adapter | EN-004 | idea | | | knowledge-brain pages |
| IDEA-006 | Memory fabric substrates | EN-004 | idea | | | Notion Drive S3 spreadsheets |
| IDEA-007 | HTTP API and SDK | EN-003 | idea | | | REST surface, typed primitives |
| IDEA-008 | Operator UI provenance drilldown | EN-006 | idea | | | summary DAG viewer, doctor |
| IDEA-009 | Mirroring splitting policy config | EN-013 | idea | | | flush policies beyond routing map |
| IDEA-010 | Backup migration dry-run | EN-013 | idea | | | export pointers, verify hashes |
| IDEA-011 | pytest bridge | EN-012 | idea | | | wrap validators for pytest runners |
| IDEA-012 | Cost token diagnostics | EN-012 | idea | | | per-backend contribution views |
| IDEA-013 | Register IDs as provenance anchors | EN-006 | idea | | | memory records cite EN rows |
| IDEA-014 | Indexing transcript reasoning engines | — | idea | | | separate product layer per spec |
