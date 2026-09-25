/** Shapes of API responses used by the UI (subset of the backend schemas). */
import type {
  AccessResponseForm,
  DesignConceptStatus,
  DesignOrigin,
  DesignRequirementBasis,
  DesignRequirementStatus,
  ExperimentState,
  KnowledgeLifecycleStage,
  KnowledgeStatus,
  IngestionStatus,
  NotificationLevel,
  ProblemFrameStatus,
  ProjectInputType,
  ProjectStatus,
  QualityGateResult,
  ReferenceAuthorityLayer,
  RejectionGround,
  RequirementCoverage,
  RequirementPriority,
  ResearchMode,
  RiskLevel,
  SensitivityLevel,
  SourceAccessMode,
  SourceAccessRequestStatus,
  SourceVerificationState,
} from "@/lib/contracts/enums";

export type Actor = { kind: "HUMAN" | "AI" | "SYSTEM"; id: string; role?: string | null };

export type Project = {
  id: string;
  title: string;
  initial_input: string;
  input_type: ProjectInputType;
  sensitivity: SensitivityLevel;
  risk_level: RiskLevel;
  status: ProjectStatus;
  research_mode: ResearchMode;
  updated_at: string;
};

export type ResearchState = {
  current_question: string | null;
  current_mode: ResearchMode;
  established_findings: string[];
  unresolved_items: string[];
  reservations: string[];
  blockers: string[];
  pending_decision_ids: string[];
  next_action: string | null;
  next_action_reason: string | null;
};

export const FRAME_TEXT_FIELDS = ["central_issue", "current_state", "desired_state", "gap", "context", "readiness"] as const;
export const FRAME_LIST_FIELDS = [
  "current_explanations",
  "initial_hypotheses",
  "constraints",
  "known",
  "unknowns",
  "research_questions",
  "reference_review_points",
] as const;
export type FrameTextField = (typeof FRAME_TEXT_FIELDS)[number];
export type FrameListField = (typeof FRAME_LIST_FIELDS)[number];
export type FrameContent = Record<FrameTextField, string> & Record<FrameListField, string[]>;

export type ProblemFrame = {
  id: string;
  version_number: number;
  status: ProblemFrameStatus;
  content: FrameContent;
  provenance: { kind: string };
  approved_at: string | null;
};

export type GateFinding = { code: string; severity: QualityGateResult; message: string };

export type Note = { id: string; body: string; captured_as: string | null; created_at: string };

export type Decision = {
  id: string;
  question: string;
  options: string[];
  status: "OPEN" | "DECIDED" | "WITHDRAWN";
  blocking: boolean;
  final_decision: string | null;
  human_justification: string | null;
  methodology_path: string | null;
  ai_recommendation: { option: string; rationale: string } | null;
};

export type AttentionItem = {
  kind: string;
  level: NotificationLevel;
  title: string;
  entity_type: string;
  entity_id: string;
};

export type Asset = {
  id: string;
  kind: string;
  access_mode: SourceAccessMode;
  available_in_environment: boolean;
  media_type: string | null;
  original_filename: string | null;
  holding_note: string | null;
  ingestion_status: IngestionStatus;
};

export type Edition = {
  id: string;
  edition_label: string | null;
  language: string | null;
  verification_state: SourceVerificationState;
  available: boolean;
  assets: Asset[];
};

export type Work = {
  id: string;
  title: string;
  authors: string[];
  authority_layer: ReferenceAuthorityLayer;
  editions: Edition[];
};

export type AccessRequest = {
  id: string;
  edition_id: string;
  reason: string;
  requested_scope: string;
  acceptable_forms: AccessResponseForm[];
  priority: string;
  status: SourceAccessRequestStatus;
};

export type Excerpt = {
  id: string;
  location: string;
  text: string;
  verification_state: SourceVerificationState;
  is_exact_quote: boolean;
  access_request_id: string | null;
};

export type SearchHit = {
  chunk_id: string;
  work_title: string;
  page_number: number;
  snippet: string;
};

export type SearchResponse = {
  query: string;
  mode: "lexical" | "semantic" | "hybrid";
  outcome: "RESULTS_FOUND" | "NO_RELEVANT_EVIDENCE_FOUND";
  scope: string;
  searched_assets: number;
  hits: SearchHit[];
};

export type Claim = {
  id: string;
  statement: string;
  claim_type: string;
  statement_origin: string;
  workflow_state: string;
  epistemic_strength: string;
  important: boolean;
};

