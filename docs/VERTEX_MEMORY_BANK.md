# Vertex AI Memory Bank — Operator Setup (EN-037 / EN-038)

The `vertex_memory_bank` backend is MemoryCore's first remote extractive
memory system. The adapter (EN-037) ships installed but **disabled**, and
even when enabled it will not touch the network until an engine is
configured — content leaves the machine only when the operator has said
so twice.

## What it gives you

- `peer` memory type: user-scoped facts routed to Memory Bank.
- Stable resource-name pointers
  (`projects/{n}/locations/{loc}/reasoningEngines/{id}/memories/{id}`).
- Hash-at-observation verification: `memorycore_verify` reads the fact
  back and reports `verified`, `stale` ("fact revised by Memory Bank
  consolidation since observation" — the service keeps an immutable
  revision per mutation, so the prior state is preserved server-side),
  or `missing`.
- A live `vertex_retrieve` fanout lane: similarity retrieval within the
  configured scope, merged with per-item attribution and extraction
  source (`generated` vs `explicit`).

## One-time GCP setup

1. Authenticated `gcloud` on the host (`gcloud auth login` and
   `gcloud auth application-default login`), a project selected, and the
   `aiplatform.googleapis.com` API enabled.
2. Create a container engine (no deployed code; it exists to hold
   memories):

   ```bash
   curl -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "Content-Type: application/json" \
     "https://{loc}-aiplatform.googleapis.com/v1/projects/{project}/locations/{loc}/reasoningEngines" \
     -d '{"displayName": "engram-memorycore"}'
   ```

3. Grant the engine's service agent access to the models it calls
   (the create response names the agent as `spec.effectiveIdentity`):

   ```bash
   gcloud projects add-iam-policy-binding {project} \
     --member="serviceAccount:service-{project_number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

4. **Pin the Memory Bank models to your project.** Without this, memory
   creation can fail with a `PERMISSION_DENIED` naming an embedding
   model under a project number that is not yours:

   ```bash
   curl -X PATCH -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "Content-Type: application/json" \
     "https://{loc}-aiplatform.googleapis.com/v1/{engine}?updateMask=contextSpec.memoryBankConfig" \
     -d '{"contextSpec": {"memoryBankConfig": {
           "similaritySearchConfig": {"embeddingModel": "projects/{project}/locations/{loc}/publishers/google/models/text-embedding-005"},
           "generationConfig": {"model": "projects/{project}/locations/{loc}/publishers/google/models/gemini-2.5-flash"}
         }}}'
   ```

## MemoryCore configuration

- Engine: `MEMORYCORE_VERTEX_ENGINE` env var, or
  `backends.vertex_memory_bank.engine` in the operator config file
  (env wins). Full resource name.
- Scope: `MEMORYCORE_VERTEX_SCOPE_USER` (default `operator`) becomes the
  `user_id` scope on writes and retrievals. Scope matching is exact and
  immutable — Memory Bank's isolation boundary.
- Enable the backend in the operator console (audited), and switch to
  `live-local` mode. In fixture mode the write-through stays synthetic
  and is disclosed as `fixture-only`.
- Optional: `MEMORYCORE_GCLOUD_BIN`, `MEMORYCORE_VERTEX_TIMEOUT_SECONDS`.

## Boundary and honesty rules

Authentication rides the allowlisted `gcloud auth print-access-token`
subprocess (ADR-0003 pattern; no SDK dependency). Tokens live in process
memory per call and are never persisted. Facts appear response-only; the
cache and audit trail hold pointers and hashes. Missing configuration,
API errors, and fixture mode all degrade honestly (`BACKEND_UNAVAILABLE`
/ lane `skipped` with a reason) — never silently.

Proven live 2026-07-20: create → pointer receipt → `verified` read-back →
server-side fact revision caught as `stale` → live similarity retrieval
through the fanout lane with attribution.
