# Research Core Specification v1.0

**Status:** Normative baseline  
**Scope:** Shared epistemic, methodological, governance, source, portability, and knowledge-lifecycle contract for all Research Suite products.  
**Products:** Product A — Platform Companion; Product B — Integrated AI Research System; Product C — Sovereign Local Research System.

---

## 1. Purpose

Research Core defines what the research system means by a project, source, claim, assumption, hypothesis, evidence, reference judgment, mechanism, design, experiment, knowledge, decision, approval, research state, and project closure.

It is technology-neutral.

It does not prescribe a specific:
- LLM;
- cloud provider;
- database engine;
- vector store;
- agent framework;
- user-interface framework;
- deployment platform.

All Research Suite products MUST preserve Research Core semantics and portability.

---

## 2. Normative language

**MUST**: mandatory requirement. Violating it means the product is outside the approved Core.

**SHOULD**: preferred default. It may be changed for a documented reason without invalidating the Core.

**MAY**: optional capability.

---

## 3. Supreme operating principle

> **The governing reference framework governs; the researcher leads; the AI assists, expands, organizes, challenges, and tests.**

The AI MUST NOT become the supreme reference authority.

The researcher owns:
- purpose;
- direction;
- contextual judgment;
- human intuition and experience;
- adoption of major hypotheses;
- design selection;
- risk acceptance within authorized bounds;
- final human decisions.

AI MAY:
- propose;
- connect;
- search;
- critique;
- generate alternatives;
- extract;
- organize;
- compare;
- detect gaps;
- create candidate hypotheses;
- identify counter-evidence.

Human intuition may generate hypotheses but MUST NOT be treated as proof.

---

## 4. Governing source hierarchy

The canonical hierarchy is:

1. Qur'an.
2. Sunnah.
3. Other approved foundational sources selected by the authorized human authority.
4. Historical and civilizational knowledge.
5. Scientific, experimental, and domain-specific knowledge.
6. Professional and field knowledge.
7. Researcher/project-local observations, hypotheses, experiments, and accumulated knowledge.

The governing direction is top-down.

Lower layers MUST NOT override higher governing layers merely because they are effective, popular, recent, or empirically successful.

Qur'an and Sunnah MUST NOT be forced to provide technical implementation details they do not directly provide. They govern worldview, purposes, values, principles, patterns, boundaries, and rulings where relevant.

---

## 5. Human-made law, policy, contracts, and institutional constraints

The Core MUST distinguish:

### Reference / normative judgment
Whether a goal, means, assumption, or design is acceptable under the approved governing reference framework.

### Operational reality
Whether current law, administrative policy, institutional rule, license, contract, or authorization allows the proposed execution now.

Human-made law and institutional policy MUST NOT automatically become the supreme ethical authority.

A current operational prohibition MAY block immediate execution, require redesign, require authorization, or remain informational while research continues.

The system MUST clearly say when:
- an idea remains researchable;
- a design is reference-consistent;
- current law/policy prevents present execution;
- a lawful alternative or future policy change would be required.

The system MUST NOT falsely imply that reference acceptability automatically authorizes illegal current execution.

---

## 6. Six governing analytical categories

Reference analysis MUST support:

1. **Foundational Conceptions and Truths** — what is the thing and how is reality fundamentally understood?
2. **Purposes and Goals** — where should action lead and why?
3. **Values and Evaluative Standards** — by what standard is something judged good, bad, worthy, or unacceptable?
4. **Sunan / Governing Patterns** — what patterns relate causes, conditions, and outcomes?
5. **Governing Universals and Rules** — what general rule governs understanding, judgment, or action?
6. **Binding Rulings and Limits** — what is required, permitted, prohibited, or conditionally allowed?

These are analytical categories, not independent sources.

---

## 7. Separation of source, interpretation, inference, and decision

Every sensitive reference operation MUST distinguish:

1. source text;
2. approved interpretation;
3. system inference/application;
4. practical judgment.

The AI MUST NOT present its own synthesis as approved interpretation.

