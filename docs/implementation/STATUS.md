# Status

**Current milestone:** M3 AI Research Engine (v0.4.0) — in progress. M2 is feature-complete.

## Completed
- M0 Foundation — #1.
- #2 Policy Engine + principal (ADR-006), #3 Project lifecycle + Research State, #4 notes, Problem Frames, Framing Gate, approvals, decisions — #8.
- #5 source identity, sandboxed storage (ADR-007), Hybrid Source Access, leads, attention queue; #6 ingestion + search (ADR-008) — #9.
- #7 — #10: Desk (projects, Problem Frame drafting with gate feedback and explicit approval, Research State, notes with explicit capture, decisions, attention queue), Library (catalog, upload, verification/availability, search), project Sources (Hybrid Source Access requests and responses); en/fr/ar with RTL and `dir="auto"` for mixed-direction content; E2E flows 1-3 of PRD §73.

## Phase 2 progress
- #11 — #17: claims, assumptions (AI-inferred labeled until human review), open questions, capture from notes.
- #14, #15 — #18: evidence pipeline (candidate → human assessment → evidence), exact quotes copied from verified page spans, lineage-based independence, counter-evidence tracks, hypotheses with immutable versions / Hypothesis Gate / automatic downgrade on new evidence, mechanisms.

- #12, #13 — #19: foundational library with human-approved Qur'an dataset import (no bundled text), exact ayah retrieval, Hadith records with edition numbering, layered reference review, human judgments with blocking reservations → blocking decisions, risk-aware Reference Gate wired into design eligibility, operational constraints kept separate (Scenarios E and F).
- #16 — #20: Lab (claims, assumptions with human review, hypotheses, mechanisms), hypothesis workspace (evidence map with candidates and acceptance, searches, reference review and judgments, standing, versions, assessment, revision), Map; E2E flows 4 and 5.

## Phase 3 progress
- #21: AI gateway (ADR-010). Anthropic and OpenAI adapters behind a provider-neutral interface, with Anthropic server-side refusal fallback enabled. Configurable model profiles; mock provider only when explicitly enabled. Untrusted-source prompt isolation and secret redaction. PRD §54 disclosure policy, human-set project AI policy (consent, allowed profiles, budgets), `STOPPED_RESOURCE_CONSTRAINT` on budget exhaustion. Append-only disclosure/usage log. Schema validation before any caller can use output. Bounded live provider-contract suite.
- Fix: request transactions now commit before the HTTP response is sent (a race seen in E2E under parallel workers).
- #29: Controlled AI tool registry (ADR-013):
  - 14 registered tools with closed schemas.
  - Task allow-lists, provenance required for proposals, project-scoped reads, proposals only as reviewable states.
  - Append-only log of every tool call, refused calls included.
  - The orchestrator acts only through tools.
- #25: Research planning and search (ADR-012):
  - Versioned research plans, which must cover all three tracks.
  - Local library search, audited, with bounded outcomes.
  - Provider-native web search (Anthropic `web_search`) through the AI gateway, with disclosure checks, budgets and a plan-level query cap. Web results become source leads, never evidence.
  - Append-only search audit and track coverage.
  - Human, decision-relative sufficiency. SUFFICIENTLY_ANSWERED is refused until counter-evidence tracks are searched.
  - Research tab UI.
  - Contracts 0.6.0.
- #22: Research Orchestrator (ADR-011). Draft Problem Frame, detect assumptions, and "Challenge this" (counter-evidence and alternative-explanation search over the local library, evidence candidates from exact page spans, competing hypotheses) run as background jobs. Output is validated and retried once. Results are proposals only, with no partial writes. Failures are classified, and failed challenges are recorded as execution failures. Cooperative cancellation. Desk and hypothesis UI with live task status. E2E flow 9 (provider outage).

## M2 exit criteria (PRD §76 Phase 2)
- [x] reference review trace is source → interpretation → system inference → judgment (layers, ADR-009)
- [x] exact source quote is protected (server-side span copy, append-only excerpts)
- [x] hypothesis can be supported/contradicted without losing history (Scenario D, E2E 4)

## M1 exit criteria (PRD §76 Phase 1)
- [x] full create → frame → approve flow (E2E 1)
- [x] upload PDF and preserve page anchors (E2E 2, worker integration test)
- [x] add metadata-only physical source (E2E 3)
- [x] audit state changes (integration tests assert audit/research events)

## Reference library
- KFGQPC developer JSON (e.g. Warsh `warshData_v10.json`) is imported directly, and its SHA-256 is the publisher file's. The Foundational Library screen stages, approves and looks up ayat. It uses a Qur'anic font (Amiri Quran, OFL, with an optional local publisher font). The server-action upload limit was raised to match the API (100 MB). A rehearsal on a disposable stack checked all 6214 Warsh ayat byte-for-byte against the source.

## Blocked (needs a human)
- Tag `v0.2.0` on `5b7e7a2` (M1) and `v0.3.0` after this PR merges (M2): this session can only push its working branch.
- Import and approve the Qur'an text dataset (Constitutional Authority) — see ADR-009.
- Add `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` as secrets of the protected `integration` environment so the provider-contract workflow can run; set them in your local `.env` to use cloud AI.
- P0-12 protect `main` with required checks (repository admin settings).

## Next
- Tag `v0.2.0` from green `main`.
- Phase 2: claims/assumptions, foundational library + Qur'an structured source, Hadith framework, reference review, evidence map + lineage, hypothesis lab, mechanisms, exact-quote protection, operational constraints.
