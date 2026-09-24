# ADR-012: Research plans, search providers and audit, web results as leads, sufficiency
Status: Accepted
Date: 2026-09-24

Context:
- PRD §22 asks for explicit questions and plans with support, challenge and alternative tracks and a search budget.
- §24 asks for search behind a `SearchProvider` interface (FR-WEB-001), provider-native web search where available (FR-WEB-002), and web results as candidate sources rather than evidence (FR-WEB-003).
- Absence, failure, inaccessibility and insufficient coverage must stay distinct (FR-WEB-004), and every search must be audited (FR-WEB-005).
- §31 requires decision-relative sufficiency with a fixed set of considerations and five conclusion states.
- The Core requires local material to be searched before external research (FR-RET-001), and web queries are outbound disclosure (§54).
- MASTER_PLAN listed "web search provider order" as an open decision.

Decision:
Search providers
- The local library is searched synchronously (`POST /projects/{id}/searches/local`) using the existing lexical index.
- Web search is a provider capability behind the AI gateway: `AIProvider.web_search(WebSearchRequest)`, called only through `gateway.run_web_search`. That applies the same disclosure policy, budget and `ai_requests` log as model calls; queries count as outbound content.
- The Anthropic adapter uses the server-side `web_search_20260209` tool with `allowed_callers=["direct"]`, so result blocks return unfiltered to the application. It uses low effort, handles `pause_turn` with bounded continuations, and treats per-query errors as failures, not empty results. Cost includes the per-search price.
- The OpenAI adapter reports web search as unavailable for now. The mock returns configured results.
- Provider order is therefore local library first, then the configured profile's provider-native web search. A generic external search API can be added as another adapter without changing callers.
- Web search runs as an orchestrator job (`web_search`), launched by a human, with durable status.

Leads, not evidence
- Each distinct web result URL becomes a `SourceLead` with origin `WEB_SEARCH`, url, title, and the search record id, de-duplicated per project.
- Leads follow the existing lead lifecycle: catalogue, excerpt, verify. They never become evidence directly. URL and title are untrusted text; the UI renders links as `noopener noreferrer nofollow`.

Plans
- `research_plans` rows are versions of a question series. A plan must cover all three tracks; settings can change depth but not skip counter-evidence search (FR-BIAS-001/004).
- Revising creates a new version and marks the old one SUPERSEDED. A DB trigger allows only that status change and forbids deletes.
- Question type is routing only; it never alters the reference authority order (FR-RSCH-004).
- `max_web_searches` caps web queries per plan series. Queries are trimmed to the remaining budget, and an exhausted budget stops as `STOPPED_RESOURCE_CONSTRAINT`.

Search audit
- `search_records` is append-only (trigger). Each record holds question, provider, track, queries, languages, outcome (`ResearchOutcomeKind`), result count, scope, actor and, for web searches, the AI request id and provenance.
- Outcomes:
  - An empty library → `INSUFFICIENT_SEARCH_COVERAGE`.
  - All queries failed with no results → `INSUFFICIENT_SEARCH_COVERAGE`.
  - Provider failure, including disclosure-blocked → `RESEARCH_EXECUTION_FAILURE`.
  - Budget exhausted → `STOPPED_RESOURCE_CONSTRAINT`.
- Failed web search jobs record their outcome through the orchestrator failure hook.
- Track coverage per plan is derived from these records.

Sufficiency
- `sufficiency_assessments` is append-only, human-only (`sufficiency.assess`, approval class), and tied to the plan's `decision_served`. All ten FR-SUFF-002 considerations are required.
- The coverage snapshot and search record ids are stored as `signals`, so a later "Why?" (§66) uses stored data.
- SUFFICIENTLY_ANSWERED is refused unless the challenge and alternative-explanation tracks each have a completed search (Core §41). Every other conclusion, including "not known", is always allowed.

Contracts
- New `research.schema.json` (ResearchPlan, SearchRecord, SufficiencyAssessment) and optional web-origin fields on `SourceLead`. Schema version goes to 0.6.0 (additive).

Consequences:
- Adding a search API provider or OpenAI web search is adapter work only.
- The AI can run searches and record their outcomes, but cannot create plans or judge sufficiency. AI drafting of plans or sufficiency is a later, separate task.
- Semantic, cross-project and multilingual query expansion (FR-RET-003/004) remain open. The audit already records the languages searched.
