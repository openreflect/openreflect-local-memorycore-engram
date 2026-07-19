# Managed Extractive Memory Landscape — Deep Research Report

Date: 2026-07-19. Method: deep-research harness — 104 agents, 5 search
angles, source fetch + falsifiable-claim extraction, 3-vote adversarial
verification per claim (2/3 refutes kill). Only surviving claims below.
Commissioned for IDEA-023 provider selection (EN-036 adapter track).

## Question

Survey the current (2025–2026) landscape of managed/extractive agent memory services that automatically generate user-scoped memory facts from conversations and retrieve them by similarity — the concept prototyped by Google Vertex AI Agent Engine Memory Bank. Cover: (1) Vertex AI Memory Bank itself — current GA status, capabilities, pricing model, API shape; (2) direct competitors and alternatives: AWS Bedrock AgentCore Memory, mem0, Zep, Letta (MemGPT), Honcho by Plastic Labs, OpenAI's memory APIs if any, and other notable open-source or hosted extractive-memory services; (3) for each: hosting model (managed cloud vs self-hostable), memory generation approach (LLM extraction, consolidation), retrieval (similarity, scoping), provenance/audit capabilities, MCP support, maturity/adoption signals, and pricing where published; (4) a comparative assessment of which are the strongest candidates to serve as a "managed extractive memory" backend behind a local memory-virtualization router (MemoryCore/Engram) that requires: a callable API, user scoping, pointer-stable memory ids, and ideally content hashes or immutable ids for independent verification. Conclude with a ranked recommendation of the top 2–3 candidates for adapter integration.

## Verified Summary

The 2025-2026 managed extractive-memory landscape, as verified here, is anchored by two hyperscaler services: Google's Vertex AI Agent Engine Memory Bank (public preview July 9, 2025; since rebranded under the Gemini Enterprise Agent Platform) and AWS Bedrock AgentCore Memory (introduced at AWS Summit NYC July 2025, GA October 2025). Both are fully managed, cloud-only pipelines that use LLM-driven extraction plus asynchronous consolidation to turn conversations into discrete, user-scoped memory records retrieved by embedding similarity, and both expose direct callable APIs with pointer-stable record identifiers — satisfying MemoryCore/Engram's core adapter requirements of callable API, user scoping, and stable ids. Neither publishes content hashes, but Memory Bank uniquely provides automatic immutable per-mutation memory revisions with rollback, the strongest provenance primitive found, while AgentCore offers finer pricing granularity and strategy-level control. Ranked recommendation for adapter integration: (1) Vertex AI Memory Bank — best provenance (immutable revisions approximate independent verification), first-class scope isolation, and cheap operations-based pricing; (2) AWS AgentCore Memory — close second with per-record ids, namespace scoping, and semantic retrieval, but no documented revision/audit history. No claims about mem0, Zep, Letta, Honcho, or OpenAI memory APIs survived adversarial verification, so a third-ranked candidate cannot be responsibly named from this evidence base.

## Findings (adversarially verified)

### 1. [high confidence, vote 3-0 (x3 merged claims)]

Vertex AI Memory Bank launched in public preview on July 9, 2025 as a managed service of Vertex AI Agent Engine, and by mid-2026 has been reorganized/rebranded as 'Agent Platform Memory Bank' under Google's Gemini Enterprise Agent Platform; Google positions it as a fully managed service covering the entire extractive-memory pipeline: generation, storage, retrieval, and embedding.

**Evidence:** Google blog (2025-07-09): 'Announcing Vertex AI Agent Engine Memory Bank available for everyone in preview... the newest managed service of the Vertex AI Agent Engine.' Current docs serve 'Agent Platform Memory Bank' under Gemini Enterprise Agent Platform ('formerly Vertex AI'). Pricing page: 'Memory Bank is a fully managed service for agent memory generation, storage, retrieval and embedding.' Explicit GA status was not verified — public preview is the last confirmed lifecycle stage.

- https://cloud.google.com/blog/products/ai-machine-learning/vertex-ai-memory-bank-in-public-preview
- https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/overview
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank
- https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing

### 2. [high confidence, vote 3-0 (x2 merged claims)]

Memory Bank generates memories via distinct LLM-driven (Gemini) extraction and consolidation steps: it analyzes conversation history from Agent Engine Sessions to extract key facts/preferences, then asynchronously consolidates new information with existing memories in the background — resolving contradictions and deduplicating — with continuous event ingestion triggering generation via configurable batching rules.

**Evidence:** Docs: 'Extract only the most meaningful information from source data to persist as memories'; 'Consolidate newly extracted information with existing memories'; 'Generate memories in the background.' Blog: 'Using Gemini models, Memory Bank can analyze a user's conversation history... to extract key facts, preferences, and context... consolidate it with existing memories, resolving contradictions... asynchronously in the background.' Nuance: generation is triggered by a GenerateMemories API call (developer-initiated, optionally blocking), not fully automatic.

