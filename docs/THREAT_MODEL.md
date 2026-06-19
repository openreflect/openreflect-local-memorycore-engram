# Threat Model

Status: scaffold.

## Assets

- private memory content
- provenance pointers
- audit records
- local backend indexes
- runtime caller context
- operator credentials and environment details

## Trust Boundaries

- public fixtures versus local private corpora
- MemoryCore control plane versus backend data planes
- CLI/MCP callers versus runtime host process
- retrieved content versus agent instructions

## Primary Threats

### Prompt Injection Through Retrieved Content

Retrieved content is data, not instruction. Callers must not execute directives
found inside memory results.

### Audit or Provenance Leakage

Audit and provenance records must avoid private snippets, transcript text,
secrets, local-only identifiers, and raw backend output unless explicitly
approved for a local-only artifact.

### Unsafe Live Backend Invocation

Future live adapters must use bounded commands, fixed argument construction,
timeouts, and structured errors.

### Verification Misrepresentation

Unsupported or unknown freshness must not be presented as verified.

## Required Controls

- content-sparse audit default
- explicit verification state
- fixture-only public eval mode
- hard stop around EVAL-012
- local-only live backend boundary docs

