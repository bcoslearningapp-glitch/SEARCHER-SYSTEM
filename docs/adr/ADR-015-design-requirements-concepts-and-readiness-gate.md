# ADR-015: Design requirements, design concepts and the Design Readiness Gate
Status: Accepted
Date: 2026-09-24

Context:
PRD §32 (FR-DESIGN-001..006) and Core §47-48 and §60 require:
- Design Requirements before serious solution design. Each requirement is traceable to purpose, reference constraints, human/context needs, mechanisms, evidence, risk and operational constraints.
- No solution form is assumed in advance.
- Concept origins are recorded.
- Reference-rejected designs stay in history, and their useful mechanisms can be recombined.
- Humans select designs; the system does not name an opaque "winner".

The `design_experiments` module (PRD §58) had no implementation yet.

Decision:
- **Requirements are versioned.** Each requirement is a series of `design_requirements` rows (`series_id`, `version_number`, `supersedes_id`).
  - A revision appends a version and moves the previous one to SUPERSEDED.
  - A DB trigger forbids changes to content and allows only forward status moves: PROPOSED→ACTIVE/SUPERSEDED/WITHDRAWN and ACTIVE→SUPERSEDED/WITHDRAWN. Deletion is forbidden.
  - Each requirement needs at least one trace (`basis` plus an optional entity reference). Entity references to claims, hypotheses, mechanisms or concepts must exist in the project.
- **AI can propose, not decide.** An AI principal can create requirements, which stay PROPOSED until a researcher confirms them, and concepts, which are always recorded with origin AI and AI provenance. A researcher cannot record a concept as AI-originated.
  - Revising, confirming and withdrawing requirements are human-only.
  - Recording coverage, reviewing, withdrawing, selecting and rejecting concepts are also human-only. Selecting and rejecting are approvals.
  - Two PROPOSE tools (`propose_design_requirement`, `propose_design_concept`) are registered for future orchestrator tasks. No task allow-list includes them yet.
- **Coverage is judged per requirement series.** `design_concept_coverage` stores the version it judged. When the requirement is later revised, the coverage is shown as stale, and the gate reports it.
- **Design Readiness Gate.** The gate is a pure function (`design_experiments/gate.py`), recorded as a `DESIGN_READINESS` quality-gate evaluation. It checks:
  - whether the concept is closed;
  - whether active requirements exist, and whether AI-proposed requirements are unconfirmed;
  - coverage by priority: an unaddressed MUST blocks, an unaddressed SHOULD is a reservation, COULD is ignored; conflicts, partial MUST coverage and stale coverage are also checked;
  - whether linked hypotheses have reached ELIGIBLE_FOR_DESIGN (not linked is a reservation, not eligible blocks);
  - the Reference Gate for the concept (a governing rejection outranks effectiveness, Core §74.8);
  - operational constraints (these limit execution, not design).
  On L3/L4 projects, partial MUST coverage and SHOULD/COULD conflicts escalate to NEEDS_HUMAN_DECISION.
- **Selection** re-runs the gate:
  - BLOCKED refuses selection.
  - NEEDS_HUMAN_DECISION requires an explicit acknowledgement with a reason, and is recorded as OVERRIDDEN_WITH_REASON.
  - Selection records an approval and leaves other concepts unchanged, so it is not a ranking.
- **Rejection** records the ground (REFERENCE / EVIDENCE / OPERATIONAL / FEASIBILITY / OTHER), a reason, the reusable mechanisms (which must be the concept's own), and a REJECTED approval.
  - Concepts cannot be deleted (DB trigger).
  - New concepts can name the concepts they derive from.
- DESIGN_CONCEPT becomes an evidence/reference target. Reference reviews and operational constraints attach to concepts the same way they attach to hypotheses.

Consequences:
- Contracts 0.7.0 add `design.DesignRequirement` and `design.DesignConcept`, plus the matching enums.
- Design hypotheses, experiments and the human-impact review (#34) build on selected concepts.
