# Status

**Current milestone:** M2 Reference, Evidence, Hypothesis (v0.3.0) — feature-complete with this PR. Next: M3 AI Research Engine.

## Completed
- M0 Foundation — #1.
- #2 Policy Engine + principal (ADR-006), #3 Project lifecycle + Research State, #4 notes, Problem Frames, Framing Gate, approvals, decisions — #8.
- #5 source identity, sandboxed storage (ADR-007), Hybrid Source Access, leads, attention queue; #6 ingestion + search (ADR-008) — #9.
- #7 — #10: Desk (projects, Problem Frame drafting with gate feedback and explicit approval, Research State, notes with explicit capture, decisions, attention queue), Library (catalog, upload, verification/availability, search), project Sources (Hybrid Source Access requests and responses); en/fr/ar with RTL and `dir="auto"` for mixed-direction content; E2E flows 1-3 of PRD §73.

## Phase 2 progress
- #11 — #17: claims, assumptions (AI-inferred labeled until human review), open questions, capture from notes.
- #14, #15 — #18: evidence pipeline (candidate → human assessment → evidence), exact quotes copied from verified page spans, lineage-based independence, counter-evidence tracks, hypotheses with immutable versions / Hypothesis Gate / automatic downgrade on new evidence, mechanisms.

- #12, #13 — #19: foundational library with human-approved Qur'an dataset import (no bundled text), exact ayah retrieval, Hadith records with edition numbering, layered reference review, human judgments with blocking reservations → blocking decisions, risk-aware Reference Gate wired into design eligibility, operational constraints kept separate (Scenarios E and F).
- #16 (this PR): Lab (claims, assumptions with human review, hypotheses, mechanisms), hypothesis workspace (evidence map with candidates and acceptance, searches, reference review and judgments, standing, versions, assessment, revision), Map; E2E flows 4 and 5.

## M2 exit criteria (PRD §76 Phase 2)
- [x] reference review trace is source → interpretation → system inference → judgment (layers, ADR-009)
- [x] exact source quote is protected (server-side span copy, append-only excerpts)
- [x] hypothesis can be supported/contradicted without losing history (Scenario D, E2E 4)

## M1 exit criteria (PRD §76 Phase 1)
- [x] full create → frame → approve flow (E2E 1)
- [x] upload PDF and preserve page anchors (E2E 2, worker integration test)
- [x] add metadata-only physical source (E2E 3)
- [x] audit state changes (integration tests assert audit/research events)

## Blocked (needs a human)
- Tag `v0.2.0` on `5b7e7a2` (M1) and `v0.3.0` after this PR merges (M2): this session can only push its working branch.
- Import and approve the Qur'an text dataset (Constitutional Authority) — see ADR-009.
- P0-12 protect `main` with required checks (repository admin settings).

## Next
- Tag `v0.2.0` from green `main`.
- Phase 2: claims/assumptions, foundational library + Qur'an structured source, Hadith framework, reference review, evidence map + lineage, hypothesis lab, mechanisms, exact-quote protection, operational constraints.
