/** Shapes of API responses used by the UI (subset of the backend schemas). */
import type {
  AccessResponseForm,
  IngestionStatus,
  NotificationLevel,
  ProblemFrameStatus,
  ProjectInputType,
  ProjectStatus,
  QualityGateResult,
  ReferenceAuthorityLayer,
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
