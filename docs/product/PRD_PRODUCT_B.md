# Product Requirements Document (PRD)
# Product B — Integrated AI Research System

**Document version:** 1.0  
**Status:** Implementation baseline  
**Language:** English  
**Primary implementation agent:** Claude Code  
**Normative dependency:** Research Core Specification v1.0  
**Product family:** Research Suite  
**Product type:** Local-first research system with integrated cloud AI APIs  
**Intended first deployment:** Local workstation / local network, Docker-based  
**Future compatibility:** Product A (Platform Companion) and Product C (Sovereign Local Research System)

---

## 1. Document purpose

This PRD defines the complete functional, architectural, operational, quality, security, and implementation requirements for Product B: the Integrated AI Research System.

The intended consumer is an autonomous software-development agent, primarily Claude Code, working in GitHub. The document is written so that implementation decisions can be made without repeatedly re-deriving the product philosophy.

This PRD is subordinate to the Research Core Specification v1.0. If a requirement in this PRD conflicts with the Research Core, the Research Core wins unless a newer approved version explicitly changes the rule.

The implementation MUST preserve compatibility with the canonical Research Core data model so a research project can later move to Product A or Product C without losing its epistemic state, source identity, provenance, judgments, decisions, or audit history.

---

## 2. Product summary

Product B is a local-first research operating system that integrates external AI models through APIs while keeping the canonical research project, source library, structured knowledge, methodology state, governance rules, and audit trail under the control of the application.

The product is not an AI chat application. Chat is one interaction surface inside a larger research system.

The system must help a researcher:

- frame an issue before prematurely answering it;
- distinguish observations, claims, interpretations, assumptions, hypotheses, and unknowns;
- adjudicate relevant goals, means, values, assumptions, and designs against the approved governing reference framework;
- search internal and external knowledge;
- deliberately seek supporting evidence, counter-evidence, and alternative explanations;
- manage physical, restricted, digital, and metadata-only sources;
- build evidence maps and hypothesis histories;
- derive mechanisms and design requirements;
- generate, compare, and test design concepts;
- learn from experiments without over-generalizing local results;
- produce high-quality multilingual research outputs with exact quotations and traceable citations;
- maintain a durable research state independent of any model context window;
- export and import the project through the Research Core portability contract.

The product must preserve the constitutional operating principle:

> **The governing reference framework governs; the researcher leads; the AI assists, expands, organizes, challenges, and tests.**

---

## 3. Product goals

### 3.1 Primary goals

The product MUST:

1. Implement Research Core v1.0 as executable product behavior rather than a prompt-only methodology.
2. Maintain the canonical research project locally as the source of truth.
3. Integrate at least OpenAI and Anthropic through a provider abstraction.
4. Allow the researcher to select or configure the AI provider by task or project policy.
5. Prevent AI providers from receiving direct database access or unrestricted filesystem access.
6. Route AI access through controlled application tools.
7. Preserve full provenance for source-derived knowledge, AI-generated synthesis, human input, and experimental results.
8. Provide explicit workflow states, epistemic states, governance states, decisions, approvals, events, and quality gates.
9. Support Arabic, English, and French as first-class research and output languages.
10. Preserve scientific terminology and exact source quotations.
11. Treat Qur'an, Sunnah, and approved foundational sources with stricter quotation and reference integrity requirements.
12. Support digital, physical, researcher-mediated, restricted, and metadata-only sources.
13. Support portable project export/import across Research Suite products.
14. Produce outputs that can be audited from final claim back to evidence and source location.
15. Remain usable if a cloud AI provider is temporarily unavailable.
16. Be architected so a future local AI provider can replace cloud providers without rewriting the Research Core.

### 3.2 Secondary goals

The product SHOULD:

- minimize repeated manual research work;
- expose research blind spots without overwhelming the researcher;
- reuse prior local knowledge while evaluating transferability;
- offer a selective optional cloud research workspace/gateway without making it the canonical source of truth;
- allow future multi-user institutional deployment;
- allow later plug-in support for additional research, search, document, and AI providers.

---

## 4. Non-goals

Version 1 MUST NOT attempt to become:

- an autonomous religious authority or automated mufti;
- a substitute for approved interpretation sources;
- a generic chat clone;
- a full academic reference manager replacement;
- a full enterprise records-management platform;
- a social research network;
- an uncontrolled multi-agent swarm;
- a direct database-access agent;
- a system in which AI-generated content becomes evidence by repetition;
- a fully sovereign/offline solution; that belongs to Product C;
- a browser bot that automates consumer ChatGPT/Claude interfaces; that belongs to Product A if ever implemented;
- a system that silently treats current law or corporate policy as the highest moral authority.

---

## 5. Governing hierarchy and operational constraints

### 5.1 Governing reference hierarchy

The Research Core authority hierarchy MUST be represented and enforced as:

1. Qur'an.
2. Sunnah.
3. Other approved foundational sources chosen by the authorized human authority.
4. Historical/civilizational knowledge.
5. Scientific/experimental/domain knowledge.
6. Professional/field knowledge.
7. Researcher/project-local knowledge.

Lower layers MUST NOT overrule higher governing layers.

### 5.2 Reference analytical categories

Reference knowledge MUST support the six analytical categories:

- Foundational Conceptions and Truths
- Purposes and Goals
- Values and Evaluative Standards
- Sunan / Governing Patterns
- Governing Universals and Rules
- Binding Rulings and Limits

These are analytical lenses, not independent sources.

### 5.3 Human-made law, contracts, policies, and institutional rules

The product MUST distinguish:

**Reference judgment:** whether a goal, means, or design is acceptable under the approved governing reference framework.

**Operational reality:** whether current laws, contracts, licensing terms, institutional rules, company policies, or administrative constraints allow the proposed execution now.

Human-made legal or institutional constraints MUST NOT be automatically classified as superior moral authority.

However, if current execution would violate applicable law, contract, rights, or institutional authorization, the product MUST flag the execution constraint clearly. It may continue researching the idea, evaluate lawful alternatives, recommend redesign, or identify what external change/approval would be required. It MUST NOT falsely present a currently prohibited execution path as operationally ready.

Operational constraint states SHOULD include:

- INFORMATIONAL
- REQUIRES_REDESIGN
- REQUIRES_EXTERNAL_APPROVAL
- BLOCKS_CURRENT_EXECUTION

---

## 6. Target users

### 6.1 Primary persona — Independent researcher/designer

A researcher who develops methods, systems, training models, organizational designs, management approaches, tools, or intellectual frameworks and needs rigorous long-term knowledge accumulation.

Needs:
- deep dialogue;
- reference-grounded analysis;
- source management;
- hypothesis testing;
- reusable project memory;
- high-quality multilingual outputs.

### 6.2 Professional researcher / consultant

Works across multiple client or organizational projects and needs:
- reusable local knowledge;
- clear separation between source evidence and interpretation;
- decision briefs;
- source traceability;
- project portability;
- configurable confidentiality.

### 6.3 Research lead / project lead

Needs:
- review queues;
- approvals;
- project state visibility;
- risk and quality gates;
- team-ready history;
- reproducibility.

### 6.4 Methodology steward

Needs:
- control over methodology versions;
- quality-gate rules;
- evidence rules;
- promotion policies;
- research defaults.

### 6.5 Constitutional authority

Needs:
- control over approved foundational sources;
- reference hierarchy;
- foundational interpretation configuration;
- protected change audit.

---

## 7. Product experience principles

1. **Complexity belongs inside the system, not in front of the researcher.**
2. AI drafts and proposes; the human approves where Research Core requires approval.
3. A conversation transcript is not the project memory.
4. The user should always know the current research question, current state, unresolved issues, pending decisions, and logical next action.
5. Internal precision and simple UX must coexist through progressive disclosure.
6. Important claims must be traceable to their evidence and source.
7. The system must expose uncertainty rather than manufacture certainty.
8. “I do not know yet” is a valid result.
9. Search depth may vary, but integrity rules do not.
10. AI provider choice must not alter Research Core semantics.

---

## 8. Core user interface model

The default product navigation SHOULD contain five research spaces:

### 8.1 Desk

Primary daily workspace.

Contains:
- current research question;
- current mode;
- “why this is the next step” explanation;
- dialogue/work area;
- established items;
- unresolved items;
- reservations;
- items requiring human attention;
- current research task progress.

### 8.2 Map

Research project map with progressive disclosure.

Top level:
- central problem;
- active hypotheses;
- major open questions;
- major decisions;
- blocking issues.

Expanded hypothesis:
- mechanism;
- supporting evidence;
- contradicting evidence;
- qualifying evidence;
- alternative explanations;
- reference judgment;
- experiments;
- remaining unknowns.

### 8.3 Library

