// GENERATED FILE - DO NOT EDIT. Source: packages/research-core-contracts/schema/enums.schema.json
// Regenerate with: python scripts/contracts/generate_bindings.py

export const RESEARCH_CORE_VERSION = "1.0.0";
export const CONTRACT_SCHEMA_VERSION = "0.7.0";

/** Project lifecycle (Core §17, PRD §9). Distinct from ResearchMode. */
export const ProjectStatusValues = ["DRAFT", "FRAMING", "ACTIVE_RESEARCH", "ON_HOLD", "FROZEN", "READY_TO_CLOSE", "CLOSED", "REOPENED"] as const;
export type ProjectStatus = (typeof ProjectStatusValues)[number];

/** Current research mode (Core §17, PRD §9). Distinct from ProjectStatus. */
export const ResearchModeValues = ["EXPLORATION", "SCRUTINY", "REFERENCE_REVIEW", "RESEARCH", "SYNTHESIS", "DESIGN", "EXPERIMENT", "LEARNING", "EVALUATION"] as const;
export type ResearchMode = (typeof ResearchModeValues)[number];

/** Kinds of research starting input (Core §10, FR-PROJ-001). */
export const ProjectInputTypeValues = ["RAW_QUESTION", "IDEA", "PROBLEM", "HYPOTHESIS", "METHOD", "TOOL", "MODEL", "FULL_SYSTEM", "EXPERIMENTAL_RESULT", "EXISTING_PROJECT"] as const;
export type ProjectInputType = (typeof ProjectInputTypeValues)[number];

/** Project data sensitivity (PRD §54). */
export const SensitivityLevelValues = ["PUBLIC", "NORMAL", "CONFIDENTIAL", "RESTRICTED", "CRITICAL"] as const;
export type SensitivityLevel = (typeof SensitivityLevelValues)[number];

/** Operational risk levels (Core §61, PRD §42). */
export const RiskLevelValues = ["L1_EXPLORATORY", "L2_APPLIED", "L3_HIGH_IMPACT", "L4_CRITICAL"] as const;
export type RiskLevel = (typeof RiskLevelValues)[number];

/** Governing source hierarchy, top-down (Core §4, PRD §5.1). Order is normative: earlier values govern later ones. */
export const ReferenceAuthorityLayerValues = ["QURAN", "SUNNAH", "APPROVED_FOUNDATIONAL", "HISTORICAL_CIVILIZATIONAL", "SCIENTIFIC_EXPERIMENTAL", "PROFESSIONAL_FIELD", "PROJECT_LOCAL"] as const;
export type ReferenceAuthorityLayer = (typeof ReferenceAuthorityLayerValues)[number];

/** Six governing analytical categories; lenses, not sources (Core §6, PRD §5.2). */
export const ReferenceAnalyticalCategoryValues = ["FOUNDATIONAL_CONCEPTIONS_AND_TRUTHS", "PURPOSES_AND_GOALS", "VALUES_AND_EVALUATIVE_STANDARDS", "SUNAN_GOVERNING_PATTERNS", "GOVERNING_UNIVERSALS_AND_RULES", "BINDING_RULINGS_AND_LIMITS"] as const;
export type ReferenceAnalyticalCategory = (typeof ReferenceAnalyticalCategoryValues)[number];

/** Separation of source text, approved interpretation, system inference and practical judgment (Core §7, FR-REF-001, FR-REF-006). */
export const ReferenceReasoningLayerValues = ["SOURCE_TEXT", "APPROVED_INTERPRETATION", "SYSTEM_SYNTHESIS", "PRACTICAL_JUDGMENT"] as const;
export type ReferenceReasoningLayer = (typeof ReferenceReasoningLayerValues)[number];

/** Reference judgment states (Core §8, FR-REF-002). NOT_IN_CONFLICT must never be represented as REFERENCE_SUPPORTED. */
export const ReferenceJudgmentStateValues = ["REFERENCE_SUPPORTED", "REFERENCE_CONSISTENT", "NOT_IN_CONFLICT", "REQUIRES_MODIFICATION", "REJECTED", "RESERVED"] as const;
export type ReferenceJudgmentState = (typeof ReferenceJudgmentStateValues)[number];

