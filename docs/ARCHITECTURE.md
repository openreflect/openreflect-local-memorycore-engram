# Engram Architecture

## Memory-core flow

```text
raw source artifact
  -> normalized memory record
  -> git commit or version pointer
  -> semantic index reference
  -> recall
  -> provenance verification
```

## Git-native primitives

- Commit: durable decision or observation point.
- Branch: alternate reasoning path or experiment.
- Diff: change in understanding.
- Tag: semantic or release marker.
- Blame/log: provenance and staleness inspection.

## Recall boundary

Semantic systems can retrieve candidates. Engram verifies whether those candidates still align with durable source state.

## Integration boundary

Engram should expose source-backed memory records to OpenReflect and other insight agents without requiring those systems to own the git substrate directly.
