# AI Orchestration

Principle: the LLM may propose; the application decides whether a proposal can mutate canonical state (PRD §48).

## AI gateway (implemented — ADR-010)
- `modules/ai_gateway`: provider-neutral `AIProvider` (`generate_structured`, `healthcheck`, `capabilities`) with Anthropic, OpenAI and mock adapters. Provider SDK imports are allowed only in the adapters (architecture test).
- `service.run_structured(session, CallContext, StructuredRequest)` is the only path from domain code to a model: profile selection → disclosure policy (PRD §54) → per-task/project budget → provider → JSON-Schema validation → append-only `ai_requests` log → `AIActionRecord` for the caller's audit entry.
- Prompts: instructions in the system prompt; retrieved sources and tool output wrapped as escaped `<untrusted_source>` data; secrets redacted.
- `service.run_web_search` (ADR-012): provider-native web search under the same disclosure, budget and log rules; results are returned for the caller to turn into source leads.
- HTTP: `GET /api/v1/ai/profiles`, `GET|PUT /api/v1/projects/{id}/ai-policy`, `GET /api/v1/projects/{id}/ai-requests`.

## Research Orchestrator (implemented — ADR-011)
- `modules/research_orchestrator`: versioned templates and strict schemas. Tasks: `draft_problem_frame`, `detect_assumptions`, `challenge` ("Challenge this"). Each runs as a durable job (`orchestrator.run`), launched by a human through `POST /api/v1/projects/{id}/ai-tasks`.
- The model only proposes. Writes go through domain services with the AI principal and gateway provenance: frames as DRAFT, assumptions UNCONFIRMED, evidence CANDIDATE (quote text copied server-side from page spans), competing hypotheses SIGNAL.
- Invalid output is retried once, then surfaced. A job body is one transaction, so there are no partial writes. Provider failures and budget stops are distinct job failure kinds. A failed challenge records RESEARCH_EXECUTION_FAILURE on its tracks, never "no evidence".
- Cooperative cancellation (`jobs.raise_if_cancelled`). The UI follows job status from the API while a task is active.

## Controlled tools (implemented — ADR-013)
- `modules/ai_tools`: READ / PROPOSE / EXTERNAL tools with closed schemas; `invoke` enforces the task allow-list, model provenance for proposals, schema validation and project scoping, and logs every call (append-only `ai_tool_calls`, refused calls included).
- The orchestrator acts only through the registry; HTTP: `GET /api/v1/ai/tools`, `GET /api/v1/projects/{id}/ai-tool-calls`.
