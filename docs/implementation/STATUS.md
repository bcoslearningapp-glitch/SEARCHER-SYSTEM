# Status

**Current milestone:** M6 Hardening and v1.0, next. M5 (v0.6.0) is complete (#52). M4 (v0.5.0) is complete (#42). Tags for v0.2.0–v0.6.0 wait on the owner (#28).

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

## Phase 4 progress
- #33: Design synthesis (ADR-015):
  - Versioned design requirements traced to what they derive from; AI-proposed requirements wait for confirmation.
  - Design concepts with recorded origin, linked hypotheses and mechanisms, and derivation from earlier concepts.
  - Requirement coverage per version, flagged as stale after a revision.
  - Risk-aware Design Readiness Gate.
  - Human selection (not a ranking), with an override when the gate needs a human decision.
  - Rejection keeps the concept and its reusable mechanisms.
  - AI PROPOSE tools, a Design tab, E2E flow, and contracts 0.7.0.
- #34: Design hypotheses and experiments (ADR-016):
  - Versioned design hypotheses (FR-EXP-001).
  - A code-enforced twelve-state experiment workflow with a risk-aware Experiment Readiness Gate and human-only approval.
  - A human-impact review, separate from reference judgment, where external approvals become unresolved operational constraints.
  - Observations, analysed results and interpretations kept as distinct append-only records.
  - Invalidated experiments never change the hypothesis' state.
  - AI PROPOSE tools, an Experiments tab, E2E flow, and contracts 0.8.0.
- #35: Learning and local knowledge (ADR-017):
  - Learning reviews and the Learning Integrity Gate for closing experiments.
  - Local knowledge items with versioned lifecycle, promoted one stage at a time by a person through the Knowledge Promotion Gate (repetition across experiments, contexts, scope, contrary evidence, confidence, time).
  - Downgrade, contest, suspend, reinstate and revalidate.
  - Time-sensitive knowledge flagged REVALIDATION_REQUIRED and surfaced in the attention queue.
  - Cross-project reuse only as a human transferability judgment, labelled and never evidence.
  - Knowledge tab, E2E flow 6, and contracts 0.9.0.
- #36: Terminology and translation integrity (ADR-018):
  - Library-wide, versioned canonical terms, where only a methodology steward approves the canonical form.
  - A deterministic ar/fr/en claim-strength screen that flags association-to-causation, dropped or added hedges, and scope changes between a source and its translation.
  - A terminology check against approved renderings.
  - Terminology page with a translation check, and contracts 0.10.0.
- #41: Project Closure Gate (ADR-019), which completes all nine gates of PRD §41:
  - Blocking decisions, unfinished experiments, unassessed evidence and the quality of the closure record are checked, with a risk-aware override.
  - Closing is recorded as an approval.
  - Desk close and reopen forms, and E2E flow 10.

## Phase 5 progress
- #43: Output composer (ADR-020):
  - Ten output types composed deterministically from canonical state, with READABLE / REFERENCED / AUDIT modes.
  - Every claim traced; exact quotes (excerpt, Qur'an, Hadith) copied from source and re-verified on every revision and at approval.
  - Immutable versions; human-only approval.
  - Outputs tab, E2E, and contracts 0.11.0.
- #44, #45: Output integrity pipeline and export (ADR-021):
  - The eight FR-OUT-002 steps run in order on each version, with append-only run records.
  - FAILED blocks approval; warnings need an acknowledged override.
  - Markdown and HTML export, with RTL, verbatim quotes, a reference list built from records, and an integrity footer.
  - Integrity panel and downloads in the UI, E2E flow 7, and contracts 0.12.0.
- #46: Research Core Package (ADR-022):
  - Checksummed zip export of the project, the library records it uses, and portable asset files.
  - Validated import that never overwrites a project and never raises trust. Withheld files become metadata-only sources; foundational texts arrive staged.
  - Export link and import card in the UI, and E2E flow 8.
  - The full round trip is tested against a second, freshly migrated database.
- #47: Selective cloud workspace and disclosure manifest (ADR-023):
  - A pluggable `CloudWorkspaceAdapter`, off by default. The `local-directory` reference adapter is sandboxed and treated as remote for disclosure.
  - A person explicitly selects excerpts, claims, hypotheses and output versions. The PRD §54 disclosure policy and the project's cloud consent are checked, and payloads carrying installation credentials are refused.
  - The disclosure manifest records every attempt, including blocked ones, with a SHA-256 and size for each item. Database triggers keep it immutable and prevent it from being deleted.
  - Each staging has a TTL with purge, and a person can delete it; the manifest entry stays.
  - A Workspace tab and an E2E flow.
- #52: DOCX and PDF export (ADR-024):
  - DOCX uses python-docx, with bidi paragraphs and RTL runs. Every quote is read back from the finished file before it is returned.
  - PDF uses fpdf2 with HarfBuzz shaping and per-paragraph direction. It embeds `quotes.json` with the exact quote texts and their SHA-256.
  - Amiri fonts (OFL) are bundled. Amiri Quran is used for Qur'an quotes, and an optional owner-supplied publisher font can replace it.
  - Downloads on the output page, and E2E flow 7 covers all four formats.

## Phase 6 progress
- #54: Test-suite completeness:
  - Reusable adapter contract checks (`tests/adapter_contracts.py`) for the SearchProvider interface (mock, Anthropic offline, OpenAI, outage) and the CloudWorkspaceAdapter. The live provider contract uses the same check.
  - A PRD §73 coverage map in `docs/evaluation/TEST_COVERAGE.md`.
  - Loading and error boundaries for every page. A missing record is a not-found page, and a service outage is an error state with a retry, never "not found".
- #55: Security review (`docs/architecture/SECURITY.md`: threat model, a control for each PRD §68 requirement, residual risks):
  - Finding: the API accepted cross-site "simple" requests (multipart uploads, body-less POSTs) and any Host header. That exposed CSRF, and DNS rebinding could read research data. Fixed:
    - a Host allow-list on the API and the web app;
    - refusal of cross-site writes, by foreign `Origin` or `Sec-Fetch-Site: cross-site`;
    - security headers on every response.
- #58: Backup and restore (`research_api.ops.backup`, `docs/operations/BACKUP_RESTORE.md`):
  - One tar archive: a `pg_dump` custom dump, every storage file, and a manifest with SHA-256 checksums.
  - Restore verifies everything first, and refuses to overwrite existing data without `--replace`.
  - Tested: restoring into an empty database returns identical ids, audit history and files.
  - The API image ships PostgreSQL 16 client tools, and backups go to a `backups` volume.
- #56: AI evaluation suite. Every blocking QUALITY_GATES dimension now has a measurement:
  - **Golden suite:** counter-evidence, prompt injection, structured output.
  - **New installation audit:** exact quotes, Qur'an/Hadith integrity, layer separation, tool authorization. It runs from the reliability page or the API, and tampered records fail it.
  - **Human-graded:** citation support.
  - The Methodology Steward still has to approve the thresholds (#28).
- #57: Performance benchmark (`scripts/bench/benchmark.py`, `docs/evaluation/PERFORMANCE.md`):
  - At 1,000 works (~15,800 chunks), every PRD §70 target passes. Search p95 is 128 ms; pages are under 0.9 s; state changes are under 15 ms.
  - Found and fixed N+1 queries in the library listing. The Library page went from 2.06 s to 0.69 s at p95, with a regression test.
  - Vector search is not measured: there is no vector index yet. That gap is tracked as #65.

## M5 exit criteria (PRD §76 Phase 5)
- [x] The export/import round trip preserves source identity and trust. `test_portability.py` imports into a second, freshly migrated database: the same ids arrive, foundational texts arrive staged, and existing library rows win.
- [x] An untransferable asset becomes metadata-only on import (`test_portability.py`).
- [x] A referenced output can trace claims to source. Claim blocks carry traces, the integrity pipeline verifies claims, citations and quotes, and references are built from records (#43, #44, E2E flow 7).
- Deliverables:
  - output composer, multilingual integrity, citation verifier, Markdown/HTML export (#43–#45);
  - DOCX/PDF export (#52);
  - the Research Core Package (#46);
  - the cloud workspace adapter and disclosure manifest (#47).

## M4 exit criteria (PRD §76 Phase 4)
- [x] Complete hypothesis → design → experiment → learning workflow. E2E flow 6 runs through the UI: requirement → concept → design hypothesis → experiment (protocol, approval, run, observation, result, interpretation) → learning review → close → local knowledge → promotion → labelled reuse.
- Deliverables:
  - Design Requirements and design concepts (#33).
  - Design Hypothesis, experiments, and observations/results/interpretations (#34).
  - Local knowledge promotion, operating rules and temporal validity (#35).
  - Terminology (#36) and the Project Closure Gate (#41).

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

- #30: AI reliability registry (ADR-014):
  - Operational metrics from the request log.
  - Append-only evaluation results with the Methodology Steward's thresholds.
  - Synthetic golden fixtures with a deterministic harness, run live in the protected workflow.
  - Reliability page.

## M3 exit criteria (PRD §76 Phase 3)
- [x] Same research task can run with either provider: the provider-neutral gateway with Anthropic and OpenAI adapters (live provider-contract suite), and `test_m3_exit.py` runs one task on two provider profiles.
- [x] A provider switch does not alter the stored schema. The records from both runs validate against the same contract; the model appears only in provenance.
- [x] No provider receives DB credentials. There are no SQL, file or shell tools, tool schemas are closed, and outbound prompts redact connection-string credentials (`test_m3_exit.py`, ADR-013).
- [x] The counter-evidence track demonstrably runs. "Challenge this" records bounded CHALLENGE and ALTERNATIVE_EXPLANATION outcomes (integration tests, E2E flow 9).
- Deliverables: OpenAI and Anthropic adapters, provider profiles, tool registry, Research Orchestrator, Policy Engine, structured outputs, web/search adapters, support/challenge/alternative tracks, research audit, cost tracking.

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

## Blocked (needs a human) — tracked in #28
- Tag `v0.2.0` on `5b7e7a2` (M1), `v0.3.0` on `c56dd92` (M2), `v0.4.0` on `8f1fdba` (M3), and `v0.5.0` on the merge commit of the M4 exit PR. This session can only push its working branch.
- Import and approve the Qur'an text dataset (Constitutional Authority) — see ADR-009.
- Add `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` as secrets of the protected `integration` environment so the provider-contract workflow can run; set them in your local `.env` to use cloud AI.
- P0-12 protect `main` with required checks (repository admin settings).

## Next
- Tag `v0.2.0` from green `main`.
- Phase 2: claims/assumptions, foundational library + Qur'an structured source, Hadith framework, reference review, evidence map + lineage, hypothesis lab, mechanisms, exact-quote protection, operational constraints.
