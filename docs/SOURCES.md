# Sources

Status: scaffold.

This file tracks primary sources used to justify MemoryCore behavior.

## Source Categories

- QMD CLI behavior and query grammar
- Lossless-Claw host-tool behavior
- MCP interface assumptions
- OpenClaw caller path assumptions
- Public-safe fixture design

## QMD

Current source evidence to capture before live adapter implementation:

- installed `qmd --help` output
- command-specific help for `query`, `search`, `vsearch`, `get`, and `multi-get`
- output shape examples using public-safe local fixtures or synthetic corpus

## Lossless-Claw

Current source evidence to capture before live adapter implementation:

- available host tool names and input/output shapes
- behavior of grep/describe/expand-query style calls
- verification limits for summary-backed versus message-backed evidence

## MCP

Current source evidence to capture before server implementation:

- expected tool registration shape
- request/response serialization rules
- local tool error behavior

## OpenClaw

OpenClaw integration remains gated by
`docs/OPENCLAW_INTEGRATION_SMOKE_PLAN.md`.