Manages:
- foundational sources;
- digital sources;
- physical sources;
- restricted sources;
- metadata-only sources;
- external discovered sources;
- suggested sources;
- source gaps;
- source access requests.

### 8.4 Lab

Manages:
- ideas;
- hypotheses;
- mechanisms;
- design requirements;
- design concepts;
- design hypotheses;
- experiments;
- results;
- learning reviews.

### 8.5 Outputs

Manages:
- research reports;
- decision briefs;
- evidence maps;
- design specifications;
- learning reviews;
- executive summaries;
- export formats;
- output-integrity status.

Administration, Constitution, Methodology, Providers, Security, and Audit SHOULD live outside the primary five-space workflow.

---

## 9. Project lifecycle

The product MUST support:

- DRAFT
- FRAMING
- ACTIVE_RESEARCH
- ON_HOLD
- FROZEN
- READY_TO_CLOSE
- CLOSED
- REOPENED

`ProjectStatus` MUST remain separate from `ResearchMode`.

Supported research modes MUST include:

- EXPLORATION
- SCRUTINY
- REFERENCE_REVIEW
- RESEARCH
- SYNTHESIS
- DESIGN
- EXPERIMENT
- LEARNING
- EVALUATION

The product MUST support re-opening previously closed matters when new evidence, a changed context, a changed reference interpretation, a source invalidation, or a meaningful experiment result affects previous conclusions.

---

## 10. Project creation requirements

### FR-PROJ-001
The user MUST be able to create a project with a minimal starting input:
- provisional title;
- initial question/problem/idea/system;
- input type;
- sensitivity level.

### FR-PROJ-002
The system SHOULD infer candidate domain, impact level, and likely research mode, but MUST allow researcher correction.

### FR-PROJ-003
A project MUST store:
- core schema version;
- methodology version;
- constitution version;
- project sensitivity;
- risk profile;
- created/updated timestamps;
- creator/owner.

### FR-PROJ-004
The product MUST support project fork with lineage.

### FR-PROJ-005
The product MUST preserve all prior versions of approved major artifacts rather than silently replacing them.

---

## 11. Research dialogue and framing

### FR-FRAME-001
For raw ideas/questions, the system MUST use iterative clarification before treating the input as a complete problem definition.

### FR-FRAME-002
The AI SHOULD ask one or a few high-value questions at a time.

### FR-FRAME-003
The AI SHOULD only ask questions that materially clarify:
- ambiguity;
- causal assumptions;
- desired state;
- context;
- constraints;
- definitions;
- evidence;
- competing interpretations.

### FR-FRAME-004
The system MUST distinguish:
- Observation
- Claim
- Interpretation
- Hypothesis
- Unknown

### FR-FRAME-005
The system MUST draft a versioned Problem Frame containing:
- central issue;
- current reality;
- desired state;
- gap;
- current explanations;
- initial hypotheses;
- context;
- constraints;
- knowns;
- unknowns;
- reference-review points;
- readiness assessment.

### FR-FRAME-006
The Problem Frame cannot become baseline APPROVED without explicit human approval.

### FR-FRAME-007
A materially changed understanding MUST create a new ProblemFrameVersion and mark the old baseline as SUPERSEDED rather than overwriting history.

---

## 12. Claims and assumptions

### FR-CLAIM-001
Claims MUST support at least:
- OBSERVATION
- FACTUAL_CLAIM
- CAUSAL_CLAIM
- INTERPRETATION
- NORMATIVE_CLAIM
- MECHANISM_CLAIM
- DESIGN_CLAIM

### FR-CLAIM-002
Workflow state MUST remain separate from epistemic assessment.

### FR-CLAIM-003
AI-inferred assumptions MUST be labeled as AI-inferred until confirmed or reclassified.

### FR-CLAIM-004
Critical assumptions MUST support criticality:
- LOW
- MEDIUM
- HIGH
- FOUNDATIONAL

### FR-CLAIM-005
The UI MUST allow a researcher to convert a note or dialogue statement into a formal claim, assumption, question, hypothesis, evidence candidate, quote, or mechanism.

---

## 13. Hypothesis Lab

### FR-HYP-001
Hypothesis lifecycle MUST support:
- SIGNAL
- IDEA
- FORMULATED_HYPOTHESIS
- UNDER_REFERENCE_REVIEW
- UNDER_SCRUTINY
- UNDER_RESEARCH
- ASSESSED
- ELIGIBLE_FOR_DESIGN
- USED_IN_DESIGN
- TESTED_IN_PRACTICE

### FR-HYP-002
Epistemic hypothesis assessments SHOULD include:
- PROMISING
- SUPPORTED
- WEAKENED
- CONTESTED
- REFUTED
- UNRESOLVED

### FR-HYP-003
A formulated hypothesis SHOULD contain:
- statement/claim;
- context;
- expected outcome;
- proposed mechanism;
- assumptions;
- boundary conditions;
- falsification conditions.

### FR-HYP-004
Hypothesis versions MUST be immutable historical snapshots.

### FR-HYP-005
The system MUST support competing hypotheses and competing mechanisms.

### FR-HYP-006
New evidence MUST be able to downgrade a previously supported hypothesis.

---

## 14. Mechanisms

### FR-MECH-001
Mechanisms MUST be first-class entities rather than text embedded only in hypotheses.

### FR-MECH-002
Mechanism status SHOULD support:
- PROPOSED
- UNDER_INVESTIGATION
- PLAUSIBLE
- SUPPORTED
- DISPUTED
- WEAKENED
- REJECTED
- CONTEXT_DEPENDENT

### FR-MECH-003
The system MUST allow evidence, hypotheses, design concepts, and experiments to link to mechanisms.

### FR-MECH-004
Cross-domain retrieval MAY retrieve prior mechanisms from unrelated domains but MUST assess transferability before treating them as relevant evidence.

---

## 15. Source model

The source model MUST separate:

### SourceWork
The intellectual work as a whole.

### SourceEdition
A specific edition, translation, printing, revision, or verified version.

### SourceAsset
A concrete asset accessible in an environment, such as:
- PDF;
- EPUB;
- HTML capture;
- image;
- scan;
- audio;
- local text;
- remote URL;
- other file.

### FR-SRC-001
Every SourceWork MUST have a stable canonical Research Core identifier.

### FR-SRC-002
Edition identity MUST be distinct from work identity.

### FR-SRC-003
SourceAsset availability MUST be environment-specific.

### FR-SRC-004
Source access modes MUST support:
- DIRECT_DIGITAL
- PHYSICAL
- RESEARCHER_MEDIATED
- RESTRICTED
- METADATA_ONLY

### FR-SRC-005
Verification states MUST support at least:
- MACHINE_VERIFIED
- RESEARCHER_SUPPLIED_EXACT
- RESEARCHER_REPORTED_SOURCE_CONTENT
- METADATA_ONLY
- UNVERIFIED

### FR-SRC-006
Source identity and metadata MUST survive project export even when the SourceAsset cannot be transferred.

### FR-SRC-007
Trust MUST NOT be upgraded by import.

### FR-SRC-008
A new environment MAY upgrade verification only through an explicit ReverificationEvent.

---

## 16. Hybrid Source Access

### FR-HYBRID-001
For a known but unavailable source, the system MUST create a targeted source-access request rather than treating the source as nonexistent.

### FR-HYBRID-002
The request SHOULD identify:
- why the source is needed;
- requested chapter/pages/section;
- required surrounding context;
- acceptable input form;
- priority.

### FR-HYBRID-003
Accepted responses MAY include:
- exact researcher-supplied text;
- page images;
- researcher summary;
- researcher attestation;
- later digital asset.

### FR-HYBRID-004
The resulting verification level MUST reflect the actual access method.

---

## 17. Source ingestion

The ingestion pipeline SHOULD implement:

1. File fingerprint/checksum.
2. Metadata extraction.
3. Work/edition matching.
4. Text extraction.
5. Structure detection.
6. Page/section anchoring.
7. Text-origin tagging.
8. Chunk generation.
9. Embedding/index generation.
10. Optional knowledge-unit extraction.

### FR-INGEST-001
The immutable original asset MUST be retained when rights and storage policy allow.

### FR-INGEST-002
Text origins MUST distinguish:
- NATIVE_DIGITAL
- OCR_EXTRACTED
- HUMAN_TRANSCRIBED

### FR-INGEST-003
OCR-derived content MUST NOT automatically become an EXACT_VERIFIED quote.

### FR-INGEST-004
Chunks are discovery units, not quotation authorities.

For exact quotation:
`retrieval result -> exact source span -> original/verified text -> quote`.

---

## 18. Foundational reference library

The foundational library MUST be logically isolated from ordinary external sources.

