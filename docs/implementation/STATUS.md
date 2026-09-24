# Status

**Current milestone:** M1 Framing & Library (v0.2.0) — feature-complete with this PR; tag after merge.

## Completed
- M0 Foundation — #1.
- #2 Policy Engine + principal (ADR-006), #3 Project lifecycle + Research State, #4 notes, Problem Frames, Framing Gate, approvals, decisions — #8.
- #5 source identity, sandboxed storage (ADR-007), Hybrid Source Access, leads, attention queue; #6 ingestion + search (ADR-008) — #9.
- #7 (this PR): Desk (projects, Problem Frame drafting with gate feedback and explicit approval, Research State, notes with explicit capture, decisions, attention queue), Library (catalog, upload, verification/availability, search), project Sources (Hybrid Source Access requests and responses); en/fr/ar with RTL and `dir="auto"` for mixed-direction content; E2E flows 1-3 of PRD §73.

## M1 exit criteria (PRD §76 Phase 1)
- [x] full create → frame → approve flow (E2E 1)
- [x] upload PDF and preserve page anchors (E2E 2, worker integration test)
- [x] add metadata-only physical source (E2E 3)
- [x] audit state changes (integration tests assert audit/research events)

## Blocked (needs a human)
- P0-12 protect `main` with required checks (repository admin settings).

## Next
- Tag `v0.2.0` from green `main`.
- Phase 2: claims/assumptions, foundational library + Qur'an structured source, Hadith framework, reference review, evidence map + lineage, hypothesis lab, mechanisms, exact-quote protection, operational constraints.
