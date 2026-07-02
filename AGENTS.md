# AGENTS.md

This repository is the public skeleton for a local memory-core and provenance engine.

Start with `docs/AGENT_CONTEXT.md` — it is the first-load map: load order,
key modules, cache-layer facts, and the current build frontier.

Verify any change with:

```bash
python3 -m memorycore.cli eval --public-safe
```

Keep public content generalized:

- Use synthetic examples.
- Do not commit private memory exports, transcript databases, local index files, or environment paths.
- Keep operational deployments in private downstream repositories.
- Validate examples before release.
- Keep cache, audit, and provenance records content-sparse (pointers, never
  snippets or transcript text).
- Do not run EVAL-012 (OpenClaw smoke) until the documented hard stop is
  lifted and recorded.