/** Reservation kinds for RESERVED judgments (Core §8, FR-REF-004). */
export const ReservationTypeValues = ["BLOCKING_RESERVATION", "NON_BLOCKING_RESERVATION"] as const;
export type ReservationType = (typeof ReservationTypeValues)[number];

/** Directness of a reference judgment (Core §8, FR-REF-003). */
export const DirectnessValues = ["DIRECT", "CLOSE", "INFERENTIAL", "EXPLORATORY"] as const;
export type Directness = (typeof DirectnessValues)[number];

/** Operational reality constraints; distinct from reference judgment (Core §5, PRD §5.3). */
export const OperationalConstraintStateValues = ["INFORMATIONAL", "REQUIRES_REDESIGN", "REQUIRES_EXTERNAL_APPROVAL", "BLOCKS_CURRENT_EXECUTION"] as const;
export type OperationalConstraintState = (typeof OperationalConstraintStateValues)[number];

/** Epistemic categories of statements (Core §14, FR-FRAME-004). */
export const EpistemicCategoryValues = ["OBSERVATION", "FACTUAL_CLAIM", "INTERPRETATION", "ASSUMPTION", "HYPOTHESIS", "UNKNOWN"] as const;
export type EpistemicCategory = (typeof EpistemicCategoryValues)[number];

/** Who asserted a statement (Core §14). */
export const StatementOriginValues = ["RESEARCHER_STATED", "SYSTEM_INFERRED", "SOURCE_STATED", "EXPERIMENT_OBSERVED"] as const;
export type StatementOrigin = (typeof StatementOriginValues)[number];

/** Claim types (Core §18, FR-CLAIM-001). */
export const ClaimTypeValues = ["OBSERVATION", "FACTUAL_CLAIM", "CAUSAL_CLAIM", "INTERPRETATION", "NORMATIVE_CLAIM", "MECHANISM_CLAIM", "DESIGN_CLAIM"] as const;
export type ClaimType = (typeof ClaimTypeValues)[number];

/** Assumption origin (Core §19, FR-CLAIM-003). SYSTEM_INFERRED stays labeled until confirmed/reclassified. */
export const AssumptionOriginValues = ["EXPLICIT", "SYSTEM_INFERRED", "SOURCE_DERIVED"] as const;
export type AssumptionOrigin = (typeof AssumptionOriginValues)[number];

/** Assumption criticality (Core §19, FR-CLAIM-004). */
export const CriticalityValues = ["LOW", "MEDIUM", "HIGH", "FOUNDATIONAL"] as const;
export type Criticality = (typeof CriticalityValues)[number];

/** Problem Frame version status (Core §12-13, FR-FRAME-006/007). */
export const ProblemFrameStatusValues = ["DRAFT", "APPROVED", "SUPERSEDED"] as const;
export type ProblemFrameStatus = (typeof ProblemFrameStatusValues)[number];

/** Hypothesis workflow lifecycle (Core §20, FR-HYP-001). */
export const HypothesisLifecycleStateValues = ["SIGNAL", "IDEA", "FORMULATED_HYPOTHESIS", "UNDER_REFERENCE_REVIEW", "UNDER_SCRUTINY", "UNDER_RESEARCH", "ASSESSED", "ELIGIBLE_FOR_DESIGN", "USED_IN_DESIGN", "TESTED_IN_PRACTICE"] as const;
export type HypothesisLifecycleState = (typeof HypothesisLifecycleStateValues)[number];

/** Hypothesis epistemic assessment (Core §20, FR-HYP-002). */
export const HypothesisEpistemicStateValues = ["PROMISING", "SUPPORTED", "WEAKENED", "CONTESTED", "REFUTED", "UNRESOLVED"] as const;
export type HypothesisEpistemicState = (typeof HypothesisEpistemicStateValues)[number];

/** Mechanism states (Core §22, FR-MECH-002). */
export const MechanismStatusValues = ["PROPOSED", "UNDER_INVESTIGATION", "PLAUSIBLE", "SUPPORTED", "DISPUTED", "WEAKENED", "REJECTED", "CONTEXT_DEPENDENT"] as const;
export type MechanismStatus = (typeof MechanismStatusValues)[number];

