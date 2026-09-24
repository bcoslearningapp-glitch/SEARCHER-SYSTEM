# AI Orchestration (planned — Phase 3)

Principle: the LLM may propose; the application decides whether a proposal can mutate canonical state (PRD §48).

- `modules/ai_gateway`: `AIProvider` interface (generate_structured, reason, tool_loop, analyze_context, summarize, healthcheck, capabilities) with Anthropic and OpenAI adapters. Provider SDK imports are allowed only here (enforced by architecture test).
- Controlled tools (FR-AI-TOOL-003) run server-side with policy checks; providers never get DB credentials or filesystem access.
- Structured proposals are validated against schemas before any mutation; failures surface or retry without partial writes (FR-ORCH-001/002, NFR-REL-003). Background execution uses the job runner (ADR-003).
- Every material AI action records provider, model, template version, supplied entity IDs and timestamp; the audit layer already enforces this for AI actors (ADR-004).
