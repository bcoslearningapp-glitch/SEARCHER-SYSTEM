# ADR-011: Research Orchestrator — AI tasks as validated proposals in background jobs
Status: Accepted
Date: 2026-09-24

Context:
PRD §48 requires a Research Orchestrator in which the LLM proposes and the application decides (FR-ORCH-001..005). AI output must land in draft or proposal states (FR-ORCH-003). Tasks must survive browser sessions and be cancellable (FR-ORCH-004/005). A search or tool failure must never read as "no evidence" (Core §72, FR-WEB-004). Important hypotheses need challenge and alternative-explanation tracks (FR-BIAS-001..003). The first tasks are: draft Problem Frame, detect assumptions, and "Challenge this" (§66).

Decision:
- `modules/research_orchestrator` owns task logic. It has no tables. It calls the AI gateway (ADR-010) and the owning domain services only, never other modules' models (architecture test). Every write uses the principal `ai:research_orchestrator` and the `AIActionRecord` returned by the gateway, so provider, model, template version, supplied entity IDs and the disclosure-log id land in audit and provenance. The provider appears only there; stored domain records are identical whichever provider ran the task.
- Humans launch tasks (`ai_task.launch`, human-only). `POST /projects/{id}/ai-tasks` creates a durable `background_jobs` row, commits it, then dispatches `orchestrator.run` to the worker. Status is read from the job (`GET /projects/{id}/ai-tasks`). The UI polls with `router.refresh()` only while a task is queued or running.
- Templates live in `templates.py` with a version string (`draft_problem_frame@1`, …) and a strict JSON Schema. Retrieved passages go into prompts as untrusted sections.
- Output states:
  - Problem Frame → DRAFT, never approved. The AI never overwrites a researcher's open draft; the task fails instead.
  - Assumptions → UNCONFIRMED / SYSTEM_INFERRED, de-duplicated against existing ones.
  - Evidence → CANDIDATE, pointing at an excerpt whose text the server copies from the page span of the search hit. The model supplies no quote text. OCR spans are never exact quotes.
  - Competing hypotheses → SIGNAL, linked as competitors, created only for alternatives the assessment rates STRONG.
- "Challenge this":
  1. Plan challenge queries and alternative explanations.
  2. Run lexical search over the project library.
  3. Have the model assess passages by id; references to passages it was not given are ignored.
  4. Propose candidates.
  5. Record one bounded track run per counter track: RESULTS_FOUND, NO_RELEVANT_EVIDENCE_FOUND, or INSUFFICIENT_SEARCH_COVERAGE when nothing is ingested.
- Invalid structured output is retried once, then surfaced. Nothing is written before all model calls in a task have succeeded and validated.
- Failure handling: the job body runs in one transaction. On any error it rolls back entirely; the gateway's disclosure log survives because it is written separately. The runner classifies failures as PROVIDER_ERROR, STOPPED_RESOURCE_CONSTRAINT or APPLICATION_ERROR. For "Challenge this", a failure hook (in a savepoint that cannot block the FAILED transition) records RESEARCH_EXECUTION_FAILURE or STOPPED_RESOURCE_CONSTRAINT on both counter tracks, so the counter-evidence search stays visibly incomplete.
- Cancellation is cooperative: bodies call `jobs.raise_if_cancelled` before writing, and the runner marks the job CANCELLED with its changes rolled back.
- The mock provider's behaviour is configurable (`AI_MOCK_MODE`), so the E2E stack can simulate a provider outage (PRD §73 flow 9) without network calls.

Consequences:
- New AI tasks need only a template and a function composing domain services; permissions, provenance and state rules stay with the services.
- Search is lexical in v1; semantic retrieval can replace `_search` later without changing the proposal flow.
- A task that fails after its model calls but during writes leaves no partial state. Its model usage is still logged and counts toward the budget.