/** Source access modes (Core §24, FR-SRC-004). Metadata presence never implies asset availability. */
export const SourceAccessModeValues = ["DIRECT_DIGITAL", "PHYSICAL", "RESEARCHER_MEDIATED", "RESTRICTED", "METADATA_ONLY"] as const;
export type SourceAccessMode = (typeof SourceAccessModeValues)[number];

/** Source verification states (Core §25, FR-SRC-005). Import never raises this; only an explicit ReverificationEvent may. */
export const SourceVerificationStateValues = ["MACHINE_VERIFIED", "RESEARCHER_SUPPLIED_EXACT", "RESEARCHER_REPORTED_SOURCE_CONTENT", "METADATA_ONLY", "UNVERIFIED"] as const;
export type SourceVerificationState = (typeof SourceVerificationStateValues)[number];

/** Concrete asset kinds (PRD §15). */
export const SourceAssetKindValues = ["PDF", "EPUB", "HTML_CAPTURE", "IMAGE", "SCAN", "AUDIO", "LOCAL_TEXT", "REMOTE_URL", "OTHER"] as const;
export type SourceAssetKind = (typeof SourceAssetKindValues)[number];

/** Origin of source text (Core §28, FR-INGEST-002). OCR is never automatically exact. */
export const TextOriginValues = ["NATIVE_DIGITAL", "OCR_EXTRACTED", "HUMAN_TRANSCRIBED"] as const;
export type TextOrigin = (typeof TextOriginValues)[number];

/** Where a source lead came from. Web results are leads, never evidence (FR-WEB-003). */
export const SourceLeadOriginValues = ["RESEARCHER_MEMORY", "WEB_SEARCH"] as const;
export type SourceLeadOrigin = (typeof SourceLeadOriginValues)[number];

/** Researcher memory of a source is a lead until verified (Core §27). */
export const SourceLeadStateValues = ["SOURCE_LEAD", "VERIFIED", "DISCARDED"] as const;
export type SourceLeadState = (typeof SourceLeadStateValues)[number];

/** Evidence roles (Core §33, FR-EVID-002). */
export const EvidenceRoleValues = ["SUPPORTS", "CONTRADICTS", "LIMITS", "QUALIFIES", "CONTEXTUALIZES"] as const;
export type EvidenceRole = (typeof EvidenceRoleValues)[number];

/** Qualitative evidence strength; no 0-100 truth score (Core §34, FR-EVID-004/005). */
export const EvidenceStrengthValues = ["UNSUBSTANTIATED", "WEAK", "PROMISING", "SUPPORTED", "STRONG", "ESTABLISHED_WITHIN_SCOPE"] as const;
export type EvidenceStrength = (typeof EvidenceStrengthValues)[number];

/** Evidence lineage/dependency relations (Core §35, FR-LINEAGE-001). */
export const LineageRelationValues = ["CITES", "REPLICATES", "USES_DATA_FROM", "DERIVED_FROM", "SUMMARIZES", "REANALYZES", "TRANSLATES"] as const;
export type LineageRelation = (typeof LineageRelationValues)[number];

/** Who/what produced a piece of content (Core §7, §36, §71). AI_GENERATED content is never independent evidence. */
export const ProvenanceKindValues = ["HUMAN_INPUT", "SOURCE_DERIVED", "AI_GENERATED", "EXPERIMENT_DERIVED", "SYSTEM_COMPUTED", "IMPORTED"] as const;
export type ProvenanceKind = (typeof ProvenanceKindValues)[number];

/** Question routing types (Core §37, FR-RSCH-003). */
export const ResearchQuestionTypeValues = ["REFERENCE", "EMPIRICAL", "HISTORICAL", "MECHANISM", "IMPLEMENTATION", "TECHNICAL", "CONTEXTUAL"] as const;
export type ResearchQuestionType = (typeof ResearchQuestionTypeValues)[number];

/** Counter-evidence architecture tracks (Core §41, FR-BIAS-001). */
export const ResearchTrackValues = ["SUPPORT", "CHALLENGE", "ALTERNATIVE_EXPLANATION"] as const;
export type ResearchTrack = (typeof ResearchTrackValues)[number];

