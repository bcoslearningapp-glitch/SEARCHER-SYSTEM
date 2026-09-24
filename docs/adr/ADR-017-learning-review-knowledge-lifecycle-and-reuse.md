# ADR-017: Learning review, local knowledge lifecycle and labelled reuse
Status: Accepted
Date: 2026-09-24

Context:
The requirements come from PRD §28-29, §35 and §41, and Core §44-45, §52 and §60:
- Experiments close through a Learning Integrity Gate.
- Local knowledge moves PROJECT_FINDING → LOCAL_RESULT → REPEATED_LOCAL_RESULT → ACCUMULATED_LOCAL_KNOWLEDGE → CANDIDATE_OPERATING_RULE → OPERATING_RULE, and never automatically.
- Knowledge keeps its scope, contexts, evidence basis, contrary evidence, confidence, time sensitivity and provenance. It can be downgraded, contested, suspended or revalidated.
- Operating rules stay distinct from foundational reference knowledge.
- Time-sensitive knowledge past its revalidation policy is marked before high-impact reuse.
- Reuse across contexts carries a transferability judgment, and analogy is never direct evidence.

Decision:
- **Learning review** (`learning_reviews`, append-only, in `design_experiments`):
  - Human-only.
  - Recordable on INTERPRETED, ABORTED and INVALIDATED experiments.
  - Records what was learned, the effect on the design hypothesis, surprises, limitations, validity threats and next steps.
- **Learning Integrity Gate.** An INTERPRETED → CLOSED move is recorded as a `LEARNING_INTEGRITY` evaluation.
  - No review blocks the move.
  - A review without limitations is a reservation; on L3/L4 it needs a human decision.
- **Knowledge items** live in `knowledge_memory`, with append-only `knowledge_versions`; every change stores a full snapshot.
  - New items always start as PROJECT_FINDING. AI may create findings (with provenance). Everything else is human.
  - An evidence basis must be an existing record in the same project: an interpretation, learning review, claim, hypothesis, mechanism, design concept or design hypothesis.
  - Items are never deleted. They are never stored in, or cited as, foundational reference layers.
- **Knowledge Promotion Gate** (`KNOWLEDGE_PROMOTION`, pure `rules.py`). Promotion is human-only, one stage at a time, and an approval. NEEDS_HUMAN_DECISION requires an acknowledgement with a reason.
  - The item must be ACTIVE and not due for revalidation.
  - At least one basis is required, and at least two *independent* bases from REPEATED_LOCAL_RESULT on. Records from the same experiment count as one.
  - Two or more contexts are expected for ACCUMULATED_LOCAL_KNOWLEDGE; a single context needs a human decision.
  - For operating-rule stages: scope is stated, contrary evidence has been searched, and confidence is above WEAK. Recorded contrary evidence or HIGHLY_VOLATILE time sensitivity needs a human decision.
- **Standing** (FR-KNOW-004), human-only and versioned:
  - DOWNGRADE to a lower stage (status DOWNGRADED);
  - CONTEST;
  - SUSPEND;
  - REINSTATE;
  - REVALIDATE, which sets `last_verified_at` and optionally the source version. Contested or suspended knowledge must be reinstated first.
- **Temporal validity.** DYNAMIC and HIGHLY_VOLATILE knowledge requires a revalidation interval. When `last_verified_at + interval` has passed:
  - the effective status reads REVALIDATION_REQUIRED;
  - the item appears in the project's attention queue;
  - promotion is blocked, and reuse into an L3/L4 project is refused.
  The mark is computed when read rather than written by a background sweep, so it is always current and needs no scheduler.
- **Reuse** (`knowledge_reuses`, append-only):
  - A human records the transferability state, a rationale and the differences for a specific knowledge version.
  - The target project lists reused knowledge with its label and `direct_evidence: false`. Nothing is copied into its evidence.
  - Suspended knowledge cannot be reused.

Consequences:
- Contracts 0.9.0 add `knowledge.schema.json`: LearningReview, KnowledgeItem, KnowledgeReuse.
- E2E flow 6 (design → experiment → learning review) extends into knowledge recording, promotion and labelled reuse.
