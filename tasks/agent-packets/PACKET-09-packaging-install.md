# PACKET-09 - Packaging And Fresh Install

## Purpose

Make the repo easy to install, run, and validate from a fresh checkout. This packet should remove setup ambiguity without adding unnecessary runtime dependencies.

## Ownership

- Primary files/modules: packaging metadata, install docs, CI install path.
- Supporting docs/scripts: `README.md`, `.github/workflows/ci.yml`, optional `pyproject.toml`, optional `docs/RUNBOOK.md`.
- Do not touch: adapter logic, MCP server implementation, QMD collection setup, OpenClaw smoke execution.

## Context To Load

- `README.md`
- `SPEC.md`
- `.github/workflows/ci.yml`
- `docs/RUNBOOK.md`
- `memorycore/cli.py`
- current validation scripts under `scripts/`

## Work Items

- Determine whether a minimal `pyproject.toml` is warranted now.
- If warranted, add package metadata and console script entrypoints that preserve current `python3 -m memorycore.cli` behavior.
- Update README/runbook quickstart for fresh checkout, public-safe eval, and optional local-only evals.
- Update CI only if needed to test the actual install path.

## Constraints

- Do not add dependencies unless a concrete packaging or MCP entrypoint need requires one.
- Public repo docs must stay generalized and private-path-free.
- Existing direct module commands must continue to work.
- You are not alone in the codebase; coordinate if Packet 07 needs a dependency or entrypoint.

## End Eval

- Eval ID: `MEMORYCORE_PACKAGE_INSTALL`
- Command: preferred install smoke such as `python3 -m pip install -e .` then `python3 -m memorycore.cli eval --public-safe`, or a documented blocked alternative if packaging is deferred.
- Passing condition: fresh-checkout install path works and public-safe eval remains green.
- Correct blocked/skipped condition: packaging deferred with a clear reason, no broken partial metadata, and README still accurately describes direct module usage.

## Reporting Contract

Return:

- changed files
- install command tested
- eval command and result
- dependency decisions
- blockers
- assumptions
- remaining gaps