export type Assumption = {
  id: string;
  statement: string;
  origin: string;
  criticality: string;
  status: string;
};

export type OpenQuestion = { id: string; question: string; question_type: string; status: string; conclusion: string | null };

export type HypothesisContent = {
  statement: string;
  context: string;
  expected_outcome: string;
  proposed_mechanism: string;
  assumptions: string[];
  boundary_conditions: string[];
  falsification_conditions: string[];
};

export type Hypothesis = {
  id: string;
  current_version: number;
  lifecycle_state: string;
  epistemic_state: string;
  suggested_epistemic_state: string;
  counter_evidence_search_complete: boolean;
  content: HypothesisContent;
  mechanism_ids: string[];
  competing_hypothesis_ids: string[];
};

export type HypothesisVersion = {
  version_number: number;
  lifecycle_state: string;
  epistemic_state: string;
  change_reason: string;
  actor: Actor;
  created_at: string;
};

export type Mechanism = { id: string; name: string; description: string; status: string };

export type EvidenceItem = {
  id: string;
  role: string;
  status: string;
  finding: string;
  excerpt_id: string;
  track: string | null;
  assessment: { strength?: string; limitations?: string } | null;
  provenance: { kind: string };
};

export type TrackStatus = { track: string; searched: boolean; last_outcome: string | null; execution_failed: boolean };

export type EvidenceMap = {
  by_role: Record<string, EvidenceItem[]>;
  candidates: EvidenceItem[];
  support_origins: number;
  contra_origins: number;
  meaningful_conflict: boolean;
  suggested_strength: string;
  tracks: TrackStatus[];
  counter_evidence_search_complete: boolean;
};

export type ReferenceEntry = { id: string; layer: string; content: string; quran_ref: string | null; provenance: { kind: string } };
export type ReferenceJudgment = {
  id: string;
  state: string;
  directness: string;
  reservation_type: string | null;
  rationale: string;
  decision_id: string | null;
};
export type ReferenceReview = {
  id: string;
  target_type: string;
  target_id: string;
  question: string;
  analytical_category: string;
  entries: ReferenceEntry[];
  judgments: ReferenceJudgment[];
  current_judgment: ReferenceJudgment | null;
};

export type Standing = {
  reference: { result: string; findings: { code: string; message: string }[] };
  operational: { execution_ready: boolean; researchable: boolean; blocking: { description: string }[] };
  summary: string;
};

export type Job = {
  id: string;
  kind: string;
  state: "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED" | "CANCELLED";
  project_id: string | null;
  params: Record<string, unknown>;
  result: Record<string, unknown> | null;
  failure_kind: string | null;
  error: string | null;
  created_at: string;
  finished_at: string | null;
};

export type AIProfile = { name: string; provider: string; model: string; local: boolean; configured: boolean; default: boolean };

export type TrackPlan = { track: string; approach: string; queries: string[] };
export type ResearchPlan = {
  id: string;
  series_id: string;
  version_number: number;
  status: "ACTIVE" | "SUPERSEDED";
  question: string;
  decision_served: string;
  question_type: string;
  risk_impact: string;
  desired_evidence_types: string[];
  languages: string[];
  tracks: TrackPlan[];
  sufficiency_criteria: string[];
  max_web_searches: number | null;
  change_reason: string | null;
  created_at: string;
};
export type SearchRecord = {
  id: string;
  plan_id: string | null;
  track: string | null;
  question: string;
  provider: string;
  queries: string[];
  languages: string[];
  outcome: string;
  result_count: number;
  scope: string;
  actor: { kind: string; id: string };
  performed_at: string;
};
export type Sufficiency = {
  id: string;
  result: string;
  considerations: Record<string, string>;
  rationale: string;
  recommend_experiment: boolean;
  assessed_by: { kind: string; id: string };
  assessed_at: string;
};
export type PlanOverview = {
  plan: ResearchPlan;
  versions: ResearchPlan[];
  coverage: { track: string; searches: number; searched: boolean; last_outcome: string | null; execution_failed: boolean }[];
  web_searches_used: number;
  searches: SearchRecord[];
  current_sufficiency: Sufficiency | null;
  sufficiency_history: Sufficiency[];
};
export type SourceLead = {
  id: string;
  statement: string;
  status: string;
  origin: string;
  url: string | null;
  title: string | null;
  search_record_id: string | null;
};