### FR-REFSRC-001
Foundational source records MUST include:
- source authority class;
- approved status;
- edition/version;
- approved by;
- approved at;
- checksum/version identifier when applicable.

### FR-REFSRC-002
AI MUST NOT autonomously add a new source to the approved foundational library.

### FR-REFSRC-003
The system MAY recommend candidate foundational sources, but adoption requires authorized human approval.

### FR-REFSRC-004
Reference hierarchy changes require Constitutional Authority and full audit.

---

## 19. Qur'an integrity requirements

### FR-QURAN-001
Qur'anic exact text MUST be retrieved from an approved structured source, not regenerated from model memory.

### FR-QURAN-002
A Qur'anic citation MUST retain:
- surah name;
- surah number;
- ayah number;
- exact approved text;
- source/version identifier.

### FR-QURAN-003
Output language editing MUST never modify Qur'anic exact text.

### FR-QURAN-004
Semantic retrieval MAY find potentially relevant verses, but retrieval MUST NOT itself constitute reference adjudication.

---

## 20. Sunnah / Hadith integrity requirements

### FR-HADITH-001
Hadith records SHOULD retain:
- collection/source;
- book;
- chapter where applicable;
- hadith number according to the approved edition;
- narrator when relevant;
- exact text;
- edition/verification metadata;
- page/location if applicable.

### FR-HADITH-002
The system MUST NOT synthesize multiple narrations into a single quotation presented as an original narration.

### FR-HADITH-003
Where numbering differs by edition, the edition context MUST remain attached.

---

## 21. Reference review

### FR-REF-001
Reference review MUST separate:
1. source text;
2. approved interpretation;
3. system application/inference;
4. practical judgment.

### FR-REF-002
Judgments MUST support:
- REFERENCE_SUPPORTED
- REFERENCE_CONSISTENT
- NOT_IN_CONFLICT
- REQUIRES_MODIFICATION
- REJECTED
- RESERVED

### FR-REF-003
Directness SHOULD support:
- DIRECT
- CLOSE
- INFERENTIAL
- EXPLORATORY

### FR-REF-004
Reserved judgments MUST support:
- BLOCKING_RESERVATION
- NON_BLOCKING_RESERVATION

### FR-REF-005
Where approved interpretations diverge, the system MUST support `REFERENCE_INTERPRETATION_DIVERGENCE` and display the differing interpretations and their implications.

### FR-REF-006
A system synthesis MUST be labeled SYSTEM_SYNTHESIS and MUST NOT be represented as approved interpretation.

---

## 22. Research question and plan

### FR-RSCH-001
A substantive research operation SHOULD begin with an explicit ResearchQuestion.

### FR-RSCH-002
A ResearchPlan SHOULD record:
- question;
- decision/use served by the answer;
- question type;
- risk/impact;
- desired evidence types;
- support-search track;
- challenge-search track;
- alternative-explanation track;
- sufficiency criteria;
- search budget.

### FR-RSCH-003
Question routing MUST support at least:
- REFERENCE
- EMPIRICAL
- HISTORICAL
- MECHANISM
- IMPLEMENTATION
- TECHNICAL
- CONTEXTUAL

### FR-RSCH-004
Reference authority order MUST remain distinct from research source-routing order.

---

## 23. Retrieval architecture

Retrieval SHOULD support:

- lexical retrieval;
- semantic retrieval;
- conceptual retrieval;
- mechanism retrieval;
- relationship retrieval;
- cross-project retrieval.

### FR-RET-001
The product MUST search current project/local library/accumulated memory before unnecessarily duplicating external research.

### FR-RET-002
Fresh external verification MUST still be used where time sensitivity or decision risk requires it.

### FR-RET-003
Query expansion SHOULD include:
- canonical terms;
- synonyms;
- translations;
- historical terminology;
- mechanisms;
- negative/failure formulations.

### FR-RET-004
The product MUST support multilingual search independent of output language.

### FR-RET-005
A canonical terminology layer MUST connect Arabic/French/English equivalents where possible.

---

## 24. External research and web search

### FR-WEB-001
External search providers MUST be abstracted behind a SearchProvider interface.

### FR-WEB-002
Version 1 SHOULD support provider-native web search where available and permit a generic external search adapter.

### FR-WEB-003
Web results MUST enter the source/evidence pipeline as candidate sources, not automatically as evidence.

### FR-WEB-004
The system MUST distinguish:
- no evidence found;
- search execution failure;
- source inaccessible;
- insufficient search coverage.

### FR-WEB-005
Search audit MUST record:
- question;
- date;
- provider/database searched;
- queries;
- languages;
- support/challenge/alternative track;
- relevant exclusions;
- unresolved gaps.

---

## 25. Confirmation-bias protection

### FR-BIAS-001
Important hypotheses MUST have separate:
- Support Track
- Challenge Track
- Alternative Explanation Track

### FR-BIAS-002
The UI MUST expose when counter-evidence search has not yet been completed.

### FR-BIAS-003
The system SHOULD proactively create competing hypotheses when strong alternative explanations appear.

### FR-BIAS-004
Research settings may change depth but MUST NOT disable the integrity requirement to search for meaningful counter-evidence on important claims.

---

## 26. Evidence model

### FR-EVID-001
Evidence MUST be a relationship between a source-derived or experiment-derived finding and a target claim/hypothesis/mechanism.

### FR-EVID-002
Evidence roles MUST support:
- SUPPORTS
- CONTRADICTS
- LIMITS
- QUALIFIES
- CONTEXTUALIZES

### FR-EVID-003
Evidence evaluation SHOULD consider:
- methodological quality;
- relevance;
- context fit;
- independence;
- directness;
- limitations;
- temporal relevance.

### FR-EVID-004
The product MUST NOT use a single opaque 0-100 “truth score”.

### FR-EVID-005
Evidence strength descriptors SHOULD support:
- UNSUBSTANTIATED
- WEAK
- PROMISING
- SUPPORTED
- STRONG
- ESTABLISHED_WITHIN_SCOPE

### FR-EVID-006
`CONTESTED` MUST be reserved for meaningful conflict between nontrivial evidence, not any weak contradictory source.

---

## 27. Evidence lineage and dependency

### FR-LINEAGE-001
Evidence/source relationships MUST support:
- CITES
- REPLICATES
- USES_DATA_FROM
- DERIVED_FROM
- SUMMARIZES
- REANALYZES
- TRANSLATES

### FR-LINEAGE-002
The system MUST detect or allow recording that multiple apparent sources depend on a common origin.

### FR-LINEAGE-003
AI-generated reports, summaries, and previous system outputs MUST NOT become independent evidence merely by being stored.

### FR-LINEAGE-004
Knowledge lineage SHOULD terminate at evidence-bearing origins whenever possible.

---

## 28. Transferability

### FR-TRANS-001
Reuse of knowledge across materially different populations/domains MUST include transferability assessment.

### FR-TRANS-002
Transferability states MUST support:
- DIRECTLY_RELEVANT
- PARTIALLY_TRANSFERABLE
- ANALOGICAL_ONLY
- NOT_TRANSFERABLE

### FR-TRANS-003
Cross-domain analogy MUST NOT be presented as direct evidence.

---

## 29. Temporal validity

### FR-TIME-001
Knowledge units MAY have temporal profiles:
- STABLE
- SLOW_CHANGING
- DYNAMIC
- HIGHLY_VOLATILE

### FR-TIME-002
The system MUST support:
- valid_from;
- last_verified_at;
- revalidation policy;
- source version/hash.

### FR-TIME-003
Time-sensitive knowledge that exceeds its revalidation policy MUST be marked REVALIDATION_REQUIRED before high-impact reuse.

---

## 30. Source-gap intelligence

### FR-GAP-001
When knowledge is insufficient, the system MUST create a SourceGap that identifies:
- missing knowledge;
- why it matters;
- impact if unresolved;
- desired source type;
- search/recommendation status.

### FR-GAP-002
The AI SHOULD recommend candidate sources with:
- rationale;
- expected contribution;
- scope;
- limitations;
- source role.

### FR-GAP-003
The product MUST not simply ask the researcher for “more sources” when it can identify what type of source is missing.

---

## 31. Research sufficiency

### FR-SUFF-001
Research sufficiency MUST be decision-relative.

### FR-SUFF-002
A sufficiency assessment MUST consider:
- support evidence;
- counter-evidence;
- alternative explanations;
- evidence independence;
- evidence diversity;
- context fit;
- critical unknowns;
- impact;
- reversibility;
- remaining uncertainty.

### FR-SUFF-003
Research conclusion states MUST support:
- SUFFICIENTLY_ANSWERED
- PARTIALLY_ANSWERED
- CONTESTED
- INSUFFICIENT_EVIDENCE
- RESEARCH_ROUTE_EXHAUSTED