/** Retrieval layers (Core §38). */
export const ResearchLayerValues = ["APPROVED_REFERENCE_LIBRARY", "PROJECT_LIBRARY", "RESEARCH_MEMORY", "EXTERNAL_KNOWLEDGE"] as const;
export type ResearchLayer = (typeof ResearchLayerValues)[number];

/** Search/tool outcome; failure is never evidence absence (Core §72, FR-WEB-004). */
export const ResearchOutcomeKindValues = ["RESULTS_FOUND", "NO_RELEVANT_EVIDENCE_FOUND", "RESEARCH_EXECUTION_FAILURE", "INSUFFICIENT_SEARCH_COVERAGE", "SOURCE_INACCESSIBLE", "STOPPED_RESOURCE_CONSTRAINT"] as const;
export type ResearchOutcomeKind = (typeof ResearchOutcomeKindValues)[number];

/** Research sufficiency conclusions (Core §46, FR-SUFF-003). */
export const SufficiencyResultValues = ["SUFFICIENTLY_ANSWERED", "PARTIALLY_ANSWERED", "CONTESTED", "INSUFFICIENT_EVIDENCE", "RESEARCH_ROUTE_EXHAUSTED"] as const;
export type SufficiencyResult = (typeof SufficiencyResultValues)[number];

/** Cross-context transferability (Core §44, FR-TRANS-002). */
export const TransferabilityStateValues = ["DIRECTLY_RELEVANT", "PARTIALLY_TRANSFERABLE", "ANALOGICAL_ONLY", "NOT_TRANSFERABLE"] as const;
export type TransferabilityState = (typeof TransferabilityStateValues)[number];

/** Temporal validity profiles (Core §45, FR-TIME-001). */
export const TemporalProfileValues = ["STABLE", "SLOW_CHANGING", "DYNAMIC", "HIGHLY_VOLATILE"] as const;
export type TemporalProfile = (typeof TemporalProfileValues)[number];

/** Design/idea origin (Core §48, FR-DESIGN-004). */
export const DesignOriginValues = ["RESEARCHER", "AI", "SOURCE", "JOINT_SYNTHESIS", "PRIOR_PROJECT"] as const;
export type DesignOrigin = (typeof DesignOriginValues)[number];

/** Experiment workflow (Core §50, FR-EXP-002). */
export const ExperimentStateValues = ["PROPOSED", "PROTOCOL_DEFINED", "RISK_REVIEW", "APPROVED", "RUNNING", "DATA_COLLECTION_COMPLETE", "ANALYSIS", "INTERPRETED", "CLOSED", "PAUSED", "ABORTED", "INVALIDATED"] as const;
export type ExperimentState = (typeof ExperimentStateValues)[number];

/** Local knowledge lifecycle; promotion is never automatic (Core §52, FR-KNOW-001). */
export const KnowledgeLifecycleStageValues = ["PROJECT_FINDING", "LOCAL_RESULT", "REPEATED_LOCAL_RESULT", "ACCUMULATED_LOCAL_KNOWLEDGE", "CANDIDATE_OPERATING_RULE", "OPERATING_RULE"] as const;
export type KnowledgeLifecycleStage = (typeof KnowledgeLifecycleStageValues)[number];

/** Knowledge standing independent of lifecycle stage (Core §52, FR-KNOW-004, FR-TIME-003). */
export const KnowledgeStatusValues = ["ACTIVE", "DOWNGRADED", "CONTESTED", "SUSPENDED", "REVALIDATION_REQUIRED"] as const;
export type KnowledgeStatus = (typeof KnowledgeStatusValues)[number];

/** AI action authority classes; policy lives in the system, not prompts (Core §57, FR-ACTION-001). */
export const ActionAuthorizationClassValues = ["AUTONOMOUS", "ACT_AND_NOTIFY", "REQUEST_APPROVAL", "FORBIDDEN"] as const;
export type ActionAuthorizationClass = (typeof ActionAuthorizationClassValues)[number];

/** Whether a path is within the methodology (Core §59, §62, FR-OVERRIDE-002, FR-DEGRADED-002). */
export const MethodologyPathStatusValues = ["COMPLIANT", "OVERRIDDEN_WITH_REASON", "DECISION_UNDER_INCOMPLETE_EVIDENCE", "OUTSIDE_METHODOLOGY_PATH"] as const;
export type MethodologyPathStatus = (typeof MethodologyPathStatusValues)[number];

