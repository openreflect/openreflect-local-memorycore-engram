# Threat Model

Status: MVP guardrail.

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

Controls:

- Treat `snippet`, `content`, `answer`, and cited transcript/source text as
  untrusted data even when they come from a trusted local backend.
- Preserve host/runtime/developer instructions above retrieved memory content
  in prompt assembly.
- Do not let retrieved content change backend selection, verification state,
  tool permissions, write paths, or external-action policy.
- If a retrieved item contains text that looks like an instruction, quote or
  summarize it as evidence and keep the caller's original task as the governing
  instruction.

### Audit or Provenance Leakage

Audit and provenance records must avoid private snippets, transcript text,
secrets, local-only identifiers, and raw backend output unless explicitly
approved for a local-only artifact.

Controls:

- Persist pointer ids and bounded operational metadata by default.
- Forbid raw `snippet`, `content`, `citations`, `summary`, `answer`, and `text`
  fields in audit and provenance records by default.
- Do not persist raw backend exception text; map failures to structured
  `code`, `category`, and content-sparse details.
- Keep public-safe evals synthetic and fixture-only.

### Unsafe Live Backend Invocation

Future live adapters must use bounded commands, fixed argument construction,
timeouts, and structured errors.

### Verification Misrepresentation

Unsupported or unknown freshness must not be presented as verified.

Controls:

- Use `unsupported` when a backend cannot verify a pointer type.
- Use `unknown` when verification was not attempted or evidence is
  insufficient.
- Use `missing` only when the backend reports the pointer cannot be resolved.
- Use `verified` only after a source-contact path confirms the referenced
  pointer still exists under the expected backend.

### Schema Drift Before Live Adapter Expansion

Schemas can lag behind normalized adapter output, causing future callers to
depend on undocumented fields or miss new persistence risks.

Controls:

- Contract/security eval validates representative request/result/error shapes
  against the canonical schemas.
- Any field that may carry retrieved data is documented as immediate response
  data, not persistence-safe metadata.
- New adapter fields require a schema update and a matching public-safe
  validation check before live expansion.

## Required Controls

- content-sparse audit default
- explicit verification state
- fixture-only public eval mode
- hard stop around EVAL-012
- local-only live backend boundary docs
- retrieved content treated as untrusted data
- schema-backed contract/security eval before live adapter expansion
