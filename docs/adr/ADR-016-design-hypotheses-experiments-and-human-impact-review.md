# ADR-016: Design hypotheses, experiments and human-impact review
Status: Accepted
Date: 2026-09-24

Context:
PRD §33-34 and Core §49-51 and §60 require several things:
- Design hypotheses state intervention, population, context, mechanism, expected outcome, measurement, failure criteria, side effects and stop conditions.
- Experiments follow a twelve-state workflow.
- Observation, analysed result and interpretation stay distinct.
- An invalid experiment is not a failed test of the hypothesis.
- Experiments that affect people are reviewed for privacy, consent, harm, authority, law/policy, data handling, institutional approval and reversibility. This review stays separate from the governing reference judgment, and required external approvals are represented as unresolved operational requirements.

Decision:
- **Design hypotheses** (`design_hypotheses` plus append-only `design_hypothesis_versions`) belong to a design concept that is not rejected or withdrawn.
  - Content is versioned. A revision is refused while an approved or running experiment tests the current version.
  - The epistemic state starts UNRESOLVED and changes only through a human assessment.
  - A non-UNRESOLVED assessment needs an interpretation from an INTERPRETED or CLOSED experiment.
  - DESIGN_HYPOTHESIS becomes a target type, so reference reviews, evidence and operational constraints attach to it.
- **Experiment workflow** (pure `experiment_rules.py`):
  - Forward path: PROPOSED → PROTOCOL_DEFINED → (RISK_REVIEW) → APPROVED → RUNNING → DATA_COLLECTION_COMPLETE → ANALYSIS → INTERPRETED → CLOSED. RISK_REVIEW can return to PROTOCOL_DEFINED.
  - When people are affected, RISK_REVIEW is mandatory.
  - PAUSED resumes only to the state it left, which is stored as `paused_from`.
  - PAUSED, ABORTED and INVALIDATED need a reason. CLOSED, ABORTED and INVALIDATED are final.
  - Every move appends to `experiment_transitions`.
- **Experiment Readiness Gate** (`EXPERIMENT_READINESS`), recorded on non-stop moves:
  - PROTOCOL_DEFINED: the protocol must be complete.
  - APPROVED:
    - protocol complete; the design hypothesis has failure and stop conditions; side effects have been considered;
    - the concept is not closed (not yet selected is a reservation);
    - when people are affected, all eight human-impact dimensions have been assessed. A CONCERN needs a human decision, and blocks on L4;
    - the Reference Gate on the concept;
    - a pending external approval is a reservation.
  - RUNNING: operational constraints on the design hypothesis and the concept must allow execution, and the reference result must not be BLOCKED.
  - DATA_COLLECTION_COMPLETE needs at least one observation. INTERPRETED needs at least one result and one interpretation.
  - Approval is a human-only approval record. NEEDS_HUMAN_DECISION requires an acknowledgement with a reason, recorded as OVERRIDDEN_WITH_REASON.
- **Human-impact review** is append-only (`human_impact_assessments`); the latest assessment per dimension counts.
  - It never touches reference judgments.
  - A REQUIRES_EXTERNAL_APPROVAL finding names the authority and creates an unresolved REQUIRES_EXTERNAL_APPROVAL operational constraint on the design hypothesis. The experiment cannot run until a person resolves that constraint.
- **Observation, analysed result and interpretation** are three append-only tables (FR-EXP-003):
  - observations are recorded only while RUNNING;
  - results are recorded only in ANALYSIS and must cite this experiment's observations;
  - interpretations are recorded only in ANALYSIS, must cite its results, and are human-only.
- **Invalidation** (FR-EXP-004) records the reason and leaves the design hypothesis' epistemic state exactly as it was. Invalidated experiments cannot ground an assessment.
- **AI** can propose design hypotheses and experiments (PROPOSED only, with provenance) through `propose_design_hypothesis` and `propose_experiment`. Every other action here is human-only.
- Design hypotheses and experiments cannot be deleted (DB trigger).

Consequences:
- Contracts 0.8.0 add `experiment.schema.json` (DesignHypothesis, Experiment, HumanImpactAssessment, Observation, ExperimentResult, Interpretation) and the HumanImpactDimension, HumanImpactFinding and InterpretationOutcome enums.
- The learning review and knowledge promotion (#35) read interpreted experiments.
