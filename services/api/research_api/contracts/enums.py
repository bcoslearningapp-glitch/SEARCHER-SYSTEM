"""GENERATED FILE - DO NOT EDIT. Source: packages/research-core-contracts/schema/enums.schema.json

Regenerate with: python scripts/contracts/generate_bindings.py
"""

from __future__ import annotations

from enum import StrEnum

RESEARCH_CORE_VERSION = "1.0.0"
CONTRACT_SCHEMA_VERSION = "0.12.0"


class ProjectStatus(StrEnum):
    """Project lifecycle (Core §17, PRD §9). Distinct from ResearchMode."""

    DRAFT = "DRAFT"
    FRAMING = "FRAMING"
    ACTIVE_RESEARCH = "ACTIVE_RESEARCH"
    ON_HOLD = "ON_HOLD"
    FROZEN = "FROZEN"
    READY_TO_CLOSE = "READY_TO_CLOSE"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class ResearchMode(StrEnum):
    """Current research mode (Core §17, PRD §9). Distinct from ProjectStatus."""

    EXPLORATION = "EXPLORATION"
    SCRUTINY = "SCRUTINY"
    REFERENCE_REVIEW = "REFERENCE_REVIEW"
    RESEARCH = "RESEARCH"
    SYNTHESIS = "SYNTHESIS"
    DESIGN = "DESIGN"
    EXPERIMENT = "EXPERIMENT"
    LEARNING = "LEARNING"
    EVALUATION = "EVALUATION"


class ProjectInputType(StrEnum):
    """Kinds of research starting input (Core §10, FR-PROJ-001)."""

    RAW_QUESTION = "RAW_QUESTION"
    IDEA = "IDEA"
    PROBLEM = "PROBLEM"
    HYPOTHESIS = "HYPOTHESIS"
    METHOD = "METHOD"
    TOOL = "TOOL"
    MODEL = "MODEL"
    FULL_SYSTEM = "FULL_SYSTEM"
    EXPERIMENTAL_RESULT = "EXPERIMENTAL_RESULT"
    EXISTING_PROJECT = "EXISTING_PROJECT"


class SensitivityLevel(StrEnum):
    """Project data sensitivity (PRD §54)."""

    PUBLIC = "PUBLIC"
    NORMAL = "NORMAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    CRITICAL = "CRITICAL"


class RiskLevel(StrEnum):
    """Operational risk levels (Core §61, PRD §42)."""

    L1_EXPLORATORY = "L1_EXPLORATORY"
    L2_APPLIED = "L2_APPLIED"
    L3_HIGH_IMPACT = "L3_HIGH_IMPACT"
    L4_CRITICAL = "L4_CRITICAL"


class ReferenceAuthorityLayer(StrEnum):
    """Governing source hierarchy, top-down (Core §4, PRD §5.1). Order is normative: earlier values govern later ones."""

    QURAN = "QURAN"
    SUNNAH = "SUNNAH"
    APPROVED_FOUNDATIONAL = "APPROVED_FOUNDATIONAL"
    HISTORICAL_CIVILIZATIONAL = "HISTORICAL_CIVILIZATIONAL"
    SCIENTIFIC_EXPERIMENTAL = "SCIENTIFIC_EXPERIMENTAL"
    PROFESSIONAL_FIELD = "PROFESSIONAL_FIELD"
    PROJECT_LOCAL = "PROJECT_LOCAL"


class ReferenceAnalyticalCategory(StrEnum):
    """Six governing analytical categories; lenses, not sources (Core §6, PRD §5.2)."""

    FOUNDATIONAL_CONCEPTIONS_AND_TRUTHS = "FOUNDATIONAL_CONCEPTIONS_AND_TRUTHS"
    PURPOSES_AND_GOALS = "PURPOSES_AND_GOALS"
    VALUES_AND_EVALUATIVE_STANDARDS = "VALUES_AND_EVALUATIVE_STANDARDS"
    SUNAN_GOVERNING_PATTERNS = "SUNAN_GOVERNING_PATTERNS"
    GOVERNING_UNIVERSALS_AND_RULES = "GOVERNING_UNIVERSALS_AND_RULES"
    BINDING_RULINGS_AND_LIMITS = "BINDING_RULINGS_AND_LIMITS"