AI-created synthesis MUST carry provenance such as `SYSTEM_SYNTHESIS`.

---

## 8. Reference-judgment states

Reference judgments MUST support:

- `REFERENCE_SUPPORTED`
- `REFERENCE_CONSISTENT`
- `NOT_IN_CONFLICT`
- `REQUIRES_MODIFICATION`
- `REJECTED`
- `RESERVED`

Reservation MUST support:
- `BLOCKING_RESERVATION`
- `NON_BLOCKING_RESERVATION`

Directness SHOULD support:
- DIRECT
- CLOSE
- INFERENTIAL
- EXPLORATORY

“No contradiction found” MUST NOT be represented as “supported by the reference”.

---

## 9. Reference interpretation divergence

If approved sources or interpretations produce materially different readings, the system MUST support:

`REFERENCE_INTERPRETATION_DIVERGENCE`

It SHOULD record:
- interpretation A;
- interpretation B;
- source of each;
- implications for the project;
- required human authority if resolution is needed.

The AI MUST NOT casually claim that foundational references contradict one another.

---

## 10. Research inputs

The system MUST support starting from:
- raw question;
- idea;
- problem;
- hypothesis;
- method;
- tool;
- model;
- full system;
- experimental result;
- existing project under evaluation.

Raw input MUST NOT automatically be treated as a complete problem model.

---

## 11. Clarifying dialogue

For incomplete inputs the system MUST support iterative clarification.

Questions SHOULD:
- be few and high-value;
- address ambiguity;
- expose influential assumptions;
- clarify current state;
- clarify desired state;
- identify gap;
- identify context and constraints;
- clarify how the researcher currently explains the problem;
- operationalize vague terms.

The system MUST NOT require a fixed questionnaire for every project.

---

## 12. Minimum Sufficient Understanding

Framing may be proposed as sufficient when the system can articulate:
- what is happening;
- what is desired;
- the gap;
- current explanations;
- key hypotheses;
- context;
- constraints;
- what is known;
- what is unknown;
- what requires reference review.

The researcher MUST explicitly approve the baseline Problem Frame.

---

## 13. Problem Frame

A Problem Frame MUST be versioned.

It SHOULD contain:
- central issue;
- current state;
- desired state;
- gap;
- current explanations;
- initial hypotheses;
- context;
- constraints;
- known knowledge;
- unknowns;
- research questions;
- reference-review points;
- readiness.

Materially changed understanding MUST create a new version rather than silently overwrite the prior baseline.

---

## 14. Epistemic categories

The system MUST distinguish:
- observation;
- documented/factual claim;
- interpretation;
- assumption;
- hypothesis;
- unknown.

It MUST also distinguish:
- what the researcher explicitly said;
- what the system inferred;
- what a source states;
- what an experiment observed.

---

## 15. Core entities

Research Core MUST support at least:

- Project
- ResearchState
- ProblemFrame
- Claim
- Assumption
- Hypothesis
- HypothesisVersion
- Mechanism
- SourceWork
- SourceEdition
- SourceAsset
- SourceExcerpt
- SourceAvailability
- SourceAccessRequest
- KnowledgeUnit
- Evidence
- EvidenceLineage
- ReferenceKnowledge
- ReferenceJudgment
- OpenQuestion
- SourceGap
- SourceRecommendation
- OperationalConstraint
- DesignRequirement
- DesignConcept
- DesignHypothesis
- Experiment
- Observation
- ExperimentResult
- Interpretation
- LocalKnowledge
- OperatingRule
- Term
- TermTranslation
- Decision
- Approval
- QualityGate
- ResearchEvent
- AuditEvent
- ResearchSession
- SessionCheckpoint

---

## 16. Three independent state dimensions

Important entities SHOULD represent separately:

### Workflow state
Where the entity is in the process.

### Epistemic state
What is currently known about its truth/support.

### Governance state
What is its status regarding reference, permissions, and approvals.

The system MUST NOT collapse these into one ambiguous status.

---

## 17. Project lifecycle