### FR-SUFF-004
The system MAY recommend moving from literature research to a controlled experiment when additional reading has low marginal value.

---

## 32. Design synthesis

### FR-DESIGN-001
Before serious solution design, the system MUST produce Design Requirements.

### FR-DESIGN-002
Design requirements MUST be traceable to:
- purpose;
- reference constraints;
- human/context needs;
- supported/plausible mechanisms;
- evidence;
- risk;
- operational constraints.

### FR-DESIGN-003
The system MUST NOT assume the solution form in advance.

### FR-DESIGN-004
Design concept origin MUST be recordable:
- RESEARCHER
- AI
- SOURCE
- JOINT_SYNTHESIS
- PRIOR_PROJECT

### FR-DESIGN-005
Reference-rejected designs MUST remain in history; useful underlying mechanisms MAY be extracted and recombined into new designs.

### FR-DESIGN-006
The system MAY compare designs but SHOULD avoid replacing human design selection with an opaque “winner”.

---

## 33. Experiment model

### FR-EXP-001
A DesignHypothesis SHOULD state:
- intervention;
- target population;
- context;
- mechanism;
- expected outcome;
- measurement plan;
- failure conditions;
- side effects;
- stop conditions.

### FR-EXP-002
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

### FR-EXP-003
Observation, analyzed result, and interpretation MUST remain distinct entities/states.

### FR-EXP-004
An invalid experiment MUST NOT be represented simply as a failed hypothesis test.

---

## 34. Human-impact, ethics, and operational review

### FR-HUMAN-001
Experiments affecting people MUST trigger review for:
- privacy;
- consent where relevant;
- possible harm;
- authority;
- applicable law/policy;
- data handling;
- reversibility.

### FR-HUMAN-002
These operational checks MUST remain logically distinct from the governing reference ethical judgment.

### FR-HUMAN-003
Where an external legal/ethical/institutional approval is required, the product MUST represent it as an unresolved operational requirement.

---

## 35. Knowledge memory

### FR-KNOW-001
Knowledge lifecycle MUST support:
- PROJECT_FINDING
- LOCAL_RESULT
- REPEATED_LOCAL_RESULT
- ACCUMULATED_LOCAL_KNOWLEDGE
- CANDIDATE_OPERATING_RULE
- OPERATING_RULE

### FR-KNOW-002
Promotion MUST NOT be automatic.

### FR-KNOW-003
Accumulated knowledge MUST preserve:
- scope;
- contexts;
- evidence basis;
- contrary evidence;
- confidence;
- time sensitivity;
- provenance.

### FR-KNOW-004
Knowledge can be downgraded, contested, suspended, or revalidated.

### FR-KNOW-005
Operating Rules MUST remain distinct from foundational reference knowledge.

---

## 36. Terminology

### FR-TERM-001
The system MUST maintain canonical terminology records.

### FR-TERM-002
A term SHOULD support:
- original/canonical term;
- domain;
- definition;
- Arabic translation;
- French translation;
- English translation;
- alternative translations;
- retain-original preference;
- source/authority.

### FR-TERM-003
Translation integrity checks MUST detect strengthening/weakening of scientific claims such as changing association into causation.

---

## 37. Output system

Supported output types SHOULD include:
- research report;
- executive summary;
- decision brief;
- reference review;
- evidence map;
- hypothesis dossier;
- design specification;
- experiment protocol;
- learning review;
- project closure report.

### FR-OUT-001
Output modes SHOULD include:
- READABLE
- REFERENCED
- AUDIT

### FR-OUT-002
The output pipeline MUST execute:
1. claim verification;
2. citation verification;
3. exact quote verification;
4. reference hierarchy/integrity check;
5. terminology check;
6. translation-semantic check;
7. language editing;
8. final rendering.

### FR-OUT-003
Language editing MUST occur after quote integrity verification and MUST NOT mutate protected exact quotes.

### FR-OUT-004
The final output MUST be able to trace material factual/research claims back to evidence/source.

### FR-OUT-005
The system MUST support high-quality Arabic, English, and French prose rather than mechanical translation.

### FR-OUT-006
Exports MUST support at minimum Markdown and HTML.
Version 1 SHOULD also support DOCX and PDF.

---

## 38. Research state

### FR-STATE-001
At all times the project MUST be able to provide:
- current question;
- current mode;
- established findings;
- unresolved matters;
- active hypotheses;
- reservations;
- blocking issues;
- pending human decisions;
- recommended next action and why.

### FR-STATE-002
Research State MUST be persisted independently of LLM context.

### FR-STATE-003
Each research session SHOULD generate a Session Checkpoint summarizing:
- what was learned;
- what changed;
- affected hypotheses;
- sources used;
- new questions;
- pending decisions;
- proposed next step.

---

## 39. Scratch / free-thinking space

### FR-SCRATCH-001
The user MUST have a workspace where exploratory notes are not automatically promoted into formal knowledge.

### FR-SCRATCH-002
The user or AI MAY explicitly capture a note into a Research Core entity.

### FR-SCRATCH-003
AI MAY suggest capture but MUST NOT silently transform informal thinking into approved claims/hypotheses.

---

## 40. Events, actions, decisions, and approvals

### FR-EVENT-001
Material state changes MUST be represented by auditable events.

### FR-EVENT-002
Event and Action MUST remain distinct.

### FR-ACTION-001
Action authorization classes MUST support:
- AUTONOMOUS
- ACT_AND_NOTIFY
- REQUEST_APPROVAL
- FORBIDDEN

### FR-DEC-001
Decisions MUST record:
- question;
- options;
- AI recommendation if any;
- rationale;
- required role;
- blocking status;
- final decision;
- human justification.

### FR-DEC-002
AI recommendation MUST remain distinct from human decision.

### FR-APPROVAL-001
Formal approvals MUST require explicit UI action and MUST NOT be inferred from ambiguous natural language.

### FR-OVERRIDE-001
Methodological recommendations MAY be overridden with recorded reason where policy permits.

### FR-OVERRIDE-002
A path violating a non-overridable constitutional rule MUST be labeled OUTSIDE_METHODOLOGY_PATH rather than falsely reclassified as compliant.

---

## 41. Quality gates

The product MUST implement:

1. Framing Gate
2. Hypothesis Gate
3. Reference Gate
4. Evidence Sufficiency Gate
5. Design Readiness Gate
6. Experiment Readiness Gate
7. Learning Integrity Gate
8. Knowledge Promotion Gate
9. Project Closure Gate

Gate results MUST support:
- PASS
- PASS_WITH_RESERVATIONS
- NEEDS_HUMAN_DECISION
- BLOCKED

Gate thresholds MUST be risk-aware.

---

## 42. Risk model

The product MUST support assessment across:
- human impact;
- scale;
- reversibility;
- uncertainty;
- system autonomy.

Suggested operational levels:
- L1 EXPLORATORY
- L2 APPLIED
- L3 HIGH_IMPACT
- L4 CRITICAL

The product SHOULD use the same gate types with stricter thresholds at higher risk levels.

---

## 43. Degraded Decision Mode

### FR-DEGRADED-001
The system MUST support urgent decisions under incomplete evidence.

### FR-DEGRADED-002
Such decisions MUST be labeled `DECISION_UNDER_INCOMPLETE_EVIDENCE`.

### FR-DEGRADED-003
The product MUST display:
- what remains unverified;
- major uncertainty;
- risks;
- recommended later review.

### FR-DEGRADED-004
This mode MUST NOT bypass hard reference constraints.

---

## 44. Project closure and reopening

### FR-CLOSE-001
The system MUST support project endings:
- KNOWLEDGE_CONCLUSION
- HYPOTHESIS_CONCLUSION
- DECISION
- DESIGN
- EXPERIMENT_CONCLUSION
- PRODUCTION_DELIVERABLE
- JUSTIFIED_STOP

### FR-CLOSE-002
Closure MUST document:
- what was resolved;
- what remains unresolved;
- confidence/scope;
- knowledge promoted;
- open questions;
- limitations;
- reopen triggers.

### FR-CLOSE-003
The system proposes readiness; the human explicitly closes the project.

### FR-REOPEN-001
Closed projects MUST support reopening with explicit trigger and a new Research State while retaining prior closure history.

---

## 45. Portability and Research Core Package

### FR-PORT-001
The product MUST export/import a versioned Research Core Package.

### FR-PORT-002
The package MUST preserve:
- project identity;
- entity identities;
- source identities/metadata;
- relationships;
- versions;
- provenance;
- verification state;
- decisions;
- audit;
- methodology version;
- constitution version;
- schema version.

### FR-PORT-003
Assets MUST be optional and governed by portability/license policy.

