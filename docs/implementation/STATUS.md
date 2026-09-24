# Status

**Current milestone:** M1 Framing & Library (v0.2.0) — in progress.

## Completed
- M0 Foundation merged to `main` in #1 (all 15 CI checks green).
- Backend for issues #2, #3, #4 (this PR): principal + Policy Engine (ADR-006); Project aggregate with lifecycle, fork, close/reopen with preserved closure records; Research State; scratch notes with explicit capture; versioned Problem Frames with risk-aware Framing Gate and explicit human approval; decisions (AI recommendation separate from human decision, Degraded Decision Mode); approvals and gate evaluations append-only; approved frames and resolved decisions immutable at the database level.

## In progress
- #5 sources (storage, SourceWork/Edition/Asset, Hybrid Source Access), #6 ingestion, #7 Desk/Library UI + E2E.

## Blocked (needs a human)
- P0-12 protect `main` with required checks (repository admin settings).

## Next
- Finish M1 (#5, #6, #7), then Phase 2.