Projects MUST support:
- DRAFT
- FRAMING
- ACTIVE_RESEARCH
- ON_HOLD
- FROZEN
- READY_TO_CLOSE
- CLOSED
- REOPENED

Research mode MUST remain distinct and MAY include:
- EXPLORATION
- SCRUTINY
- REFERENCE_REVIEW
- RESEARCH
- SYNTHESIS
- DESIGN
- EXPERIMENT
- LEARNING
- EVALUATION

---

## 18. Claims

Claims SHOULD support types:
- OBSERVATION
- FACTUAL_CLAIM
- CAUSAL_CLAIM
- INTERPRETATION
- NORMATIVE_CLAIM
- MECHANISM_CLAIM
- DESIGN_CLAIM

Workflow state and epistemic strength MUST remain separate.

---

## 19. Assumptions

Assumptions MUST identify whether they are:
- explicit;
- inferred by the system;
- source-derived.

AI-inferred assumptions MUST remain labeled until confirmed/reclassified.

Criticality SHOULD support:
- LOW
- MEDIUM
- HIGH
- FOUNDATIONAL

---

## 20. Hypothesis lifecycle

The system MUST support a lifecycle conceptually equivalent to:

Signal -> Idea -> Formulated Hypothesis -> Reference Review -> Scrutiny -> Research -> Assessment -> Design Input -> Experiment -> Learning

Epistemic states SHOULD support:
- PROMISING
- SUPPORTED
- WEAKENED
- CONTESTED
- REFUTED
- UNRESOLVED

New knowledge MUST be able to downgrade earlier confidence.

---

## 21. Formulated hypothesis

A research-ready hypothesis SHOULD include:
- claim;
- context;
- expected outcome;
- proposed mechanism;
- assumptions;
- boundary conditions;
- potential falsifier/falsification conditions.

The system SHOULD not treat a vague intuition as a mature hypothesis.

---

## 22. Mechanisms

Mechanisms are first-class Research Core entities.

Mechanism states MAY include:
- PROPOSED
- UNDER_INVESTIGATION
- PLAUSIBLE
- SUPPORTED
- DISPUTED
- WEAKENED
- REJECTED
- CONTEXT_DEPENDENT

Mechanisms MUST remain distinguishable from their implementation forms.

---

## 23. Source identity model

The Core MUST distinguish:

### SourceWork
The intellectual work.

### SourceEdition
A specific edition, translation, revision, printing, or verified version.

### SourceAsset
The concrete accessible file/media/URL/object.

A stable canonical source identity MUST be portable across products.

---

## 24. Source access modes

The Core MUST support:
- DIRECT_DIGITAL
- PHYSICAL
- RESEARCHER_MEDIATED
- RESTRICTED
- METADATA_ONLY

The presence of source metadata MUST NOT imply asset availability.

---

## 25. Source verification states

At minimum:
- MACHINE_VERIFIED
- RESEARCHER_SUPPLIED_EXACT
- RESEARCHER_REPORTED_SOURCE_CONTENT
- METADATA_ONLY
- UNVERIFIED

Import/transfer MUST NOT automatically raise verification level.

A later environment MAY raise verification through an explicit Reverification Event.

---

## 26. Hybrid Source Access

When a known source is unavailable to the current product, the system SHOULD request only what is needed:
- relevant pages;
- chapter;
- section;
- surrounding context;
- exact excerpt;
- researcher summary.

The resulting evidence/knowledge MUST retain the correct verification status.

---

## 27. Researcher memory as source lead

A statement such as “I remember reading that author X said Y” MUST NOT become source evidence automatically.

It SHOULD become a:
`SOURCE_LEAD`

until verified.

---

## 28. OCR and transcription

Source text origin MUST support:
- NATIVE_DIGITAL
- OCR_EXTRACTED
- HUMAN_TRANSCRIBED

OCR text MUST NOT be considered an exact verified quote until checked against the source image/text by an approved mechanism or human.

---

## 29. Exact quotations

If content is presented as an exact quotation:
- it MUST match the verified source;
- language editing MUST NOT rewrite it;
- source identity and location MUST be retained.