### FR-PORT-004
Missing assets MUST result in `METADATA_ONLY` or appropriate source availability state, not deletion of the source or its relationships.

### FR-PORT-005
Imports MUST run schema compatibility validation and migration.

### FR-PORT-006
Trust cannot upgrade on import.

---

## 46. Product B AI architecture

Product B MUST implement an `Intelligence Access Layer`.

### 46.1 Provider interface

At minimum:

```text
AIProvider
- generate_structured()
- reason()
- tool_loop()
- analyze_context()
- summarize()
- healthcheck()
- capabilities()
```

Version 1 MUST include:
- Anthropic provider adapter
- OpenAI provider adapter

The rest of the application MUST NOT contain provider-specific research logic.

### 46.2 Model configuration

A model profile SHOULD define:
- provider;
- model identifier;
- intended task classes;
- cost/latency class;
- capabilities;
- maximum context assumptions;
- evaluation status;
- default/allowed tools.

The product MUST NOT hardcode one permanent model identifier as product logic.

### 46.3 Provider switching

Provider/model selection MAY be:
- project default;
- task-specific;
- admin policy;
- quality/cost policy.

Research Core semantics MUST remain unchanged when switching providers.

---

## 47. Controlled AI tool access

### FR-AI-TOOL-001
AI providers MUST NOT receive direct PostgreSQL credentials.

### FR-AI-TOOL-002
AI providers MUST NOT receive unrestricted filesystem access.

### FR-AI-TOOL-003
AI interaction MUST use registered controlled tools such as:
- get_project_state
- search_sources
- get_source_excerpt
- get_reference_source
- get_quran_ayah
- get_hadith_record
- get_claim_evidence
- get_hypothesis
- search_prior_projects
- search_external_web
- create_candidate_source
- propose_claim
- propose_hypothesis
- propose_event

### FR-AI-TOOL-004
Tools MUST enforce project permissions and sensitivity policy server-side.

### FR-AI-TOOL-005
Tool calls affecting approved state MUST pass through Policy Engine and required approval logic.

---

## 48. AI orchestration

The application MUST contain a Research Orchestrator that coordinates AI tasks while the Research Core controls valid transitions.

Principle:

> The LLM may propose analysis, events, actions, and conclusions. The application decides whether the proposal can mutate canonical state.

### FR-ORCH-001
LLM output that mutates canonical state MUST use structured schemas.

### FR-ORCH-002
Schema validation failures MUST be retried or surfaced; they MUST NOT produce partial silent mutations.

### FR-ORCH-003
High-impact changes SHOULD use a draft/proposal state before canonical acceptance.

### FR-ORCH-004
Long tasks MUST be cancellable and resumable where feasible.

### FR-ORCH-005
The system MUST preserve task status independent of the browser session.

---

## 49. Policy Engine

The Policy Engine MUST evaluate:

- current project/entity state;
- incoming event;
- methodology version;
- constitution version;
- risk level;
- permissions;
- operational constraints.

It MUST return:
- allowed actions;
- required actions;
- blocked actions;
- required decisions/approvals;
- gates to re-run;
- notifications.

Policy enforcement MUST exist in code/configuration, not only prompts.

---

## 50. Prompt and template management

### FR-PROMPT-001
System prompts, research templates, structured-output schemas, and critical instructions MUST be version-controlled.

### FR-PROMPT-002
A material AI-generated research action MUST record prompt/template version.

### FR-PROMPT-003
Prompt templates SHOULD distinguish:
- instructions;
- research context;
- retrieved sources;
- user input;
- tool results;
- output schema.

### FR-PROMPT-004
External source text MUST be clearly marked untrusted data and MUST NOT be interpreted as application instructions.

---

## 51. Prompt-injection protection

### FR-SEC-AI-001
External web/source content MUST be handled as untrusted content.

### FR-SEC-AI-002
Source content MUST NOT grant itself tool permissions.

### FR-SEC-AI-003
The system SHOULD extract structured evidence before allowing source content to participate in high-privilege agent loops.

### FR-SEC-AI-004
Dangerous/destructive tools MUST require policy approval and MUST NOT be callable solely because a retrieved document instructs the model to do so.

---

## 52. AI reliability registry and evaluation

The product MUST maintain an AI capability/reliability registry.

Evaluation dimensions SHOULD include:
- citation accuracy;
- exact quote fidelity;
- Qur'an/Hadith reference integrity;
- claim/source separation;
- counter-evidence retrieval;
- assumption detection;
- structured-output reliability;
- Arabic writing quality;
- French writing quality;
- English writing quality;
- tool-use correctness;
- hallucination rate;
- long-context consistency.

### FR-EVAL-001
Changing a model MUST NOT rewrite existing knowledge automatically.

### FR-EVAL-002
Model migrations SHOULD run a regression suite before changing defaults.

### FR-EVAL-003
Critical research flows MUST have golden test fixtures.

---

## 53. Reproducibility record

Material AI actions MUST record where available:
- provider;
- model identifier/version;
- methodology version;
- constitution version;
- prompt/template version;
- source IDs/excerpts supplied;
- tool outputs;
- structured result;
- timestamp;
- user/task ID.

The system MUST NOT require storage of hidden chain-of-thought.

---

## 54. Data sensitivity and external disclosure

Project sensitivity MUST support at least:
- PUBLIC
- NORMAL
- CONFIDENTIAL
- RESTRICTED
- CRITICAL

Default policy recommendation:

- PUBLIC: cloud AI allowed.
- NORMAL: cloud AI allowed.
- CONFIDENTIAL: cloud AI requires explicit project policy and selective context.
- RESTRICTED: external AI disabled by default; product should recommend Product C or explicit authorized exception.
- CRITICAL: external AI disabled; Product C recommended.

### FR-DATA-001
Every outbound AI request SHOULD be traceable to a disclosure record containing:
- project;
- provider;
- task;
- source/entity IDs included;
- data classification;
- timestamp.

### FR-DATA-002
The system MUST support redaction/context minimization before provider transmission.

### FR-DATA-003
Provider API keys MUST never be stored in source control or logs.

---

## 55. Local-first data architecture

The canonical project data MUST be local by default.

Recommended implementation:

- PostgreSQL + pgvector for structured data and vectors.
- Local object storage for source assets.
- Redis for background-job coordination.
- Dedicated worker process for long AI/research/indexing tasks.

The system MUST remain operable for reading and manual editing when cloud AI is unavailable.

---

## 56. Optional cloud research workspace/gateway

Product B MUST architect for an optional selective cloud workspace without making it canonical.

Two supported execution modes:

### Local Retrieval Mode
The local system retrieves only relevant excerpts and sends the necessary context in API requests.

### Selective Cloud Workspace Mode
The researcher explicitly selects project/source content to stage in a remote research workspace or gateway accessible through controlled tools.

Requirements:

### FR-CLOUD-001
No silent full-database synchronization.

### FR-CLOUD-002
Selection must be explicit and policy-checked.

### FR-CLOUD-003
A disclosure/export manifest MUST record what was staged.

### FR-CLOUD-004
The remote workspace MUST expose controlled authenticated tools/endpoints, not raw database credentials.

### FR-CLOUD-005
The local database remains canonical.

### FR-CLOUD-006
Remote content MAY have TTL/expiry and deletion controls.

### FR-CLOUD-007
The implementation SHOULD use a pluggable `CloudWorkspaceAdapter`; the first concrete remote provider may be chosen through an ADR during implementation.

---

## 57. Recommended technical architecture

The implementation SHOULD use a modular monolith for v1.

### Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS
- Accessible component system
- Client/server state separation
- SSE or WebSocket for long-job progress when needed

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- modular domain packages
- REST API plus event/progress stream

### Database
- PostgreSQL
- pgvector

### Background execution
- Redis
- Celery (or equivalent approved in an ADR)
- explicit job states, retries, cancellation

### Source storage
- filesystem-backed local object store for development
- S3-compatible abstraction
- optional MinIO local deployment

### Packaging/runtime
- Docker
- Docker Compose
- `.env`-based local secrets/config
- reproducible single-command local startup

Exact framework versions SHOULD be current supported stable versions at implementation start and MUST be pinned in lockfiles.

---

## 58. Domain architecture

The backend SHOULD be divided into bounded modules:

1. `project_workflow`
2. `reference_governance`
3. `sources_library`
4. `claims_evidence`
5. `hypothesis_lab`
6. `design_experiments`
7. `knowledge_memory`
8. `research_orchestration`
9. `outputs_integrity`
10. `governance_audit`
11. `portability`
12. `ai_gateway`
13. `search_retrieval`
14. `operational_constraints`

No module may bypass another module’s public service/contract solely for convenience.

---

## 59. Canonical data contracts

