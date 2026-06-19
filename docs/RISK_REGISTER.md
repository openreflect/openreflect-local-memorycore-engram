# Risk Register

Status: scaffold.

## Active Risks

### RISK-001: Fixture Confidence Overclaiming

Risk: Public-safe fixture evals can make live backend readiness look stronger
than it is.

Mitigation: Keep live/local evals skipped and named until executable live checks
exist.

### RISK-002: Private Data Leakage

Risk: Audit, provenance, logs, fixtures, or examples may accidentally contain
private content.

Mitigation: Keep records content-sparse by default and add leak checks before
public release.

### RISK-003: Stale Backend Indexes

Risk: QMD or other memory indexes may return plausible but stale context.

Mitigation: Verification state must distinguish fresh, stale, unsupported, and
unknown.

### RISK-004: Ambiguous LCM Verification

Risk: Lossless-Claw recall can provide strong conversational evidence without
always proving freshness or completeness.

Mitigation: Preserve cited IDs and explicitly mark inferred versus source-backed
claims.

### RISK-005: Shell-Out Boundary

Risk: Future live QMD adapter may execute subprocess commands unsafely.

Mitigation: Define allowlisted commands, bounded arguments, timeouts, and
content-sparse error handling before live mode.

### RISK-006: Retrieved Content Treated As Instructions

Risk: A caller may place retrieved snippets, source content, summaries, or
answers into a prompt without preserving the distinction between evidence and
instructions.

Mitigation: Contract and threat model state that retrieved content is untrusted
data. Validation checks keep that rule visible before live adapters expand.

### RISK-007: Contract Schema Drift

Risk: Adapter output may gain fields before the public contract and validation
surface describe whether those fields are response-only, persistence-safe, or
forbidden by default.

Mitigation: `MEMORYCORE_CONTRACT_SECURITY` validates representative
request/result/error shapes against canonical schemas and checks persistence
leak deny lists.

### RISK-008: Host Bridge Availability Ambiguity

Risk: A Lossless-Claw host bridge may be missing, partially injected, timed out,
or able to recall content without proving the cited summary/message still
exists.

Mitigation: The LCM adapter returns structured unavailable/timeout outcomes and
only treats `lcm_describe` pointer existence as verification proof. Grep and
expand-query recall remain `unknown` unless the host separately verifies the
pointer.