export type FoundationalSource = {
  id: string;
  work_id: string;
  authority_layer: string;
  edition_version: string;
  status: "STAGED" | "APPROVED" | "RETIRED";
  sha256: string;
  dataset_summary: { surahs?: number; ayat?: number; format?: string };
  approved_by: { kind: string; id: string } | null;
  approved_at: string | null;
};

export type Ayah = {
  surah_number: number;
  surah_name: string;
  ayah_number: number;
  text: string;
  source_id: string;
  source_version: string;
  source_sha256: string;
};

export type Evaluation = {
  id: string;
  provider: string;
  model: string;
  dimension: string;
  score: number;
  threshold: number;
  comparator: string;
  passed: boolean;
  sample_size: number;
  method: string;
  fixture_set: string | null;
  created_at: string;
};
export type Reliability = {
  dimensions: { key: string; label: string; comparator: string; threshold: number; blocking: boolean }[];
  operational: {
    provider: string;
    model: string;
    task: string;
    calls: number;
    succeeded: number;
    invalid_output: number;
    refusals: number;
    unavailable: number;
    blocked: number;
    structured_output_reliability: number | null;
    estimated_cost_usd: string;
  }[];
  models: {
    provider: string;
    model: string;
    latest: Record<string, Evaluation>;
    blocking_failures: string[];
    blocking_unevaluated: string[];
  }[];
};

export type RequirementTrace = { basis: DesignRequirementBasis; entity_type?: string | null; entity_id?: string | null; note?: string | null };

export type DesignRequirement = {
  id: string;
  series_id: string;
  version_number: number;
  supersedes_id: string | null;
  statement: string;
  priority: RequirementPriority;
  traces: RequirementTrace[];
  status: DesignRequirementStatus;
  change_reason: string | null;
  provenance: { kind: string };
};

export type ConceptCoverage = {
  requirement_id: string;
  requirement_series_id: string;
  coverage: RequirementCoverage;
  note: string | null;
  stale: boolean;
};

export type DesignConcept = {
  id: string;
  title: string;
  description: string;
  origin: DesignOrigin;
  origin_reference: string | null;
  status: DesignConceptStatus;
  hypothesis_ids: string[];
  mechanism_ids: string[];
  derived_from_concept_ids: string[];
  coverage: ConceptCoverage[];
  rejection: { ground: RejectionGround; reason: string; reusable_mechanism_ids: string[] } | null;
  selection: { gate_result: QualityGateResult; methodology_path: string } | null;
  provenance: { kind: string };
};

export type GateEvaluation = {
  id: string;
  gate: string;
  result: QualityGateResult;
  risk_level: RiskLevel;
  findings: GateFinding[];
  evaluated_at: string;
};

export type DesignHypothesisContent = {
  intervention: string;
  target_population: string;
  context: string;
  mechanism: string;
  expected_outcome: string;
  measurement_plan: string;
  failure_conditions: string[];
  side_effects: string[];
  stop_conditions: string[];
};

export type DesignHypothesis = {
  id: string;
  concept_id: string;
  current_version: number;
  content: DesignHypothesisContent;
  affects_people: boolean;
  epistemic_state: string;
  provenance: { kind: string };
};

export type ExperimentProtocol = Record<"method" | "sample" | "duration" | "data_collected" | "analysis_plan" | "success_criteria", string>;

export type Experiment = {
  id: string;
  design_hypothesis_id: string;
  title: string;
  protocol: ExperimentProtocol;
  state: ExperimentState;
  paused_from: ExperimentState | null;
  affects_people: boolean;
  invalidation_reason: string | null;
  provenance: { kind: string };
  transitions: { from_state: string; to_state: string; reason: string | null; created_at: string; actor: Actor }[];
};

export type ExperimentRecord = {
  human_impact: {
    id: string;
    dimension: string;
    finding: string;
    note: string;
    external_authority: string | null;
    operational_constraint_id: string | null;
    assessed_at: string;
  }[];
  observations: { id: string; description: string; measurements: Record<string, unknown> | null; observed_at: string }[];
  results: { id: string; observation_ids: string[]; method: string; summary: string }[];
  interpretations: { id: string; result_ids: string[]; outcome: string; statement: string; limitations: string | null }[];
  learning_reviews: {
    id: string;
    learned: string;
    hypothesis_effect: string;
    surprises: string | null;
    limitations: string[];
    validity_threats: string[];
    next_steps: string[];
    created_at: string;
  }[];
};

export type KnowledgeBasis = { entity_type: string; entity_id: string; context?: string | null; note?: string | null };