A paraphrase or summary MUST be labeled as such.

---

## 30. Qur'an

Exact Qur'anic text MUST be retrieved from an approved source, not regenerated from model memory.

A Qur'anic record MUST retain:
- surah name;
- surah number;
- ayah number;
- exact approved text;
- source/version.

The output editor MUST NOT alter exact Qur'anic text.

---

## 31. Sunnah / Hadith

Hadith records SHOULD support:
- collection/source;
- book;
- chapter if relevant;
- number according to approved edition;
- narrator if relevant;
- exact text;
- edition/verification metadata;
- page/location where applicable.

Different numbering systems MUST not be conflated.

Multiple narrations MUST NOT be merged into one synthetic quotation.

---

## 32. Source does not equal evidence

The system MUST preserve the sequence:

Source -> relevant passage/result -> evidence candidate -> assessment -> evidence -> claim/hypothesis/mechanism

A book or study MUST NOT count as “evidence” merely because it exists.

---

## 33. Evidence roles

Evidence MUST support:
- SUPPORTS
- CONTRADICTS
- LIMITS
- QUALIFIES
- CONTEXTUALIZES

Evidence assessment SHOULD consider:
- quality;
- relevance;
- context fit;
- directness;
- independence;
- limitations;
- temporal relevance.

---

## 34. Evidence strength

For revisable empirical/local knowledge, descriptors MAY include:
- UNSUBSTANTIATED
- WEAK
- PROMISING
- SUPPORTED
- STRONG
- ESTABLISHED_WITHIN_SCOPE

The Core MUST NOT require a false-precision 0-100 truth score.

---

## 35. Evidence lineage

The system MUST support dependency relationships such as:
- CITES
- REPLICATES
- USES_DATA_FROM
- DERIVED_FROM
- SUMMARIZES
- REANALYZES
- TRANSLATES

Multiple sources relying on the same original evidence MUST NOT automatically count as independent evidence.

---

## 36. AI-generated evidence contamination

AI-generated analysis, summaries, prior reports, and syntheses MUST retain AI provenance.

They MUST NOT become independent evidence of their own claims merely because they were stored and retrieved later.

Whenever possible, lineage SHOULD terminate at an external evidence-bearing origin or a documented experiment.

---

## 37. Research question and routing

Research SHOULD be organized around explicit questions.

Question types MAY include:
- REFERENCE
- EMPIRICAL
- HISTORICAL
- MECHANISM
- IMPLEMENTATION
- TECHNICAL
- CONTEXTUAL

The question determines the research route.

Reference authority hierarchy remains separate from search order.

---

## 38. Research layers

Retrieval SHOULD support:
1. approved reference library;
2. current project/personal library;
3. accumulated research memory;
4. external knowledge.

Not every question requires every layer.

---

## 39. Retrieval methods

The Core MAY support:
- lexical retrieval;
- semantic retrieval;
- conceptual retrieval;
- mechanism retrieval;
- relationship retrieval;
- cross-project retrieval.

Retrieval finds candidate material; it does not itself adjudicate truth or reference compliance.

---

## 40. Multilingual research

The system MUST support the principle:

`question language != research language != output language`

Canonical concepts SHOULD connect Arabic, English, and French terminology.

---

## 41. Counter-evidence architecture

Important hypotheses MUST be researchable through:

### Support Track
What supports the claim?

### Challenge Track
What contradicts, limits, or weakens the claim?

### Alternative Explanation Track
Could the observed result be real but caused by something else?

Research depth preferences MUST NOT remove the integrity requirement to search for meaningful counter-evidence on important claims.

---

## 42. Source gaps

When knowledge is insufficient, the system SHOULD create a SourceGap identifying:
- missing knowledge;
- why it matters;
- impact if unresolved;
- desired source type;
- candidate sources;
- limitations.

The system SHOULD recommend useful sources rather than only ask the researcher to provide more.

Foundational sources require authorized human adoption.

---

## 43. Conflict analysis

The system SHOULD test whether evidence conflict comes from:
- definitions;
- populations;
- time;
- context;
- intervention;
- measurement;
- methodology;
- scope;
- real unresolved disagreement.