/** Quality gates (Core §60, PRD §41). */
export const QualityGateTypeValues = ["FRAMING", "HYPOTHESIS", "REFERENCE", "EVIDENCE_SUFFICIENCY", "DESIGN_READINESS", "EXPERIMENT_READINESS", "LEARNING_INTEGRITY", "KNOWLEDGE_PROMOTION", "PROJECT_CLOSURE"] as const;
export type QualityGateType = (typeof QualityGateTypeValues)[number];

/** Quality gate results (Core §60, PRD §41). */
export const QualityGateResultValues = ["PASS", "PASS_WITH_RESERVATIONS", "NEEDS_HUMAN_DECISION", "BLOCKED"] as const;
export type QualityGateResult = (typeof QualityGateResultValues)[number];

/** Project closure types (Core §66, FR-CLOSE-001). */
export const ClosureTypeValues = ["KNOWLEDGE_CONCLUSION", "HYPOTHESIS_CONCLUSION", "DECISION", "DESIGN", "EXPERIMENT_CONCLUSION", "PRODUCTION_DELIVERABLE", "JUSTIFIED_STOP"] as const;
export type ClosureType = (typeof ClosureTypeValues)[number];

/** Kind of actor behind an event/approval (PRD §62, §67). */
export const ActorKindValues = ["HUMAN", "AI", "SYSTEM"] as const;
export type ActorKind = (typeof ActorKindValues)[number];

/** Role-aware domain; v1 may be single-user but must not assume one actor (PRD §62). */
export const ActorRoleValues = ["RESEARCHER", "PROJECT_LEAD", "METHODOLOGY_STEWARD", "CONSTITUTIONAL_AUTHORITY", "SYSTEM"] as const;
export type ActorRole = (typeof ActorRoleValues)[number];

/** Human attention levels (PRD §65). */
export const NotificationLevelValues = ["INFO", "ATTENTION", "DECISION_REQUIRED", "BLOCKING"] as const;
export type NotificationLevel = (typeof NotificationLevelValues)[number];

/** Output modes (FR-OUT-001). */
export const OutputModeValues = ["READABLE", "REFERENCED", "AUDIT"] as const;
export type OutputMode = (typeof OutputModeValues)[number];

/** First-class research/output languages (PRD §3.1, Core §40). */
export const LanguageCodeValues = ["ar", "en", "fr"] as const;
export type LanguageCode = (typeof LanguageCodeValues)[number];

/** Hybrid Source Access request lifecycle (Core §26, FR-HYBRID-001). */
export const SourceAccessRequestStatusValues = ["OPEN", "PARTIALLY_FULFILLED", "FULFILLED", "CANCELLED"] as const;
export type SourceAccessRequestStatus = (typeof SourceAccessRequestStatusValues)[number];

/** Accepted forms of a researcher response to a source access request (FR-HYBRID-003). */
export const AccessResponseFormValues = ["EXACT_TEXT", "PAGE_IMAGES", "RESEARCHER_SUMMARY", "RESEARCHER_ATTESTATION", "DIGITAL_ASSET"] as const;
export type AccessResponseForm = (typeof AccessResponseFormValues)[number];

/** Priority of requests and work items. */
export const PriorityValues = ["LOW", "MEDIUM", "HIGH", "URGENT"] as const;
export type Priority = (typeof PriorityValues)[number];

/** Decision record lifecycle; AI recommendation stays distinct from the human decision (FR-DEC-001/002). */
export const DecisionStatusValues = ["OPEN", "DECIDED", "WITHDRAWN"] as const;
export type DecisionStatus = (typeof DecisionStatusValues)[number];

/** Outcome of an explicit human approval action (FR-APPROVAL-001). */
export const ApprovalOutcomeValues = ["APPROVED", "REJECTED"] as const;
export type ApprovalOutcome = (typeof ApprovalOutcomeValues)[number];

/** Source asset ingestion state (PRD §17). */
export const IngestionStatusValues = ["NOT_STARTED", "QUEUED", "RUNNING", "COMPLETE", "FAILED", "NOT_APPLICABLE"] as const;
export type IngestionStatus = (typeof IngestionStatusValues)[number];