export type KnowledgeItem = {
  id: string;
  project_id: string;
  current_version: number;
  statement: string;
  stage: KnowledgeLifecycleStage;
  status: KnowledgeStatus;
  effective_status: KnowledgeStatus;
  revalidation_due: boolean;
  scope: string;
  contexts: string[];
  evidence_basis: KnowledgeBasis[];
  contrary_evidence: KnowledgeBasis[];
  contrary_evidence_searched: boolean;
  confidence: string;
  temporal_profile: string;
  last_verified_at: string | null;
  revalidation_interval_days: number | null;
  provenance: { kind: string };
};

export type KnowledgeReuse = {
  id: string;
  knowledge_item_id: string;
  statement: string;
  source_project_id: string;
  stage: KnowledgeLifecycleStage;
  effective_status: KnowledgeStatus;
  transferability: string;
  rationale: string;
  differences: string | null;
  label: string;
  direct_evidence: false;
};

export type Term = {
  id: string;
  series_id: string;
  version_number: number;
  term: string;
  original_language: string;
  domain: string;
  definition: string;
  translations: { ar: string | null; en: string | null; fr: string | null };
  alternatives: { language: string; text: string; note: string | null }[];
  retain_original: boolean;
  source_authority: string | null;
  status: "PROPOSED" | "APPROVED" | "SUPERSEDED" | "REJECTED";
  provenance: { kind: string };
};

export type StrengthProfile = { relation: string; certainty: string; scope: string; markers: Record<string, string[]> };

export type TranslationCheck = {
  source_profile: StrengthProfile;
  translation_profile: StrengthProfile;
  strength_drift: { axis: string; direction: string; source_level: string; translation_level: string; message: string }[];
  terminology: { term_id: string; term: string; source_form: string; expected: string[]; found: boolean; message: string }[];
  passed: boolean;
};

export type Closure = {
  id: string;
  closure_type: string;
  record: { resolved: string[]; confidence_scope: string; limitations: string[] };
  closed_at: string;
  reopened_at: string | null;
  reopen_trigger: string | null;
};

export type OutputBlock = {
  kind: "HEADING" | "PARAGRAPH" | "CLAIM" | "EVIDENCE" | "QUOTE" | "LIST" | "NOTE";
  text: string;
  level?: number | null;
  items?: string[] | null;
  label?: string | null;
  trace: { entity_type: string; entity_id: string }[];
  quote?: { source_kind: string; excerpt_id?: string | null; quran_ref?: string | null; hadith_record_id?: string | null; text: string; language?: string | null } | null;
};

export type OutputVersion = {
  id: string;
  version_number: number;
  status: "DRAFT" | "APPROVED" | "SUPERSEDED";
  blocks: OutputBlock[];
  change_reason: string | null;
  approval_id: string | null;
  created_by: Actor;
  created_at: string;
  integrity: "VERIFIED" | "VERIFIED_WITH_WARNINGS" | "FAILED" | null;
};

export type Output = {
  id: string;
  project_id: string;
  output_type: string;
  title: string;
  language: "en" | "fr" | "ar";
  mode: "READABLE" | "REFERENCED" | "AUDIT";
  subject_type: string | null;
  subject_id: string | null;
  current_version: number;
  provenance: { kind: string };
  latest: OutputVersion;
};

export type IntegrityRun = {
  id: string;
  status: "VERIFIED" | "VERIFIED_WITH_WARNINGS" | "FAILED";
  steps: { step: string; status: "PASS" | "WARN" | "FAIL" | "SKIPPED"; findings: { code: string; message: string; block?: number | null }[] }[];
  created_at: string;
};

export type WorkspaceInfo = { adapter: string; enabled: boolean; remote: boolean; default_ttl_hours: number; max_ttl_hours: number; kinds: string[] };

export type StagedItem = { entity_type: string; entity_id: string; sha256: string; byte_size: number; remote_ref: string | null };

export type Staging = {
  id: string;
  adapter: string;
  purpose: string;
  status: "ACTIVE" | "BLOCKED" | "DELETED" | "EXPIRED";
  sensitivity: string;
  policy_decision: { allowed: boolean; reason: string };
  expires_at: string | null;
  staged_by: Actor;
  created_at: string;
  deleted_at: string | null;
  delete_reason: string | null;
  items: StagedItem[];
};

export type AIPolicy = {
  cloud_consent: boolean;
  allowed_profiles: string[];
  preferred_profile: string | null;
  project_budget_usd: string | null;
  task_budget_usd: string | null;
  spent_usd: string;
};