class ReferenceReasoningLayer(StrEnum):
    """Separation of source text, approved interpretation, system inference and practical judgment (Core §7, FR-REF-001, FR-REF-006)."""

    SOURCE_TEXT = "SOURCE_TEXT"
    APPROVED_INTERPRETATION = "APPROVED_INTERPRETATION"
    SYSTEM_SYNTHESIS = "SYSTEM_SYNTHESIS"
    PRACTICAL_JUDGMENT = "PRACTICAL_JUDGMENT"


class ReferenceJudgmentState(StrEnum):
    """Reference judgment states (Core §8, FR-REF-002). NOT_IN_CONFLICT must never be represented as REFERENCE_SUPPORTED."""

    REFERENCE_SUPPORTED = "REFERENCE_SUPPORTED"
    REFERENCE_CONSISTENT = "REFERENCE_CONSISTENT"
    NOT_IN_CONFLICT = "NOT_IN_CONFLICT"
    REQUIRES_MODIFICATION = "REQUIRES_MODIFICATION"
    REJECTED = "REJECTED"
    RESERVED = "RESERVED"


class ReservationType(StrEnum):
    """Reservation kinds for RESERVED judgments (Core §8, FR-REF-004)."""

    BLOCKING_RESERVATION = "BLOCKING_RESERVATION"
    NON_BLOCKING_RESERVATION = "NON_BLOCKING_RESERVATION"


class Directness(StrEnum):
    """Directness of a reference judgment (Core §8, FR-REF-003)."""

    DIRECT = "DIRECT"
    CLOSE = "CLOSE"
    INFERENTIAL = "INFERENTIAL"
    EXPLORATORY = "EXPLORATORY"


class OperationalConstraintState(StrEnum):
    """Operational reality constraints; distinct from reference judgment (Core §5, PRD §5.3)."""

    INFORMATIONAL = "INFORMATIONAL"
    REQUIRES_REDESIGN = "REQUIRES_REDESIGN"
    REQUIRES_EXTERNAL_APPROVAL = "REQUIRES_EXTERNAL_APPROVAL"
    BLOCKS_CURRENT_EXECUTION = "BLOCKS_CURRENT_EXECUTION"


class EpistemicCategory(StrEnum):
    """Epistemic categories of statements (Core §14, FR-FRAME-004)."""

    OBSERVATION = "OBSERVATION"
    FACTUAL_CLAIM = "FACTUAL_CLAIM"
    INTERPRETATION = "INTERPRETATION"
    ASSUMPTION = "ASSUMPTION"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN = "UNKNOWN"


class StatementOrigin(StrEnum):
    """Who asserted a statement (Core §14)."""

    RESEARCHER_STATED = "RESEARCHER_STATED"
    SYSTEM_INFERRED = "SYSTEM_INFERRED"
    SOURCE_STATED = "SOURCE_STATED"
    EXPERIMENT_OBSERVED = "EXPERIMENT_OBSERVED"


class ClaimType(StrEnum):
    """Claim types (Core §18, FR-CLAIM-001)."""

    OBSERVATION = "OBSERVATION"
    FACTUAL_CLAIM = "FACTUAL_CLAIM"
    CAUSAL_CLAIM = "CAUSAL_CLAIM"
    INTERPRETATION = "INTERPRETATION"
    NORMATIVE_CLAIM = "NORMATIVE_CLAIM"
    MECHANISM_CLAIM = "MECHANISM_CLAIM"
    DESIGN_CLAIM = "DESIGN_CLAIM"


class AssumptionOrigin(StrEnum):
    """Assumption origin (Core §19, FR-CLAIM-003). SYSTEM_INFERRED stays labeled until confirmed/reclassified."""

    EXPLICIT = "EXPLICIT"
    SYSTEM_INFERRED = "SYSTEM_INFERRED"
    SOURCE_DERIVED = "SOURCE_DERIVED"