/** Claim workflow state; independent of epistemic strength (Core §16, §18, FR-CLAIM-002). */
export const ClaimWorkflowStateValues = ["PROPOSED", "ACTIVE", "UNDER_REVIEW", "RETIRED"] as const;
export type ClaimWorkflowState = (typeof ClaimWorkflowStateValues)[number];

/** Assumption review status; SYSTEM_INFERRED assumptions stay UNCONFIRMED until a human acts (Core §19, FR-CLAIM-003). */
export const AssumptionStatusValues = ["UNCONFIRMED", "CONFIRMED", "REJECTED", "RECLASSIFIED"] as const;
export type AssumptionStatus = (typeof AssumptionStatusValues)[number];

/** Open question lifecycle (Core §15, §37). */
export const OpenQuestionStatusValues = ["OPEN", "ANSWERED", "CLOSED_UNANSWERED"] as const;
export type OpenQuestionStatus = (typeof OpenQuestionStatusValues)[number];

/** Evidence pipeline: candidate -> assessment -> accepted evidence (Core §32). */
export const EvidenceStatusValues = ["CANDIDATE", "ACCEPTED", "REJECTED"] as const;
export type EvidenceStatus = (typeof EvidenceStatusValues)[number];

/** What evidence can bear on (FR-EVID-001). */
export const EvidenceTargetTypeValues = ["CLAIM", "HYPOTHESIS", "MECHANISM", "DESIGN_CONCEPT"] as const;
export type EvidenceTargetType = (typeof EvidenceTargetTypeValues)[number];

/** What a design requirement is derived from (FR-DESIGN-002, Core §47). */
export const DesignRequirementBasisValues = ["PURPOSE", "REFERENCE_CONSTRAINT", "HUMAN_CONTEXT_NEED", "MECHANISM", "EVIDENCE", "RISK", "OPERATIONAL_CONSTRAINT"] as const;
export type DesignRequirementBasis = (typeof DesignRequirementBasisValues)[number];

/** Design requirement priority. */
export const RequirementPriorityValues = ["MUST", "SHOULD", "COULD"] as const;
export type RequirementPriority = (typeof RequirementPriorityValues)[number];

/** Requirement versions are never edited; a revision supersedes (Core §47). AI-proposed requirements stay PROPOSED until a human confirms them. */
export const DesignRequirementStatusValues = ["PROPOSED", "ACTIVE", "SUPERSEDED", "WITHDRAWN"] as const;
export type DesignRequirementStatus = (typeof DesignRequirementStatusValues)[number];

/** Design concept status; selection is a human decision (FR-DESIGN-006). Rejected designs stay in history (FR-DESIGN-005). */
export const DesignConceptStatusValues = ["PROPOSED", "UNDER_REVIEW", "SELECTED", "REJECTED", "WITHDRAWN"] as const;
export type DesignConceptStatus = (typeof DesignConceptStatusValues)[number];

/** How a design concept addresses a requirement. */
export const RequirementCoverageValues = ["MEETS", "PARTIAL", "NOT_ADDRESSED", "CONFLICTS"] as const;
export type RequirementCoverage = (typeof RequirementCoverageValues)[number];

/** Why a design was rejected; REFERENCE rejections keep reusable mechanisms visible (FR-DESIGN-005). */
export const RejectionGroundValues = ["REFERENCE", "EVIDENCE", "OPERATIONAL", "FEASIBILITY", "OTHER"] as const;
export type RejectionGround = (typeof RejectionGroundValues)[number];

/** Foundational source approval state; only APPROVED sources are served (FR-REFSRC-001..003). */
export const FoundationalSourceStatusValues = ["STAGED", "APPROVED", "RETIRED"] as const;
export type FoundationalSourceStatus = (typeof FoundationalSourceStatusValues)[number];

/** Kind of human-made operational constraint (Core §5, PRD §5.3). */
export const ConstraintKindValues = ["LAW", "REGULATION", "CONTRACT", "LICENSE", "INSTITUTIONAL_POLICY", "AUTHORIZATION", "OTHER"] as const;
export type ConstraintKind = (typeof ConstraintKindValues)[number];
