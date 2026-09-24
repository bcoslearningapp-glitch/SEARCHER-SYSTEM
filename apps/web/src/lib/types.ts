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