The repository SHOULD contain product-independent Research Core schemas in a dedicated versioned package.

Recommended:
`packages/research-core-contracts/`

It SHOULD include:
- JSON Schema and/or language-neutral schemas;
- enums;
- package manifest version;
- import/export contract;
- source identity contract;
- event and state contract.

The Python backend may expose Pydantic models aligned to these contracts.

The contract package MUST not contain OpenAI/Anthropic-specific structures.

---

## 60. Persistence principles

1. Major approved versions are immutable.
2. Canonical current state may point to the latest approved version.
3. Audit events are append-oriented.
4. The system is event-aware but v1 need not use full event sourcing.
5. AI drafts/proposals must not overwrite approved state silently.
6. Entity IDs must be globally stable UUIDs or equivalent portable IDs.
7. Soft-deletion/archival SHOULD be preferred for epistemically meaningful entities.

---

## 61. Search/indexing principles

The product SHOULD maintain:
- full-text index;
- vector index;
- metadata filters;
- source/edition/page anchors;
- mechanism/concept relationships.

Embedding implementation MUST be abstracted.

The default embedding approach SHOULD support Arabic, French, and English well.

A local embedding option SHOULD be preferred where practical to minimize external disclosure, but the exact model must be benchmarked rather than assumed.

---

## 62. Authentication and roles

The architecture MUST support:
- Researcher
- Project Lead
- Methodology Steward
- Constitutional Authority

V1 MAY launch in single-user mode but MUST NOT hardcode the assumption that only one actor can exist.

All approvals/decisions/audit records must identify actor.

Authentication implementation may begin with local accounts or a local owner account, but the domain must remain role-aware.

---

## 63. Settings architecture

Settings MUST be separated into:

### Researcher preferences
- research depth;
- dialogue density;
- critique intensity;
- AI initiative;
- research breadth;
- alternative generation;
- memory scope;
- output detail.

### Project configuration
- sensitivity;
- impact;
- execution policy;
- AI providers;
- budget;
- source policies.

### Methodology administration
- gate thresholds;
- evidence policies;
- promotion policies;
- research templates.

### Constitutional administration
- reference hierarchy;
- approved foundational sources;
- foundational rules.

Researcher preferences MUST NOT override constitutional rules.

---

## 64. Cost control

### FR-COST-001
The system MUST record AI usage/cost where provider data permits.

### FR-COST-002
The user SHOULD be able to configure:
- per-task budget;
- per-project budget;
- preferred model class;
- retry limits;
- deep-research permission.

### FR-COST-003
Budget exhaustion MUST end as `STOPPED_RESOURCE_CONSTRAINT`, not falsely `RESEARCH_COMPLETE`.

### FR-COST-004
The Orchestrator SHOULD use lower-cost models for tasks proven by evaluation to not require frontier reasoning.

---

## 65. Notifications and human attention

Notification levels:
- INFO
- ATTENTION
- DECISION_REQUIRED
- BLOCKING

The main user experience MUST contain a “Needs Your Attention” queue showing:
- pending approvals;
- blocking questions;
- reference reservations;
- source-access requests;
- evidence reviews;
- knowledge-promotion decisions.

The system SHOULD suppress low-value notifications for routine extraction/indexing.

---

## 66. Explainability actions

The UI SHOULD provide:

### Why?
Explain evidence, policy, reference judgment, and methodology behind a recommendation.

### Challenge this
Launch a challenge/counter-evidence research task.

### What if?
Evaluate consequences of changing/removing an assumption, mechanism, or condition.

These features MUST use stored traceable data, not a fabricated retrospective explanation.

---

## 67. Audit

The system MUST record:
- actor;
- event;
- entity;
- timestamp;
- previous/new state where relevant;
- methodology version;
- constitution version;
- AI model/provider for AI actions;
- approval/decision;
- reason.

Audit data SHOULD be exportable.

---

## 68. Security requirements

### SEC-001
No API keys in git.

### SEC-002
No secrets in browser bundles.

### SEC-003
Backend logs MUST redact provider keys/tokens and sensitive headers.

### SEC-004
AI providers have no raw database credentials.

### SEC-005
Database queries generated by LLM text MUST NOT be executed directly.

### SEC-006
Uploaded files MUST be validated at system boundaries.

### SEC-007
File paths MUST be sandboxed to configured storage roots.

### SEC-008
Source text is untrusted input for agent/tool purposes.

### SEC-009
Destructive administrative operations require explicit authorization.

### SEC-010
Export/import packages MUST validate manifest/schema/checksums before import.

### SEC-011
Provider/tool permissions MUST follow least privilege.

---

## 69. Reliability and recovery

### NFR-REL-001
The application MUST tolerate AI provider outage without corrupting state.

### NFR-REL-002
Background jobs MUST have durable status.

### NFR-REL-003
A failed AI response MUST NOT partially mutate canonical state.

### NFR-REL-004
Database migrations MUST be reversible where feasible and backed up before destructive transformations.

### NFR-REL-005
Local backup/restore documentation MUST be provided before v1.0 release.

---

## 70. Performance targets

Initial non-binding targets for local workstation:

- standard project page load: < 2 seconds excluding long background jobs;
- full-text/local metadata search: < 1 second for normal personal-library scale;
- vector search: < 2 seconds for typical local corpus;
- state-changing local API actions: < 500 ms excluding AI/search;
- AI tasks: asynchronous with visible progress when > 5 seconds;
- source ingestion: background task with progress/cancel status.

Performance targets may be revised after realistic corpus benchmarking.

---

## 71. Accessibility and internationalization

### NFR-I18N-001
The UI MUST support Arabic RTL, English LTR, and French LTR.

### NFR-I18N-002
Mixed Arabic/Latin scientific terminology MUST render correctly.

### NFR-I18N-003
The UI SHOULD meet WCAG 2.1 AA principles where practical.

### NFR-I18N-004
Dates, numbers, and citation formats SHOULD be locale-aware but stable in stored canonical data.

---

## 72. Observability

Local observability SHOULD include:
- structured application logs;
- background job logs;
- AI request metadata without sensitive payload by default;
- provider latency/error metrics;
- ingestion errors;
- search failures;
- gate failures.

The product MUST distinguish application error, provider error, search failure, and knowledge insufficiency.

---

## 73. Testing strategy

The repository MUST include:

### Unit tests
For:
- state transitions;
- policy rules;
- quality gates;
- source identity;
- import/export;
- trust preservation;
- reference enums/rules;
- quotation protection.

### Integration tests
For:
- database persistence;
- source ingestion;
- provider adapters with mocks;
- search adapter;
- background workers;
- export/import round trips.

### Contract tests
For:
- OpenAI adapter;
- Anthropic adapter;
- SearchProvider interface;
- CloudWorkspaceAdapter;
- Research Core package schema.

### End-to-end tests
At minimum:
1. Create project -> framing -> approve Problem Frame.
2. Add digital source -> extract -> cite.
3. Add physical metadata-only source -> Hybrid Access.
4. Create hypothesis -> evidence support/challenge.
5. Reference review -> reservation -> human decision.
6. Design -> experiment -> learning review.
7. Generate referenced output.
8. Export project -> import -> trust preserved.
9. Provider outage -> project remains usable.
10. Reopen closed project.

### Evaluation tests
Separate from ordinary software tests, using golden research fixtures.

---

## 74. AI evaluation acceptance suite

Before declaring v1.0 quality-ready, the system SHOULD meet approved thresholds on a maintained benchmark including:

- exact quote preservation;
- citation-source support;
- no invented Qur'an/Hadith quotations;
- reference/source/inference separation;
- counter-evidence discovery;
- hypothesis falsifier quality;
- assumption detection;
- structured output compliance;
- multilingual terminology consistency;
- Arabic prose quality;
- English prose quality;
- French prose quality;
- tool authorization compliance.

Thresholds must be stored in `docs/evaluation/QUALITY_GATES.md` and may evolve independently of software test pass/fail.

---

## 75. Recommended repository structure

```text
/
├─ apps/
│  └─ web/                         # Next.js frontend
├─ services/
│  ├─ api/                         # FastAPI application
│  └─ worker/                      # Background worker entrypoint
├─ packages/
│  └─ research-core-contracts/     # Language-neutral canonical contracts
├─ docs/
│  ├─ product/
│  │  ├─ PRD_PRODUCT_B.md
│  │  └─ RESEARCH_CORE_V1.md
│  ├─ architecture/
│  │  ├─ OVERVIEW.md
│  │  ├─ DATA_MODEL.md
│  │  ├─ AI_ORCHESTRATION.md
│  │  ├─ SECURITY.md
│  │  └─ PORTABILITY.md
│  ├─ adr/
│  ├─ implementation/
│  │  ├─ MASTER_PLAN.md
│  │  └─ STATUS.md
│  └─ evaluation/
│     └─ QUALITY_GATES.md
├─ infra/
│  └─ docker/
├─ tests/
│  └─ e2e/
├─ scripts/
├─ .github/
│  ├─ workflows/
│  ├─ ISSUE_TEMPLATE/
│  └─ PULL_REQUEST_TEMPLATE.md
├─ .claude/
│  ├─ settings.json
│  └─ rules/
├─ CLAUDE.md
├─ GITHUB_SETUP.md
├─ docker-compose.yml
├─ Makefile
├─ .env.example
└─ README.md
```