class Criticality(StrEnum):
    """Assumption criticality (Core §19, FR-CLAIM-004)."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    FOUNDATIONAL = "FOUNDATIONAL"


class ProblemFrameStatus(StrEnum):
    """Problem Frame version status (Core §12-13, FR-FRAME-006/007)."""

    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    SUPERSEDED = "SUPERSEDED"


class HypothesisLifecycleState(StrEnum):
    """Hypothesis workflow lifecycle (Core §20, FR-HYP-001)."""

    SIGNAL = "SIGNAL"
    IDEA = "IDEA"
    FORMULATED_HYPOTHESIS = "FORMULATED_HYPOTHESIS"
    UNDER_REFERENCE_REVIEW = "UNDER_REFERENCE_REVIEW"
    UNDER_SCRUTINY = "UNDER_SCRUTINY"
    UNDER_RESEARCH = "UNDER_RESEARCH"
    ASSESSED = "ASSESSED"
    ELIGIBLE_FOR_DESIGN = "ELIGIBLE_FOR_DESIGN"
    USED_IN_DESIGN = "USED_IN_DESIGN"
    TESTED_IN_PRACTICE = "TESTED_IN_PRACTICE"


class HypothesisEpistemicState(StrEnum):
    """Hypothesis epistemic assessment (Core §20, FR-HYP-002)."""

    PROMISING = "PROMISING"
    SUPPORTED = "SUPPORTED"
    WEAKENED = "WEAKENED"
    CONTESTED = "CONTESTED"
    REFUTED = "REFUTED"
    UNRESOLVED = "UNRESOLVED"


class MechanismStatus(StrEnum):
    """Mechanism states (Core §22, FR-MECH-002)."""

    PROPOSED = "PROPOSED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    PLAUSIBLE = "PLAUSIBLE"
    SUPPORTED = "SUPPORTED"
    DISPUTED = "DISPUTED"
    WEAKENED = "WEAKENED"
    REJECTED = "REJECTED"
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"


class SourceAccessMode(StrEnum):
    """Source access modes (Core §24, FR-SRC-004). Metadata presence never implies asset availability."""

    DIRECT_DIGITAL = "DIRECT_DIGITAL"
    PHYSICAL = "PHYSICAL"
    RESEARCHER_MEDIATED = "RESEARCHER_MEDIATED"
    RESTRICTED = "RESTRICTED"
    METADATA_ONLY = "METADATA_ONLY"


class SourceVerificationState(StrEnum):
    """Source verification states (Core §25, FR-SRC-005). Import never raises this; only an explicit ReverificationEvent may."""

    MACHINE_VERIFIED = "MACHINE_VERIFIED"
    RESEARCHER_SUPPLIED_EXACT = "RESEARCHER_SUPPLIED_EXACT"
    RESEARCHER_REPORTED_SOURCE_CONTENT = "RESEARCHER_REPORTED_SOURCE_CONTENT"
    METADATA_ONLY = "METADATA_ONLY"
    UNVERIFIED = "UNVERIFIED"


class SourceAssetKind(StrEnum):
    """Concrete asset kinds (PRD §15)."""

    PDF = "PDF"
    EPUB = "EPUB"
    HTML_CAPTURE = "HTML_CAPTURE"
    IMAGE = "IMAGE"
    SCAN = "SCAN"
    AUDIO = "AUDIO"
    LOCAL_TEXT = "LOCAL_TEXT"
    REMOTE_URL = "REMOTE_URL"
    OTHER = "OTHER"


class TextOrigin(StrEnum):
    """Origin of source text (Core §28, FR-INGEST-002). OCR is never automatically exact."""

    NATIVE_DIGITAL = "NATIVE_DIGITAL"
    OCR_EXTRACTED = "OCR_EXTRACTED"
    HUMAN_TRANSCRIBED = "HUMAN_TRANSCRIBED"


class SourceLeadOrigin(StrEnum):
    """Where a source lead came from. Web results are leads, never evidence (FR-WEB-003)."""

    RESEARCHER_MEMORY = "RESEARCHER_MEMORY"
    WEB_SEARCH = "WEB_SEARCH"


class SourceLeadState(StrEnum):
    """Researcher memory of a source is a lead until verified (Core §27)."""

    SOURCE_LEAD = "SOURCE_LEAD"
    VERIFIED = "VERIFIED"
    DISCARDED = "DISCARDED"


class EvidenceRole(StrEnum):
    """Evidence roles (Core §33, FR-EVID-002)."""

    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    LIMITS = "LIMITS"
    QUALIFIES = "QUALIFIES"
    CONTEXTUALIZES = "CONTEXTUALIZES"


class EvidenceStrength(StrEnum):
    """Qualitative evidence strength; no 0-100 truth score (Core §34, FR-EVID-004/005)."""

    UNSUBSTANTIATED = "UNSUBSTANTIATED"
    WEAK = "WEAK"
    PROMISING = "PROMISING"
    SUPPORTED = "SUPPORTED"
    STRONG = "STRONG"
    ESTABLISHED_WITHIN_SCOPE = "ESTABLISHED_WITHIN_SCOPE"


class LineageRelation(StrEnum):
    """Evidence lineage/dependency relations (Core §35, FR-LINEAGE-001)."""

    CITES = "CITES"
    REPLICATES = "REPLICATES"
    USES_DATA_FROM = "USES_DATA_FROM"
    DERIVED_FROM = "DERIVED_FROM"
    SUMMARIZES = "SUMMARIZES"
    REANALYZES = "REANALYZES"
    TRANSLATES = "TRANSLATES"


class ProvenanceKind(StrEnum):
    """Who/what produced a piece of content (Core §7, §36, §71). AI_GENERATED content is never independent evidence."""

    HUMAN_INPUT = "HUMAN_INPUT"
    SOURCE_DERIVED = "SOURCE_DERIVED"
    AI_GENERATED = "AI_GENERATED"
    EXPERIMENT_DERIVED = "EXPERIMENT_DERIVED"
    SYSTEM_COMPUTED = "SYSTEM_COMPUTED"
    IMPORTED = "IMPORTED"


class ResearchQuestionType(StrEnum):
    """Question routing types (Core §37, FR-RSCH-003)."""

    REFERENCE = "REFERENCE"
    EMPIRICAL = "EMPIRICAL"
    HISTORICAL = "HISTORICAL"
    MECHANISM = "MECHANISM"
    IMPLEMENTATION = "IMPLEMENTATION"
    TECHNICAL = "TECHNICAL"
    CONTEXTUAL = "CONTEXTUAL"


class ResearchTrack(StrEnum):
    """Counter-evidence architecture tracks (Core §41, FR-BIAS-001)."""

    SUPPORT = "SUPPORT"
    CHALLENGE = "CHALLENGE"
    ALTERNATIVE_EXPLANATION = "ALTERNATIVE_EXPLANATION"


class ResearchLayer(StrEnum):
    """Retrieval layers (Core §38)."""

    APPROVED_REFERENCE_LIBRARY = "APPROVED_REFERENCE_LIBRARY"
    PROJECT_LIBRARY = "PROJECT_LIBRARY"
    RESEARCH_MEMORY = "RESEARCH_MEMORY"
    EXTERNAL_KNOWLEDGE = "EXTERNAL_KNOWLEDGE"


class ResearchOutcomeKind(StrEnum):
    """Search/tool outcome; failure is never evidence absence (Core §72, FR-WEB-004)."""

    RESULTS_FOUND = "RESULTS_FOUND"
    NO_RELEVANT_EVIDENCE_FOUND = "NO_RELEVANT_EVIDENCE_FOUND"
    RESEARCH_EXECUTION_FAILURE = "RESEARCH_EXECUTION_FAILURE"
    INSUFFICIENT_SEARCH_COVERAGE = "INSUFFICIENT_SEARCH_COVERAGE"
    SOURCE_INACCESSIBLE = "SOURCE_INACCESSIBLE"
    STOPPED_RESOURCE_CONSTRAINT = "STOPPED_RESOURCE_CONSTRAINT"


class SufficiencyResult(StrEnum):
    """Research sufficiency conclusions (Core §46, FR-SUFF-003)."""

    SUFFICIENTLY_ANSWERED = "SUFFICIENTLY_ANSWERED"
    PARTIALLY_ANSWERED = "PARTIALLY_ANSWERED"
    CONTESTED = "CONTESTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    RESEARCH_ROUTE_EXHAUSTED = "RESEARCH_ROUTE_EXHAUSTED"


class TransferabilityState(StrEnum):
    """Cross-context transferability (Core §44, FR-TRANS-002)."""

    DIRECTLY_RELEVANT = "DIRECTLY_RELEVANT"
    PARTIALLY_TRANSFERABLE = "PARTIALLY_TRANSFERABLE"
    ANALOGICAL_ONLY = "ANALOGICAL_ONLY"
    NOT_TRANSFERABLE = "NOT_TRANSFERABLE"


class TemporalProfile(StrEnum):
    """Temporal validity profiles (Core §45, FR-TIME-001)."""

    STABLE = "STABLE"
    SLOW_CHANGING = "SLOW_CHANGING"
    DYNAMIC = "DYNAMIC"
    HIGHLY_VOLATILE = "HIGHLY_VOLATILE"


class DesignOrigin(StrEnum):
    """Design/idea origin (Core §48, FR-DESIGN-004)."""

    RESEARCHER = "RESEARCHER"
    AI = "AI"
    SOURCE = "SOURCE"
    JOINT_SYNTHESIS = "JOINT_SYNTHESIS"
    PRIOR_PROJECT = "PRIOR_PROJECT"


class ExperimentState(StrEnum):
    """Experiment workflow (Core §50, FR-EXP-002)."""

    PROPOSED = "PROPOSED"
    PROTOCOL_DEFINED = "PROTOCOL_DEFINED"
    RISK_REVIEW = "RISK_REVIEW"
    APPROVED = "APPROVED"
    RUNNING = "RUNNING"
    DATA_COLLECTION_COMPLETE = "DATA_COLLECTION_COMPLETE"
    ANALYSIS = "ANALYSIS"
    INTERPRETED = "INTERPRETED"
    CLOSED = "CLOSED"
    PAUSED = "PAUSED"
    ABORTED = "ABORTED"
    INVALIDATED = "INVALIDATED"


class KnowledgeLifecycleStage(StrEnum):
    """Local knowledge lifecycle; promotion is never automatic (Core §52, FR-KNOW-001)."""

    PROJECT_FINDING = "PROJECT_FINDING"
    LOCAL_RESULT = "LOCAL_RESULT"
    REPEATED_LOCAL_RESULT = "REPEATED_LOCAL_RESULT"
    ACCUMULATED_LOCAL_KNOWLEDGE = "ACCUMULATED_LOCAL_KNOWLEDGE"
    CANDIDATE_OPERATING_RULE = "CANDIDATE_OPERATING_RULE"
    OPERATING_RULE = "OPERATING_RULE"


class KnowledgeStatus(StrEnum):
    """Knowledge standing independent of lifecycle stage (Core §52, FR-KNOW-004, FR-TIME-003)."""

    ACTIVE = "ACTIVE"
    DOWNGRADED = "DOWNGRADED"
    CONTESTED = "CONTESTED"
    SUSPENDED = "SUSPENDED"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"


class ActionAuthorizationClass(StrEnum):
    """AI action authority classes; policy lives in the system, not prompts (Core §57, FR-ACTION-001)."""

    AUTONOMOUS = "AUTONOMOUS"
    ACT_AND_NOTIFY = "ACT_AND_NOTIFY"
    REQUEST_APPROVAL = "REQUEST_APPROVAL"
    FORBIDDEN = "FORBIDDEN"


class MethodologyPathStatus(StrEnum):
    """Whether a path is within the methodology (Core §59, §62, FR-OVERRIDE-002, FR-DEGRADED-002)."""

    COMPLIANT = "COMPLIANT"
    OVERRIDDEN_WITH_REASON = "OVERRIDDEN_WITH_REASON"
    DECISION_UNDER_INCOMPLETE_EVIDENCE = "DECISION_UNDER_INCOMPLETE_EVIDENCE"
    OUTSIDE_METHODOLOGY_PATH = "OUTSIDE_METHODOLOGY_PATH"


class QualityGateType(StrEnum):
    """Quality gates (Core §60, PRD §41)."""

    FRAMING = "FRAMING"
    HYPOTHESIS = "HYPOTHESIS"
    REFERENCE = "REFERENCE"
    EVIDENCE_SUFFICIENCY = "EVIDENCE_SUFFICIENCY"
    DESIGN_READINESS = "DESIGN_READINESS"
    EXPERIMENT_READINESS = "EXPERIMENT_READINESS"
    LEARNING_INTEGRITY = "LEARNING_INTEGRITY"
    KNOWLEDGE_PROMOTION = "KNOWLEDGE_PROMOTION"
    PROJECT_CLOSURE = "PROJECT_CLOSURE"


class QualityGateResult(StrEnum):
    """Quality gate results (Core §60, PRD §41)."""

    PASS = "PASS"
    PASS_WITH_RESERVATIONS = "PASS_WITH_RESERVATIONS"
    NEEDS_HUMAN_DECISION = "NEEDS_HUMAN_DECISION"
    BLOCKED = "BLOCKED"


class ClosureType(StrEnum):
    """Project closure types (Core §66, FR-CLOSE-001)."""

    KNOWLEDGE_CONCLUSION = "KNOWLEDGE_CONCLUSION"
    HYPOTHESIS_CONCLUSION = "HYPOTHESIS_CONCLUSION"
    DECISION = "DECISION"
    DESIGN = "DESIGN"
    EXPERIMENT_CONCLUSION = "EXPERIMENT_CONCLUSION"
    PRODUCTION_DELIVERABLE = "PRODUCTION_DELIVERABLE"
    JUSTIFIED_STOP = "JUSTIFIED_STOP"


class ActorKind(StrEnum):
    """Kind of actor behind an event/approval (PRD §62, §67)."""

    HUMAN = "HUMAN"
    AI = "AI"
    SYSTEM = "SYSTEM"


class ActorRole(StrEnum):
    """Role-aware domain; v1 may be single-user but must not assume one actor (PRD §62)."""

    RESEARCHER = "RESEARCHER"
    PROJECT_LEAD = "PROJECT_LEAD"
    METHODOLOGY_STEWARD = "METHODOLOGY_STEWARD"
    CONSTITUTIONAL_AUTHORITY = "CONSTITUTIONAL_AUTHORITY"
    SYSTEM = "SYSTEM"


class NotificationLevel(StrEnum):
    """Human attention levels (PRD §65)."""

    INFO = "INFO"
    ATTENTION = "ATTENTION"
    DECISION_REQUIRED = "DECISION_REQUIRED"
    BLOCKING = "BLOCKING"


class OutputMode(StrEnum):
    """Output modes (FR-OUT-001)."""

    READABLE = "READABLE"
    REFERENCED = "REFERENCED"
    AUDIT = "AUDIT"


class LanguageCode(StrEnum):
    """First-class research/output languages (PRD §3.1, Core §40)."""

    AR = "ar"
    EN = "en"
    FR = "fr"


class SourceAccessRequestStatus(StrEnum):
    """Hybrid Source Access request lifecycle (Core §26, FR-HYBRID-001)."""

    OPEN = "OPEN"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class AccessResponseForm(StrEnum):
    """Accepted forms of a researcher response to a source access request (FR-HYBRID-003)."""

    EXACT_TEXT = "EXACT_TEXT"
    PAGE_IMAGES = "PAGE_IMAGES"
    RESEARCHER_SUMMARY = "RESEARCHER_SUMMARY"
    RESEARCHER_ATTESTATION = "RESEARCHER_ATTESTATION"
    DIGITAL_ASSET = "DIGITAL_ASSET"


class Priority(StrEnum):
    """Priority of requests and work items."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class DecisionStatus(StrEnum):
    """Decision record lifecycle; AI recommendation stays distinct from the human decision (FR-DEC-001/002)."""

    OPEN = "OPEN"
    DECIDED = "DECIDED"
    WITHDRAWN = "WITHDRAWN"