Weak contrary evidence MUST NOT automatically create a `CONTESTED` state when stronger independent evidence is one-sided.

---

## 44. Transferability

Cross-context reuse MUST distinguish:
- DIRECTLY_RELEVANT
- PARTIALLY_TRANSFERABLE
- ANALOGICAL_ONLY
- NOT_TRANSFERABLE

Similarity MUST NOT be treated as automatic transferability.

Cross-domain analogy MUST NOT be presented as direct evidence.

---

## 45. Temporal validity

Knowledge MAY carry:
- STABLE
- SLOW_CHANGING
- DYNAMIC
- HIGHLY_VOLATILE

and:
- valid_from;
- last_verified_at;
- revalidation policy;
- source version/hash.

High-impact reuse of expired time-sensitive knowledge SHOULD trigger revalidation.

---

## 46. Research sufficiency

Sufficiency MUST be relative to the decision/task.

It SHOULD consider:
- supporting evidence;
- opposing evidence;
- alternative explanations;
- independence;
- diversity;
- context fit;
- critical unknowns;
- impact;
- reversibility;
- uncertainty.

Results MUST support:
- SUFFICIENTLY_ANSWERED
- PARTIALLY_ANSWERED
- CONTESTED
- INSUFFICIENT_EVIDENCE
- RESEARCH_ROUTE_EXHAUSTED

“Not known” is a valid conclusion.

---

## 47. Design requirements

Before serious design, the system SHOULD derive Design Requirements from:
- goal;
- reference constraints;
- human/context characteristics;
- mechanisms;
- evidence;
- risks;
- operational constraints.

The solution form MUST NOT be assumed in advance.

---

## 48. Innovation and design origins

Design/idea origins MUST be recordable as:
- RESEARCHER
- AI
- SOURCE
- JOINT_SYNTHESIS
- PRIOR_PROJECT

AI may generate alternatives, but human adoption remains explicit where required.

A reference-rejected design SHOULD remain in history so acceptable mechanisms can potentially be reused in another design.

---

## 49. Design hypothesis

A DesignHypothesis SHOULD state:
- intervention;
- target population;
- context;
- mechanism;
- expected outcome;
- measurement;
- failure criteria;
- side effects;
- stop conditions.

---

## 50. Experiments

Experiment workflow SHOULD support:
- PROPOSED
- PROTOCOL_DEFINED
- RISK_REVIEW
- APPROVED
- RUNNING
- DATA_COLLECTION_COMPLETE
- ANALYSIS
- INTERPRETED
- CLOSED
- PAUSED
- ABORTED
- INVALIDATED

Observation, calculated/analyzed result, and interpretation MUST remain distinct.

---

## 51. Human-impact and operational review

When humans are materially affected, the system SHOULD inspect:
- privacy;
- consent where relevant;
- harm;
- authority;
- data use;
- applicable law;
- institutional approval;
- reversibility.

These operational considerations MUST remain logically separate from the governing reference ethical judgment.

---

## 52. Local knowledge lifecycle

The Core MUST support:

Project Finding -> Local Result -> Repeated Local Result -> Accumulated Local Knowledge -> Candidate Operating Rule -> Operating Rule

Promotion MUST NOT be automatic.

Knowledge MUST be able to be downgraded, contested, suspended, or revalidated.

Operating Rules MUST remain distinct from foundational reference knowledge.

---

## 53. Terminology

The Core SHOULD maintain canonical terminology with:
- term;
- definition;
- domain;
- language;
- approved translations;
- alternatives;
- retain-original rule;
- source.

Translation MUST NOT silently change the strength of a scientific claim.

---

## 54. Output integrity

A final output pipeline SHOULD include:
1. claim verification;
2. citation verification;
3. exact quotation verification;
4. reference-integrity check;
5. terminology consistency;
6. semantic translation check;
7. language editing;
8. rendering/export.

Language editing MUST NOT alter protected exact quotations.

---

## 55. Output traceability

Material final claims SHOULD be traceable:

