# Observability

Status: MVP guardrail.

MemoryCore observability should explain what happened without storing the memory
content itself.

## Events To Record

- request received
- backend selected
- backend unavailable
- result returned
- verification attempted
- verification unsupported
- error returned

## Fields To Prefer

- request id
- operation
- normalized intent
- client surface
- backend id
- backend mode
- status
- error code
- error category
- provenance pointer id
- result count
- result index
- verification state
- elapsed time
- event timestamp
- eval id, when emitted by validation

## Fields To Avoid By Default

- raw snippets
- raw content
- raw citations
- raw summaries or answers
- `summary`
- `answer`
- `text`
- transcript text
- source text
- prompt text
- full summaries
- credentials
- tokens
- account ids
- local absolute paths when public-safe output is possible
- raw backend exception text
- `raw_exception`

## Event Shape

Observable events should be dictionaries with bounded operational fields:

- `event_name`: one of the event names above.
- `request_id`: stable request id when available.
- `operation`: `search`, `get`, `verify`, or `health`.
- `client_surface`: caller surface when available.
- `backend_id`: selected or requested backend id when available.
- `status`: `ok`, `error`, `degraded`, `unavailable`, `fixture-only`,
  `not-run-hard-stop`, or `unknown`.
- `error_code` and `error_category`: structured error identifiers only.
- `pointer_id`: backend-native pointer id without copied source content.
- `result_count`: integer count, not result text.
- `verification_state`: canonical verification state.
- `elapsed_ms`: bounded non-negative duration.
- `timestamp`: event time.

Observability output is not a transcript, answer cache, or prompt log. If a
debug-only local artifact needs richer data, it must be explicitly local-only,
excluded from public-safe eval output, and named separately from default
observability.

## Health States

- `ok`
- `degraded`
- `unavailable`
- `fixture-only`
- `not-run-hard-stop`
- `unknown`