Claude Code may refine directories through ADRs, but MUST preserve the logical separation.

---

## 76. Development phases

### Phase 0 — Repository and platform foundation

Deliver:
- repository structure;
- Docker Compose;
- frontend/backend skeleton;
- PostgreSQL + pgvector;
- Redis/worker;
- CI;
- migration system;
- canonical contract package;
- audit framework;
- CLAUDE.md and GitHub rules.

Exit criteria:
- clean clone starts locally;
- CI green;
- migration and rollback smoke test;
- no product feature implemented outside architecture.

### Phase 1 — Project, framing, source library

Deliver:
- project lifecycle;
- Research State;
- research dialogue shell;
- Problem Frame;
- source work/edition/asset model;
- ingestion;
- Hybrid Source metadata;
- Library UI.

Exit criteria:
- full create -> frame -> approve flow;
- upload PDF and preserve page anchors;
- add metadata-only physical source;
- audit state changes.

### Phase 2 — Reference, claims, evidence, hypothesis

Deliver:
- claims/assumptions;
- foundational library;
- Qur'an structured retrieval;
- Hadith/source framework;
- reference judgments;
- evidence map;
- hypothesis lifecycle;
- mechanism entities.

Exit criteria:
- reference review trace is source -> interpretation -> system inference -> judgment;
- exact source quote is protected;
- hypothesis can be supported/contradicted without losing history.

### Phase 3 — Research engine and AI integration

Deliver:
- OpenAI adapter;
- Anthropic adapter;
- provider profiles;
- tool registry;
- Research Orchestrator;
- Policy Engine;
- structured outputs;
- web/search adapters;
- support/challenge/alternative research tracks;
- research audit;
- cost tracking.

Exit criteria:
- same research task can run with either provider;
- provider switch does not alter stored schema;
- no provider receives DB credentials;
- counter-evidence track demonstrably runs.

### Phase 4 — Design, experiments, memory

Deliver:
- Design Requirements;
- design concepts;
- Design Hypothesis;
- experiments;
- observations/results/interpretations;
- local knowledge promotion;
- operating rules;
- temporal validity.

Exit criteria:
- complete hypothesis -> design -> experiment -> learning workflow.

### Phase 5 — Outputs, portability, cloud workspace

Deliver:
- output composer;
- multilingual integrity;
- citation verifier;
- Markdown/HTML/DOCX/PDF export;
- Research Core Package import/export;
- selective optional cloud workspace/gateway adapter;
- disclosure manifest.

Exit criteria:
- export/import round trip preserves source identity and trust;
- untransferable asset becomes metadata-only;
- referenced output can trace claims to source.

### Phase 6 — Hardening and v1.0

Deliver:
- full E2E suite;
- security review;
- AI evaluation suite;
- performance benchmark;
- backup/restore;
- user documentation;
- release artifacts.

Exit criteria:
- Definition of Done for v1.0 satisfied.

---

## 77. Definition of Done — feature level

A feature is not done unless:

1. acceptance criteria are implemented;
2. unit/integration tests exist where appropriate;
3. frontend states include loading/error/empty/success;
4. audit requirements are implemented;
5. permissions/policy are enforced server-side;
6. migrations are included if data changes;
7. relevant documentation is updated;
8. no secrets are committed;
9. CI passes;
10. the PR links the GitHub issue and describes Research Core implications.

---

## 78. Definition of Done — Product B v1.0

Product B v1.0 is complete when:

- a researcher can create and complete an end-to-end research project;
- Research State survives sessions and provider changes;
- two AI providers are supported through abstraction;
- reference review is traceable and separates source/interpretation/inference/judgment;
- physical/restricted/metadata-only sources are usable through Hybrid Source Access;
- counter-evidence search is operational;
- evidence lineage exists;
- hypothesis and mechanism lifecycle works;
- design and experiment workflows work;
- accumulated local knowledge can be promoted with human approval;
- multilingual output-integrity checks work;
- Qur'an and exact foundational quotations are protected;
- project export/import preserves identity, provenance, trust, and source metadata;
- provider outage does not make project data unavailable;
- full GitHub CI passes;
- AI evaluation thresholds are met;
- a clean machine can run the product from documented setup.

---

# 79. GitHub development operating model for Claude Code

This section is normative for implementation.

## 79.1 Repository ownership

Use one private GitHub repository for Product B v1 unless a future ADR justifies splitting it.

The repository is the authoritative development record.

The PRD and Research Core specification MUST be committed before substantive implementation.

## 79.2 Default branch

Use `main` as the protected, always-buildable branch.

Direct feature development on `main` is prohibited.

Use short-lived branches:

- `feat/<issue>-<slug>`
- `fix/<issue>-<slug>`
- `refactor/<issue>-<slug>`
- `docs/<issue>-<slug>`
- `test/<issue>-<slug>`
- `chore/<issue>-<slug>`

Prefer squash merge into `main` to keep a linear issue-oriented history.

## 79.3 Commit convention

Use Conventional Commits:

- `feat:`
- `fix:`
- `refactor:`
- `test:`
- `docs:`
- `chore:`
- `perf:`
- `security:`

Commits should describe intent, not implementation trivia.

## 79.4 GitHub Issues

Claude Code MUST decompose the PRD into GitHub issues before large-scale implementation.

Issue labels SHOULD include:

**Type**
- `type:feature`
- `type:bug`
- `type:refactor`
- `type:docs`
- `type:test`
- `type:security`

**Domain**
- `domain:project`
- `domain:reference`
- `domain:sources`
- `domain:evidence`
- `domain:hypothesis`
- `domain:research`
- `domain:design`
- `domain:experiments`
- `domain:knowledge`
- `domain:outputs`
- `domain:ai`
- `domain:portability`
- `domain:infra`

**Priority**
- `P0`
- `P1`
- `P2`
- `P3`

Each issue MUST contain:
- objective;
- relevant PRD requirement IDs;
- dependencies;
- implementation notes;
- acceptance criteria;
- tests required;
- migration/security implications.

## 79.5 Pull requests

Every nontrivial issue MUST be implemented through a PR.

PR template MUST include:
- linked issue;
- summary;
- PRD requirement IDs;
- architecture impact;
- data migration impact;
- security/privacy impact;
- tests run;
- screenshots for UI changes;
- risks/known limitations;
- documentation updates.

Claude Code is authorized to:
- create branches;
- edit files;
- run tests;
- commit;
- push feature branches;
- open PRs;
- respond to CI failures;
- update PRs;
- merge routine PRs once all required checks pass and no blocking review remains.

Claude Code MUST NOT:
- force-push protected/shared branches;
- bypass failed checks;
- rewrite published history as a shortcut;
- delete repository history;
- commit secrets;
- merge a PR that knowingly violates the PRD/Core;
- silently alter constitutional methodology requirements.

If implementation requires a product-level change not covered by the PRD, Claude Code MUST create an ADR and a `needs-product-decision` issue rather than silently redefining the product.

## 79.6 Branch protection / ruleset

Protect `main`.

Required:
- pull request before merge;
- required status checks;
- conversation resolution;
- prevent force push;
- prevent branch deletion;
- linear history if compatible with chosen merge strategy.

If repository plan supports it, use a GitHub ruleset rather than overlapping branch-protection rules.

For a fully autonomous build, do not require a human approval on every routine PR; rely on CI plus automated review. Human approval should be reserved for flagged product/constitutional/security decisions.

## 79.7 Required CI checks

Recommended unique required checks:

- `frontend-lint`
- `frontend-typecheck`
- `frontend-unit`
- `backend-lint`
- `backend-typecheck`
- `backend-unit`
- `backend-integration`
- `migration-check`
- `contract-check`
- `e2e-smoke`
- `docker-build`

Never reuse identical required job names in different workflows.

## 79.8 GitHub Actions workflows

Create at minimum:

### `.github/workflows/ci.yml`
Runs on PR and main push.
- install dependencies;
- lint;
- type-check;
- unit tests;
- integration tests;
- contract validation;
- migration validation;
- Docker build.

### `.github/workflows/e2e.yml`
Runs E2E tests with isolated services.