Final statement -> Claim -> Evidence -> SourceExcerpt -> SourceEdition -> SourceAsset/Hybrid Source

The system SHOULD expose verification limitations in final integrity review.

---

## 56. Events

Meaningful changes SHOULD produce ResearchEvents.

Examples:
- ProblemFrameApproved
- HypothesisCreated
- EvidenceAdded
- ContradictoryEvidenceDetected
- SourceGapDetected
- ReferenceReservationRaised
- DesignSelected
- ExperimentCompleted
- KnowledgePromotionProposed
- ProjectReopened

Event and Action MUST remain conceptually distinct.

---

## 57. AI action authority

Actions MUST be classifiable as:
- AUTONOMOUS
- ACT_AND_NOTIFY
- REQUEST_APPROVAL
- FORBIDDEN

The policy belongs to the system, not to a prompt alone.

---

## 58. Decisions and approvals

AI recommendation MUST remain distinct from human decision.

Formal approval MUST require explicit approval action when the Core requires it.

Ambiguous conversational language MUST NOT automatically become approval.

---

## 59. Override

Methodological recommendations MAY be overridden where policy allows, with documented reason.

A path that violates non-overridable constitutional constraints MUST be marked `OUTSIDE_METHODOLOGY_PATH`, not falsely described as compliant.

---

## 60. Quality Gates

The Core MUST support:
1. Framing Gate
2. Hypothesis Gate
3. Reference Gate
4. Evidence Sufficiency Gate
5. Design Readiness Gate
6. Experiment Readiness Gate
7. Learning Integrity Gate
8. Knowledge Promotion Gate
9. Project Closure Gate

Gate results:
- PASS
- PASS_WITH_RESERVATIONS
- NEEDS_HUMAN_DECISION
- BLOCKED

Gate thresholds SHOULD scale with risk.

---

## 61. Risk model

The system SHOULD assess:
- human impact;
- scale;
- reversibility;
- uncertainty;
- system autonomy.

Operational levels MAY include:
- L1 EXPLORATORY
- L2 APPLIED
- L3 HIGH_IMPACT
- L4 CRITICAL

---

## 62. Degraded Decision Mode

Urgent decisions under incomplete evidence MUST be identifiable as:
`DECISION_UNDER_INCOMPLETE_EVIDENCE`

The system MUST expose:
- what is unverified;
- uncertainty;
- risk;
- required later review.

This mode MUST NOT bypass hard reference constraints.

---

## 63. Research State

At any point the Core MUST be able to represent:
- current question;
- current mode;
- established findings;
- unresolved items;
- active hypotheses;
- reservations;
- blockers;
- pending decisions;
- next recommended action and reason.

Research State MUST not depend on an LLM context window.

---

## 64. Session checkpoint

A research session SHOULD produce a checkpoint:
- what was learned;
- what changed;
- affected hypotheses;
- sources used;
- new questions;
- pending decisions;
- next action.

The chat transcript MUST NOT be the sole project memory.

---

## 65. Free-thinking space

Researchers MUST be able to think/write informally without every statement becoming formal knowledge.

Promotion from scratch space into formal entities requires explicit capture or an appropriate confirmed action.

---

## 66. Project closure

Closure types MUST support:
- KNOWLEDGE_CONCLUSION
- HYPOTHESIS_CONCLUSION
- DECISION
- DESIGN
- EXPERIMENT_CONCLUSION
- PRODUCTION_DELIVERABLE
- JUSTIFIED_STOP

Closure SHOULD record:
- resolved items;
- unresolved items;
- confidence/scope;
- promoted knowledge;
- limitations;
- open questions;
- reopen triggers.

The system proposes readiness; a human closes the project.

---

## 67. Reopening

A closed project MAY reopen because of:
- strong new evidence;
- changed context;
- source invalidation;
- changed approved reference understanding;
- contradictory local result;
- significant technological change;
- new target population;
- changed operational law/policy.

Reopening MUST preserve the prior closure record.

---

## 68. Portability

All products MUST support a canonical Research Core portability contract.