- https://cloud.google.com/blog/products/ai-machine-learning/vertex-ai-memory-bank-in-public-preview
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/generate-memories

### 3. [high confidence, vote 3-0 (x2 merged claims)]

Memory Bank exposes a direct SDK/API surface requiring no agent framework: memories.generate takes a session source (vertex_session_source) plus a free-form scope dictionary (documented max 5 key-value pairs, no '*' characters) that defaults to {"user_id": session.user_id}; LLM consolidation only merges memories sharing an identical scope.

**Evidence:** API shape: client.agent_engines.memories.generate(name=..., vertex_session_source={"session": session.response.name}, scope=SCOPE, config={"wait_for_completion": True}). Docs: 'Only memories with the same scope are considered for consolidation'; 'Defaults to {"user_id": session.user_id}.' Caveat: the '5 key-value pairs' phrasing was dropped in Google's July 2026 docs restructure (no source contradicts it); the user_id default applies specifically to Sessions-sourced generation.

- https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/quickstart-api
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/generate-memories

### 4. [high confidence, vote 3-0 (x2 merged claims)]

Memory Bank retrieval directly satisfies Engram's user-scoping requirement: memories are organized by developer-defined scope (e.g. user ID), scope is immutable and exact-match at retrieval, and callers can either fetch all memories in a scope or run embedding-based similarity search (vectors over the memories' fact text, top-k, distance-sorted) — with both consolidation and retrieval isolated to a specific identity.

**Evidence:** 'Retrieve memories using similarity search that is scoped to a specific identity'; 'Only memories that have the exact same scope (independent of order) as the retrieval request are returned'; 'A memory's scope is defined when the memory is generated or created and is immutable.' Similarity search is optional — scope-only RetrieveMemories returns all memories in that scope. Scope is a key-value dict convention rather than a first-class identity primitive.

- https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/overview
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/fetch-memories
- https://cloud.google.com/blog/products/ai-machine-learning/vertex-ai-memory-bank-in-public-preview

### 5. [high confidence, vote 3-0 (x2 merged claims)]

Memory Bank provides the strongest verified provenance/audit primitive in this survey: each memory has a stable fully-qualified resource name (projects/.../reasoningEngines/.../memories/{id}) carrying content in a plain-text 'fact' field, and every mutation automatically creates an immutable child MemoryRevision — giving a complete version history of extraction/consolidation steps plus a RollbackMemory operation. No content hashes are documented; the id is pointer-stable but the fact content under it can change via consolidation, and consolidation can also delete memories.

**Evidence:** 'Automatically create and maintain memory revisions which allow you to inspect how memories transform as new information is ingested'; 'Memory revision resources provide a complete version history of a memory resource across all mutation operations'; 'A new, immutable revision is automatically saved each time that the memory is created or modified.' Qualifications: revisions default to a 365-day TTL, can be disabled per-instance/per-request, so not a permanent audit log by default; ids can dangle after consolidation-driven deletion.

- https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/overview
- https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/quickstart-api
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/fetch-memories

### 6. [high confidence, vote 3-0]

Memory Bank's published pricing is operations- and storage-based, not per-memory: Agent Storage at $0.30/GiB-month (including revisions), read API requests at $0.085 (1 Agent Compute vCPU-h) per 3 million operations, write API requests at $0.085 per 1 million operations, with generation/embedding model tokens billed separately under their model SKUs. This billing structure commences September 1, 2026.

**Evidence:** Pricing page verified live 2026-07-19: 'Storage: Total data stored (including revisions), billed as Agent Storage ($0.30/GiB-month)... Read API requests: 1 Agent Compute vCPU-h ($0.085) for every 3 million read operations... Write API requests: 1 Agent Compute vCPU-h ($0.085) for every 1 million write operations.' Note: the inference that the service is free before Sept 1, 2026 was REFUTED (0-3) — current pre-commencement billing terms are unverified.

- https://cloud.google.com/vertex-ai/pricing
- https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing

### 7. [high confidence, vote 3-0 (x2 merged claims)]

AWS Bedrock AgentCore Memory is a fully managed, cloud-only (not self-hostable) agent memory service and the direct managed competitor to Vertex AI Memory Bank: introduced in preview at AWS Summit New York City 2025 (July), GA October 13, 2025, handling short-term session context (raw events) and long-term cross-session knowledge retention.

**Evidence:** 'AgentCore Memory is a fully managed service... a simple and powerful way to handle both short-term context and long-term knowledge retention without the need to build or manage complex infrastructure.' No source offers a self-hosted deployment; the 'self-managed strategy' only customizes extraction pipelines inside the managed service. Third-party comparisons uniformly treat AgentCore Memory and Vertex Memory Bank as directly comparable managed extractive-memory services.

- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html
- https://aws.amazon.com/blogs/machine-learning/amazon-bedrock-agentcore-memory-building-context-aware-agents/
- https://aws.amazon.com/about-aws/whats-new/2025/10/amazon-bedrock-agentcore-available/

### 8. [high confidence, vote 3-0 (x6 merged claims)]

AgentCore Memory's extraction is strategy-driven and opt-in: long-term records are generated only when memory strategies are explicitly attached via CreateMemory/UpdateMemory (no strategies = no extraction); once enabled, built-in strategies (semantic facts, user preferences, summaries, episodic) run fully managed with predefined algorithms on raw events ingested via CreateEvent, through an asynchronous background pipeline with two explicit steps — extraction and consolidation — retaining only distilled insights (not raw transcripts) across sessions.

**Evidence:** 'If no strategies are specified, long-term memory records will not be extracted for that memory'; 'AgentCore handles all memory extraction and consolidation automatically with predefined algorithms... No configuration required beyond basic trigger settings'; 'Long-term memory generation is an asynchronous process that runs in the background... Extraction... Consolidation'; 'Long-term memory preserves only the key insights such as summaries of the conversations, facts and knowledge, or user preferences.' Custom/self-managed strategies can write arbitrary records, so 'only distilled insights' describes built-in behavior, not a hard platform constraint.

- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-strategies.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-types.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html

### 9. [high confidence, vote 3-0 (x2 merged claims)]

AgentCore Memory satisfies Engram's retrieval and pointer-stability requirements: extracted memories are discrete records with individual memoryRecordIds, fetchable via GetMemoryRecord/ListMemoryRecords, and retrieved by semantic similarity search via RetrieveMemoryRecords (searchQuery + topK, namespace/actorId scoping, relevance-scored results, optional metadata filters). AWS does not explicitly guarantee record-id immutability across the async consolidation step, and no content hashes are documented.

**Evidence:** 'Extracted memories are stored as memory records and can be accessed using the GetMemoryRecord, ListMemoryRecords, or RetrieveMemoryRecords operations'; 'The RetrieveMemoryRecords operation... performs a semantic search to find memory records that are most relevant to the query.' GetMemoryRecord takes a required memoryRecordId; responses return memoryRecordSummaries ordered by relevance with numeric scores.

- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-types.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/API_RetrieveMemoryRecords.html

### 10. [high confidence, vote 3-0 (x3 merged claims)]

AgentCore Memory pricing (live as of 2026-07-19) is per-event/per-record/per-retrieval: $0.25 per 1,000 new events (short-term); long-term storage at $0.75 per 1,000 records/month (built-in strategies) or $0.25 per 1,000 records/month (built-in-with-override or self-managed, plus separate model usage at standard Bedrock rates), billed hourly assuming a 31-day month; retrieval at $0.50 per 1,000 memory record retrievals.

**Evidence:** Pricing table verified live 2026-07-19: '$0.25 per 1,000 new events'; '$0.75 per 1000 memory records stored per month... $0.25 per 1000 memory records stored per month... Billed hourly assuming a 31 day month'; '$0.50 per 1000 memory record retrievals.' Independently corroborated by third-party pricing breakdowns (Cloud Burn, 2026-05-14).

- https://aws.amazon.com/bedrock/agentcore/pricing/

### 11. [medium confidence, vote ?]

Ranked recommendation for a MemoryCore/Engram adapter backend: (1) Vertex AI / Agent Platform Memory Bank — the only surveyed service with an automatic immutable revision history plus rollback, giving the closest verified approximation to independent verification absent content hashes, plus exact-match scope isolation, stable resource names, and low-cost operations-based pricing; (2) AWS AgentCore Memory — a strong second with individually addressable record ids, namespace/actor scoping, semantic retrieval, and transparent per-record pricing, but no documented revision/audit primitive and no id-immutability guarantee across consolidation. Neither provides content hashes, so Engram-side hashing of fetched fact text at ingest (re-verified via GetMemoryRecord / memories.get) is the recommended verification pattern for both. A third candidate cannot be named: no claims about mem0, Zep, Letta, Honcho, or OpenAI memory APIs survived verification.

**Evidence:** Synthesized comparative judgment derived from the high-confidence per-service findings above, not itself a directly verified claim. Both services meet the hard requirements (callable API without framework lock-in, user scoping, pointer-stable ids); the ranking turns on Memory Bank's revisions/rollback provenance ('A new, immutable revision is automatically saved each time that the memory is created or modified') versus AgentCore's absence of any documented equivalent. Marked medium because it is an inference and because the competitive field beyond the two hyperscalers is unverified.

- https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-types.html
- https://aws.amazon.com/bedrock/agentcore/pricing/
- https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing
