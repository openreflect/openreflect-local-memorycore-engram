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