### `.github/workflows/security.yml`
Runs dependency/security/static checks appropriate to stack.

### `.github/workflows/provider-contract.yml`
Manual/scheduled provider contract tests.
Uses protected environment secrets.
Must enforce a bounded request/budget test suite.

### `.github/workflows/release.yml`
On release tag:
- run full checks;
- build release artifacts;
- generate release notes;
- optionally publish container images;
- attach setup artifact/source bundle.

### `.github/workflows/claude.yml` (optional but recommended)
Claude Code GitHub Action for issue/PR tasks and `@claude` interactions.

## 79.9 Secrets

Never store provider credentials in code or committed config.

Use GitHub Actions secrets only for workflows that genuinely require live provider integration.

Normal CI SHOULD use mocks/fakes.

Suggested integration secrets:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`

For Claude Code GitHub Actions, use either:
- `ANTHROPIC_API_KEY`, or
- `CLAUDE_CODE_OAUTH_TOKEN`

according to the chosen Claude Code GitHub integration.

Use `.env.example` with placeholders only.

Local developer secrets belong in ignored local environment files.

## 79.10 GitHub environments

Create an `integration` environment for live provider tests.

Where GitHub plan capabilities permit, protect the environment and restrict access to secrets.

A later hosted deployment MAY add `staging` and `production`, but Product B v1 is local-first and MUST NOT require hosted deployment to function.

## 79.11 Releases

Use semantic versioning.

Suggested milestones:
- `v0.1.0` foundation
- `v0.2.0` framing/library
- `v0.3.0` evidence/hypothesis
- `v0.4.0` AI research engine
- `v0.5.0` design/experiments
- `v0.9.0` feature complete/beta
- `v1.0.0` quality-approved release

A release tag MUST only be created from `main`.

---

# 80. Claude Code implementation contract

Claude Code MUST treat:

1. `docs/product/PRD_PRODUCT_B.md`
2. `docs/product/RESEARCH_CORE_V1.md`
3. `CLAUDE.md`
4. approved ADRs

as the authority order for implementation.

Before coding, Claude Code MUST:

1. inspect the repository;
2. read the PRD and Research Core;
3. create/update `docs/implementation/MASTER_PLAN.md`;
4. create milestone/issues;
5. identify unresolved architectural decisions;
6. implement the smallest dependency-correct vertical slice first.

Claude Code SHOULD default to action rather than only describing code changes.

It MUST investigate existing files before making claims about the codebase.

It MUST not optimize merely to pass tests by hardcoding fixtures or bypassing real domain logic.

It MUST preserve Research Core semantics even if a simpler shortcut appears technically convenient.

It MUST keep provider-specific code behind adapters.

It MUST keep business rules out of prompts when they can be encoded as deterministic policy/state logic.

It MUST write migrations and tests with domain changes.

It MUST update `docs/implementation/STATUS.md` after each merged PR or milestone.

It MUST use ADRs for durable architectural decisions.

---

# 81. Architecture Decision Records

Create ADRs in `docs/adr/`.

Use format:

```text
# ADR-NNN: Title
Status: Proposed / Accepted / Superseded
Date:
Context:
Decision:
Alternatives considered:
Consequences:
Research Core impact:
Migration impact:
```

ADR required for changes such as:
- queue technology;
- cloud workspace concrete provider;
- authentication implementation;
- embedding model default;
- source parsing/OCR major stack;
- storage abstraction;
- major repository restructuring;
- policy-engine implementation approach.

An ADR must not override constitutional Core requirements.

---

# 82. Claude Code repository configuration

Root `CLAUDE.md` SHOULD remain concise and point to the PRD rather than duplicating it.

Use:
- `CLAUDE.md` for persistent project instructions;
- `.claude/settings.json` for shared Claude Code settings/hooks/permissions;
- `.claude/settings.local.json` for local uncommitted overrides;
- `.claude/rules/` for path/domain-scoped coding rules if useful.

Do not place secrets in any `.claude` file committed to git.

---

# 83. Initial vertical slice

The first real product slice after scaffolding MUST be:

```text
Create Project
  -> Research Dialogue
  -> Draft Problem Frame
  -> Explicit Human Approval
  -> Create Claim/Hypothesis
  -> Add/Index Local Source
  -> Retrieve Evidence
  -> Call Cloud AI through Provider Adapter
  -> Validate Structured Result
  -> Persist Event/Audit/Research State
  -> Display Updated Project State
```

This slice proves:
- UI/backend/database;
- local-first state;
- source retrieval;
- provider abstraction;
- structured output;
- human approval;
- audit;
- Research State.

Do not build advanced multi-agent behavior before this slice is reliable.

---

# 84. Explicit implementation constraints

Claude Code MUST NOT:

- use a single giant “system prompt” as the methodology engine;
- embed all domain logic in frontend state;
- let provider responses directly write the database;
- use raw model-generated SQL;
- delete historical hypothesis/Problem Frame versions;
- collapse SourceWork/SourceEdition/SourceAsset into one file record;
- treat chat history as canonical project memory;
- use AI output as independent evidence without provenance;
- upgrade source trust on import;
- bypass exact quotation verification;
- silently send entire projects to cloud providers;
- build Product C/local-LLM concerns into v1 unless they are clean provider interfaces needed for future replacement.

---

# 85. Open implementation choices

The following are intentionally left to implementation ADRs because they do not change product semantics:

- exact supported PostgreSQL major version;
- exact stable Node/Python versions;
- exact component library;
- exact Celery-equivalent if a better option is justified;
- first local multilingual embedding model;
- concrete optional cloud workspace provider;
- exact PDF/DOCX renderer;
- authentication mechanism for multi-user mode;
- exact web-search provider order.

Claude Code may choose a pragmatic default after evaluating maintainability, current stability, multilingual needs, and local-first constraints.

---

# 86. Product acceptance scenarios

A v1 acceptance review MUST successfully demonstrate:

### Scenario A — Raw question
User enters an ambiguous idea. System asks targeted questions, drafts Problem Frame, and waits for explicit approval.

### Scenario B — Physical book
User catalogs a physical book. Project later needs it. System recognizes the known source and creates a Hybrid Source Access request. Researcher provides exact pages. The system marks the excerpt with the appropriate verification state.

### Scenario C — Exact Qur'an citation
The system retrieves a verse from the approved structured source, preserves exact text, and produces the correct surah/ayah reference without language editing.

### Scenario D — Hypothesis challenge
A hypothesis has supporting evidence. User invokes “Challenge this.” System performs counter-search and alternative-explanation search, updates Evidence Map, and may downgrade the hypothesis.

### Scenario E — Effective but reference-rejected design
The system records empirical effectiveness evidence but blocks methodology approval of the design due to the reference judgment while preserving useful mechanisms for alternative design.

### Scenario F — Current legal constraint
A design is reference-consistent but current regulation prevents immediate implementation. System records the operational constraint without reclassifying the design as morally invalid.

### Scenario G — Provider switch
The same structured research task is executed using Anthropic and OpenAI adapters. Both outputs conform to the same Research Core schema; provider details remain audit metadata.

### Scenario H — Provider outage
Cloud AI fails. User can still browse, edit, inspect sources, review prior evidence, and export the project.

### Scenario I — Portable source without asset
Project is exported to another Research Suite product without a licensed PDF. Source identity, edition, evidence relationships, and verification state transfer; asset becomes unavailable/metadata-only.

### Scenario J — Urgent decision
User invokes Degraded Decision Mode. The system provides a decision brief explicitly marked incomplete, listing unresolved evidence and risks.

### Scenario K — Experimental learning
A design experiment produces unexpected results. System stores observation separately from interpretation and creates a new hypothesis rather than claiming automatic success/failure.

### Scenario L — Final output
The system generates an English, Arabic, or French report with verified quotations, consistent terminology, references, and an audit view mapping key claims to evidence.

---

# 87. Final product principle

Product B succeeds only if the researcher can trust that:

- the system knows what it knows;
- knows what it does not know;
- distinguishes source from interpretation;
- distinguishes reference judgment from empirical effectiveness;
- distinguishes governing ethics from current human operational constraints;
- exposes contradictory evidence;
- preserves exact quotations;
- does not silently rewrite research history;
- allows the human researcher to lead;
- remains portable to the rest of the Research Suite.

That trust is more important than maximizing the number of autonomous agent actions.

---

## Appendix A — Official implementation references for Claude Code / GitHub

Claude Code documentation:
- https://code.claude.com/docs/en/overview
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/github-actions

GitHub documentation:
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
- https://docs.github.com/en/actions/reference/security/secrets

These URLs are implementation references, not product requirements. If vendor behavior changes, the implementation must follow the current official documentation while preserving this PRD’s product semantics.