The exported project MUST preserve:
- project ID;
- entity IDs;
- versions;
- relationships;
- provenance;
- verification states;
- source metadata;
- decisions;
- audit;
- methodology version;
- constitution version;
- schema version.

Assets MAY be excluded based on rights/policy.

Missing assets MUST NOT erase source identity or evidence relationships.

Trust MUST NOT increase merely because of import.

---

## 69. Source portability rule

The following MUST transfer when permitted by the project export scope:

- SourceWork identity;
- SourceEdition metadata;
- authors/title/publisher/date;
- ISBN/DOI/identifiers;
- bibliographic metadata;
- reference-authority role;
- verification state;
- access state;
- evidence/knowledge relationships;
- license/portability metadata.

SourceAsset bytes transfer only if allowed.

---

## 70. AI-provider independence

Research Core MUST NOT depend on:
- OpenAI;
- Anthropic;
- local LLM;
- any single model name.

Provider choice is product implementation.

The same canonical project should remain usable across Product A, B, and C.

---

## 71. AI reliability

Products using AI SHOULD maintain model capability/evaluation records.

Changing model/provider MUST NOT silently rewrite existing knowledge.

Material AI actions SHOULD record:
- provider;
- model;
- methodology version;
- prompt/template version;
- supplied evidence/source IDs;
- tool outputs;
- structured result;
- timestamp.

Hidden chain-of-thought is not required.

---

## 72. Search/tool failure

The system MUST distinguish:
- `RESEARCH_EXECUTION_FAILURE`
- `NO_RELEVANT_EVIDENCE_FOUND`
- `INSUFFICIENT_SEARCH_COVERAGE`

A failed tool/API call MUST NOT become “no evidence exists”.

---

## 73. Product UX principle

The internal model may be complex, but user-facing workflow SHOULD use progressive disclosure.

Researchers SHOULD NOT be forced to manually manage every internal state/event.

The product should draft and organize; the user should intervene where judgment or approval matters.

---

## 74. Constitutional invariants

The following are non-negotiable in ordinary project settings:

1. Governing reference hierarchy is preserved.
2. AI is not a foundational authority.
3. Source text, interpretation, inference, and decision remain distinct.
4. Hypothesis is not fact.
5. Source is not evidence merely by existence.
6. Important claims require counter-evidence search.
7. Quantity of citations does not prove independence.
8. Effectiveness does not override a governing reference rejection.
9. Non-contradiction does not mean support.
10. Similarity does not mean grounding.
11. Similarity does not mean transferability.
12. One local result does not become a universal law.
13. AI cannot validate itself through stored AI outputs.
14. Import does not increase trust.
15. Exact quotation is not edited.
16. OCR is not automatically exact.
17. Translation does not silently strengthen/weakens claims.
18. “No evidence found” is bounded by actual search strategy.
19. Search failure is not evidence absence.
20. Time-sensitive knowledge can expire.
21. Unknown may remain unknown.
22. “We do not know” is a valid research conclusion.
23. Human approval is required where the methodology says so.
24. Projects end; knowledge may continue.
25. Human-made law/policy describes operational reality and does not replace the supreme governing reference.
26. Current operational restrictions must still be stated accurately.
27. Research may continue on an idea that current operational rules do not presently allow to be implemented.
28. Foundational sources cannot be automatically adopted by AI.

---

## 75. Research Core success criterion

A conforming product must preserve the following loop:

Question
-> Framing
-> Claims/Assumptions
-> Reference Review
-> Research
-> Counter-Research
-> Evidence
-> Hypothesis
-> Mechanism
-> Design
-> Re-review
-> Experiment
-> Learning
-> Knowledge
-> Output
-> Closure/Reopening

The process MUST allow backward movement whenever new knowledge materially changes an earlier conclusion.

---

## 76. Versioning

This document is `Research Core v1.0`.

Future changes:
- patch: clarifications with no semantic contract change;
- minor: backward-compatible additions;
- major: semantic changes requiring migrations or changed product behavior.

Every Research Core Package MUST declare the Core/schema version used.
