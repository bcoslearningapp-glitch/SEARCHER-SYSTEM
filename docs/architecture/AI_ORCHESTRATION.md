# AI Orchestration

Principle: the LLM may propose; the application decides whether a proposal can mutate canonical state (PRD §48).

## AI gateway (implemented — ADR-010)
- `modules/ai_gateway`: provider-neutral `AIProvider` (`generate_structured`, `healthcheck`, `capabilities`) with Anthropic, OpenAI and mock adapters. Provider SDK imports are allowed only in the adapters (architecture test).
- `service.run_structured(session, CallContext, StructuredRequest)` is the only path from domain code to a model: profile selection → disclosure policy (PRD §54) → per-task/project budget → provider → JSON-Schema validation → append-only `ai_requests` log → `AIActionRecord` for the caller's audit entry.
- Prompts: instructions in the system prompt; retrieved sources and tool output wrapped as escaped `<untrusted_source>` data; secrets redacted.
- HTTP: `GET /api/v1/ai/profiles`, `GET|PUT /api/v1/projects/{id}/ai-policy`, `GET /api/v1/projects/{id}/ai-requests`.

## Research Orchestrator (planned — issue #22)
- Controlled tools (FR-AI-TOOL-003) run server-side with policy checks; providers never get DB credentials or filesystem access.
- Structured proposals are validated before any mutation; failures surface or retry without partial writes (FR-ORCH-001/002, NFR-REL-003). Background execution uses the job runner (ADR-003).
- Every material AI action records provider, model, template version, supplied entity IDs and timestamp; the audit layer enforces this for AI actors (ADR-004).
