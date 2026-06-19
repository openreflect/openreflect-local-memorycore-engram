# Observability

Status: scaffold.

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
- backend id
- backend mode
- status
- error code
- provenance pointer id
- verification state
- elapsed time

## Fields To Avoid By Default

- raw snippets
- transcript text
- full summaries
- credentials
- local absolute paths when public-safe output is possible
- raw backend exception text

## Health States

- `ok`
- `degraded`
- `unavailable`
- `fixture-only`
- `not-run-hard-stop`
- `unknown`