class ApprovalOutcome(StrEnum):
    """Outcome of an explicit human approval action (FR-APPROVAL-001)."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class IngestionStatus(StrEnum):
    """Source asset ingestion state (PRD §17)."""

    NOT_STARTED = "NOT_STARTED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ClaimWorkflowState(StrEnum):
    """Claim workflow state; independent of epistemic strength (Core §16, §18, FR-CLAIM-002)."""

    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    RETIRED = "RETIRED"


class AssumptionStatus(StrEnum):
    """Assumption review status; SYSTEM_INFERRED assumptions stay UNCONFIRMED until a human acts (Core §19, FR-CLAIM-003)."""

    UNCONFIRMED = "UNCONFIRMED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    RECLASSIFIED = "RECLASSIFIED"


class OpenQuestionStatus(StrEnum):
    """Open question lifecycle (Core §15, §37)."""

    OPEN = "OPEN"
    ANSWERED = "ANSWERED"
    CLOSED_UNANSWERED = "CLOSED_UNANSWERED"


class EvidenceStatus(StrEnum):
    """Evidence pipeline: candidate -> assessment -> accepted evidence (Core §32)."""

    CANDIDATE = "CANDIDATE"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class EvidenceTargetType(StrEnum):
    """What evidence can bear on (FR-EVID-001)."""

    CLAIM = "CLAIM"
    HYPOTHESIS = "HYPOTHESIS"
    MECHANISM = "MECHANISM"
    DESIGN_CONCEPT = "DESIGN_CONCEPT"
    DESIGN_HYPOTHESIS = "DESIGN_HYPOTHESIS"


class DesignRequirementBasis(StrEnum):
    """What a design requirement is derived from (FR-DESIGN-002, Core §47)."""

    PURPOSE = "PURPOSE"
    REFERENCE_CONSTRAINT = "REFERENCE_CONSTRAINT"
    HUMAN_CONTEXT_NEED = "HUMAN_CONTEXT_NEED"
    MECHANISM = "MECHANISM"
    EVIDENCE = "EVIDENCE"
    RISK = "RISK"
    OPERATIONAL_CONSTRAINT = "OPERATIONAL_CONSTRAINT"


class RequirementPriority(StrEnum):
    """Design requirement priority."""

    MUST = "MUST"
    SHOULD = "SHOULD"
    COULD = "COULD"


class DesignRequirementStatus(StrEnum):
    """Requirement versions are never edited; a revision supersedes (Core §47). AI-proposed requirements stay PROPOSED until a human confirms them."""

    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"


class DesignConceptStatus(StrEnum):
    """Design concept status; selection is a human decision (FR-DESIGN-006). Rejected designs stay in history (FR-DESIGN-005)."""

    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SELECTED = "SELECTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class RequirementCoverage(StrEnum):
    """How a design concept addresses a requirement."""

    MEETS = "MEETS"
    PARTIAL = "PARTIAL"
    NOT_ADDRESSED = "NOT_ADDRESSED"
    CONFLICTS = "CONFLICTS"


class RejectionGround(StrEnum):
    """Why a design was rejected; REFERENCE rejections keep reusable mechanisms visible (FR-DESIGN-005)."""

    REFERENCE = "REFERENCE"
    EVIDENCE = "EVIDENCE"
    OPERATIONAL = "OPERATIONAL"
    FEASIBILITY = "FEASIBILITY"
    OTHER = "OTHER"


class HumanImpactDimension(StrEnum):
    """What a human-impact review inspects when people are affected (Core §51, FR-HUMAN-001). Distinct from the reference judgment (FR-HUMAN-002)."""

    PRIVACY = "PRIVACY"
    CONSENT = "CONSENT"
    HARM = "HARM"
    AUTHORITY = "AUTHORITY"
    LAW_AND_POLICY = "LAW_AND_POLICY"
    DATA_HANDLING = "DATA_HANDLING"
    INSTITUTIONAL_APPROVAL = "INSTITUTIONAL_APPROVAL"
    REVERSIBILITY = "REVERSIBILITY"


class HumanImpactFinding(StrEnum):
    """Outcome of one human-impact dimension; REQUIRES_EXTERNAL_APPROVAL becomes an unresolved operational requirement (FR-HUMAN-003)."""

    NOT_APPLICABLE = "NOT_APPLICABLE"
    ADDRESSED = "ADDRESSED"
    CONCERN = "CONCERN"
    REQUIRES_EXTERNAL_APPROVAL = "REQUIRES_EXTERNAL_APPROVAL"


class InterpretationOutcome(StrEnum):
    """What a human interpretation concludes about the design hypothesis from analysed results (FR-EXP-003)."""

    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    INCONCLUSIVE = "INCONCLUSIVE"
    QUALIFIES = "QUALIFIES"


class TermStatus(StrEnum):
    """Terminology record state; only a human approves the canonical form (FR-TERM-001, Core §53)."""

    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    SUPERSEDED = "SUPERSEDED"
    REJECTED = "REJECTED"


class OutputType(StrEnum):
    """Output types (PRD §37)."""

    RESEARCH_REPORT = "RESEARCH_REPORT"
    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"
    DECISION_BRIEF = "DECISION_BRIEF"
    REFERENCE_REVIEW = "REFERENCE_REVIEW"
    EVIDENCE_MAP = "EVIDENCE_MAP"
    HYPOTHESIS_DOSSIER = "HYPOTHESIS_DOSSIER"
    DESIGN_SPECIFICATION = "DESIGN_SPECIFICATION"
    EXPERIMENT_PROTOCOL = "EXPERIMENT_PROTOCOL"
    LEARNING_REVIEW = "LEARNING_REVIEW"
    CLOSURE_REPORT = "CLOSURE_REPORT"


class OutputBlockKind(StrEnum):
    """Block kinds in an output version; CLAIM blocks must trace to canonical entities and QUOTE blocks are protected exact text (FR-OUT-003/004)."""

    HEADING = "HEADING"
    PARAGRAPH = "PARAGRAPH"
    CLAIM = "CLAIM"
    EVIDENCE = "EVIDENCE"
    QUOTE = "QUOTE"
    LIST = "LIST"
    NOTE = "NOTE"


class OutputVersionStatus(StrEnum):
    """Output versions are never overwritten; approval is human (PRD §37)."""

    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    SUPERSEDED = "SUPERSEDED"


class QuoteSourceKind(StrEnum):
    """Where a protected exact quote comes from."""

    EXCERPT = "EXCERPT"
    QURAN = "QURAN"
    HADITH = "HADITH"


class IntegrityStep(StrEnum):
    """The output integrity pipeline, in order (FR-OUT-002)."""

    CLAIM_VERIFICATION = "CLAIM_VERIFICATION"
    CITATION_VERIFICATION = "CITATION_VERIFICATION"
    EXACT_QUOTE_VERIFICATION = "EXACT_QUOTE_VERIFICATION"
    REFERENCE_INTEGRITY = "REFERENCE_INTEGRITY"
    TERMINOLOGY_CHECK = "TERMINOLOGY_CHECK"
    TRANSLATION_SEMANTIC_CHECK = "TRANSLATION_SEMANTIC_CHECK"
    LANGUAGE_EDITING = "LANGUAGE_EDITING"
    FINAL_RENDERING = "FINAL_RENDERING"


class IntegrityStepStatus(StrEnum):
    """Result of one integrity step."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


class IntegrityStatus(StrEnum):
    """Overall integrity of an output version; FAILED cannot be approved (FR-OUT-002)."""

    VERIFIED = "VERIFIED"
    VERIFIED_WITH_WARNINGS = "VERIFIED_WITH_WARNINGS"
    FAILED = "FAILED"


class FoundationalSourceStatus(StrEnum):
    """Foundational source approval state; only APPROVED sources are served (FR-REFSRC-001..003)."""

    STAGED = "STAGED"
    APPROVED = "APPROVED"
    RETIRED = "RETIRED"


class ConstraintKind(StrEnum):
    """Kind of human-made operational constraint (Core §5, PRD §5.3)."""

    LAW = "LAW"
    REGULATION = "REGULATION"
    CONTRACT = "CONTRACT"
    LICENSE = "LICENSE"
    INSTITUTIONAL_POLICY = "INSTITUTIONAL_POLICY"
    AUTHORIZATION = "AUTHORIZATION"
    OTHER = "OTHER"
