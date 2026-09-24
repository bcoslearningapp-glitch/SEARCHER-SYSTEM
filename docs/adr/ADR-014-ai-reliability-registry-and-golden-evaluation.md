# ADR-014: AI reliability registry and golden evaluation
Status: Accepted
Date: 2026-09-24

Context:
PRD §52 requires an AI capability/reliability registry covering thirteen dimensions. It also forbids a model change from rewriting existing knowledge (FR-EVAL-001), expects a regression suite before default models change (FR-EVAL-002), and requires golden fixtures for critical flows (FR-EVAL-003). QUALITY_GATES lists proposed thresholds, pending Methodology Steward approval.

Decision:
- Dimensions and thresholds live in `ai_reliability/dimensions.py` as configuration mirroring QUALITY_GATES, including which ones block v1.0. Prompt-injection resistance is added as a blocking dimension; it is required by §51 and CLAUDE.md.
- Operational reliability is derived from the append-only `ai_requests` log, per provider, model and task: calls, successes, invalid output, refusals, unavailability, policy blocks, fallbacks, tokens, estimated cost and structured-output reliability. Nothing is copied or estimated separately.
- Evaluation results go into the append-only `ai_evaluations` table (DB trigger), one row per model and dimension. Each row stores the score, the threshold and comparator in force at the time, pass/fail, sample size, method (AUTOMATED_GOLDEN or HUMAN_GRADED), fixture set and details.
  - Only the Methodology Steward or the system `golden-evaluation` principal may record results (`ai_evaluation.record`). An AI principal can never grade itself.
  - A model's standing is the latest result per dimension. Blocking dimensions that fail or have no result are listed, which keeps the model off default use.
- Golden fixtures in `docs/evaluation/fixtures/` are synthetic JSON:
  - counter-evidence retrieval (seeded counter passages);
  - hidden-assumption detection (seeded assumptions matched by keyword);
  - prompt-injection resistance (injected passages with canaries).
- The harness (`ai_reliability/golden.py`) runs the production templates against the fixtures, scores deterministically and also measures structured-output reliability with the production retry. It reaches the model through a pluggable caller:
  - the AI gateway (disclosure-checked as PUBLIC synthetic data, budgeted, logged under a fixed evaluation project id);
  - a direct provider call in the protected provider-contract workflow, which asserts that blocking dimensions pass before a default model change;
  - a fake in CI, which tests the scoring itself.
- Recording a result changes nothing in research data (FR-EVAL-001). Provenance on every AI action already names the model that produced it.

Consequences:
- Human-graded dimensions (citation accuracy, layer separation, prose quality in each language, hallucination rate) are recorded through the API by the Steward. Their graded sample sets will grow with Phase 4-6 flows.
- Thresholds stay placeholders until the Steward approves them. Past rows keep the threshold they were judged against.
