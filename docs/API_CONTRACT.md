# API Contract

Status: scaffold.

MemoryCore exposes one contract across CLI, MCP-shaped calls, and future
runtime callers: request in, normalized result out, structured error on failure.

## Contract Goals

- Keep backend-specific behavior behind adapters.
- Preserve provenance and verification state without storing private content.
- Make CLI and MCP outputs equivalent for the same request.
- Keep error shapes stable enough for agents to recover programmatically.

## Request Contract

Canonical schema: `schemas/request.schema.json`.

Required fields and allowed operations should be treated as public interface.
Changes require a schema update, fixture update, eval update, and migration note.

## Result Contract

Canonical schema: `schemas/result.schema.json`.

Every successful result should include:

- request identity
- operation
- backend identity
- normalized result records
- provenance pointer fields when available
- verification state when supported or explicitly unsupported

## Error Contract

Canonical schema: `schemas/error.schema.json`.

Errors should be structured, machine-readable, and content-sparse. Avoid leaking
backend exception text if it may contain local paths, snippets, secrets, or
private corpus material.

## CLI and MCP Equivalence

The CLI and MCP-shaped surface should return the same normalized data model.
Differences should be limited to transport wrapper details.

## Versioning Notes

No external versioning scheme is defined yet. Until it is, prefer additive
changes and mark breaking contract changes in `docs/MIGRATION_PLAN.md`.

