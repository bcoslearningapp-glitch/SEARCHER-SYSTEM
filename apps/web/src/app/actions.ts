"use server";

/**
 * Server actions: the browser posts forms here; the Next.js server calls the API.
 * All rules are enforced by the API; these functions only translate forms.
 */
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { ApiError, apiSend, apiUpload } from "@/lib/api";
import { frameFromForm, optionalText, text, type ActionResult } from "@/lib/form";
import type { Project } from "@/lib/types";

async function run(operation: () => Promise<unknown>): Promise<ActionResult> {
  try {
    await operation();
  } catch (error) {
    if (error instanceof ApiError) return { ok: false, message: error.message, details: error.details };
    return { ok: false, message: "The research service is unreachable. Your data is unchanged." };
  }
  revalidatePath("/", "layout");
  return { ok: true };
}

export async function createProject(_: ActionResult, form: FormData): Promise<ActionResult> {
  let created: Project | null = null;
  const result = await run(async () => {
    created = await apiSend<Project>("POST", "/api/v1/projects", {
      title: text(form, "title"),
      initial_input: text(form, "initial_input"),
      input_type: text(form, "input_type"),
      sensitivity: text(form, "sensitivity"),
      risk_level: text(form, "risk_level"),
      primary_language: text(form, "locale") || "en",
    });
  });
  if (created) redirect(`/${text(form, "locale") || "en"}/projects/${(created as Project).id}`);
  return result;
}

export async function saveFrameDraft(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("PUT", `/api/v1/projects/${text(form, "project_id")}/problem-frames/draft`, {
      content: frameFromForm(form),
    }),
  );
}

export async function approveFrame(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `/api/v1/projects/${text(form, "project_id")}/problem-frames/${text(form, "version_id")}/approve`, {
      acknowledge_reservations: form.get("acknowledge_reservations") === "on",
      reason: optionalText(form, "reason"),
    }),
  );
}

export async function addNote(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() => apiSend("POST", `/api/v1/projects/${text(form, "project_id")}/notes`, { body: text(form, "body") }));
}

export async function captureNote(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `/api/v1/projects/${text(form, "project_id")}/notes/${text(form, "note_id")}/capture`, {
      target: text(form, "target"),
    }),
  );
}

export async function createDecision(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `/api/v1/projects/${text(form, "project_id")}/decisions`, {
      question: text(form, "question"),
      options: text(form, "options")
        .split(/\r?\n/)
        .map((o) => o.trim())
        .filter(Boolean),
      blocking: form.get("blocking") === "on",
    }),
  );
}

export async function resolveDecision(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `/api/v1/projects/${text(form, "project_id")}/decisions/${text(form, "decision_id")}/resolve`, {
      final_decision: text(form, "final_decision"),
      human_justification: text(form, "human_justification"),
    }),
  );
}

export async function transitionProject(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `/api/v1/projects/${text(form, "project_id")}/transition`, {
      target: text(form, "target"),
      reason: optionalText(form, "reason"),
    }),
  );
}

export async function catalogSource(_: ActionResult, form: FormData): Promise<ActionResult> {
  const holding = text(form, "holding");
  const authors = text(form, "authors")
    .split(/[\n;]/)
    .map((a) => a.trim())
    .filter(Boolean);
  return run(() =>
    apiSend("POST", "/api/v1/sources", {
      work: { title: text(form, "title"), authors, authority_layer: text(form, "authority_layer") },
      edition: {
        edition_label: optionalText(form, "edition_label"),
        language: optionalText(form, "language"),
        publisher: optionalText(form, "publisher"),
      },
      holding: holding ? { access_mode: holding, note: optionalText(form, "holding_note") } : null,
      project_id: optionalText(form, "project_id") ?? null,
    }),
  );
}

export async function uploadAsset(_: ActionResult, form: FormData): Promise<ActionResult> {
  const file = form.get("file");
  if (!(file instanceof File) || file.size === 0) return { ok: false, message: "Choose a file to upload." };
  const payload = new FormData();
  payload.set("file", file, file.name);
  return run(() => apiUpload(`/api/v1/sources/editions/${text(form, "edition_id")}/assets`, payload));
}

export async function linkSource(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `/api/v1/projects/${text(form, "project_id")}/sources/${text(form, "work_id")}`, {}),
  );
}

export async function requestAccess(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `/api/v1/projects/${text(form, "project_id")}/access-requests`, {
      edition_id: text(form, "edition_id"),
      reason: text(form, "reason"),
      requested_scope: text(form, "requested_scope"),
      surrounding_context: optionalText(form, "surrounding_context"),
      acceptable_forms: form.getAll("acceptable_forms").map(String),
      priority: text(form, "priority") || "MEDIUM",
    }),
  );
}

export async function respondToAccess(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend(
      "POST",
      `/api/v1/projects/${text(form, "project_id")}/access-requests/${text(form, "request_id")}/responses`,
      {
        form: text(form, "form"),
        location: text(form, "location"),
        text: text(form, "text"),
        fulfills_request: form.get("fulfills_request") === "on",
      },
    ),
  );
}

// --- Lab: claims, assumptions, hypotheses, mechanisms, evidence, reference ---

const P = (form: FormData) => `/api/v1/projects/${text(form, "project_id")}`;

function listField(form: FormData, name: string): string[] {
  return text(form, name)
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
}

function hypothesisContent(form: FormData) {
  return {
    statement: text(form, "statement"),
    context: text(form, "context"),
    expected_outcome: text(form, "expected_outcome"),
    proposed_mechanism: text(form, "proposed_mechanism"),
    assumptions: listField(form, "assumptions"),
    boundary_conditions: listField(form, "boundary_conditions"),
    falsification_conditions: listField(form, "falsification_conditions"),
  };
}

export async function createClaim(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/claims`, {
      statement: text(form, "statement"),
      claim_type: text(form, "claim_type"),
      important: form.get("important") === "on",
    }),
  );
}

export async function createAssumption(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/assumptions`, { statement: text(form, "statement"), criticality: text(form, "criticality") }),
  );
}

export async function reviewAssumption(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/assumptions/${text(form, "assumption_id")}/review`, { status: text(form, "status") }),
  );
}

export async function createHypothesis(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() => apiSend("POST", `${P(form)}/hypotheses`, { content: { statement: text(form, "statement") } }));
}

export async function reviseHypothesis(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/hypotheses/${text(form, "hypothesis_id")}/revise`, {
      content: hypothesisContent(form),
      change_reason: text(form, "change_reason"),
    }),
  );
}

export async function transitionHypothesis(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/hypotheses/${text(form, "hypothesis_id")}/transition`, {
      target: text(form, "target"),
      reason: text(form, "reason"),
    }),
  );
}

export async function assessHypothesis(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/hypotheses/${text(form, "hypothesis_id")}/assess`, {
      epistemic_state: text(form, "epistemic_state"),
      reason: text(form, "reason"),
    }),
  );
}

export async function createMechanism(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/mechanisms`, { name: text(form, "name"), description: text(form, "description") }),
  );
}

export async function proposeEvidence(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/evidence`, {
      target_type: text(form, "target_type"),
      target_id: text(form, "target_id"),
      role: text(form, "role"),
      finding: text(form, "finding"),
      excerpt_id: text(form, "excerpt_id"),
      track: optionalText(form, "track") ?? null,
    }),
  );
}

export async function assessEvidence(_: ActionResult, form: FormData): Promise<ActionResult> {
  const decision = text(form, "decision");
  return run(() =>
    apiSend("POST", `${P(form)}/evidence/${text(form, "evidence_id")}/assess`, {
      decision,
      strength: decision === "ACCEPT" ? text(form, "strength") : undefined,
      limitations: optionalText(form, "limitations"),
    }),
  );
}

export async function recordTrack(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/research-tracks`, {
      target_type: text(form, "target_type"),
      target_id: text(form, "target_id"),
      track: text(form, "track"),
      outcome: text(form, "outcome"),
      scope: text(form, "scope"),
    }),
  );
}

export async function createReview(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/reference-reviews`, {
      target_type: text(form, "target_type"),
      target_id: text(form, "target_id"),
      question: text(form, "question"),
      analytical_category: text(form, "analytical_category"),
    }),
  );
}

export async function addReviewEntry(_: ActionResult, form: FormData): Promise<ActionResult> {
  const layer = text(form, "layer");
  return run(() =>
    apiSend("POST", `${P(form)}/reference-reviews/${text(form, "review_id")}/entries`, {
      layer,
      content: optionalText(form, "content"),
      quran_ref: optionalText(form, "quran_ref"),
    }),
  );
}

export async function judgeReview(_: ActionResult, form: FormData): Promise<ActionResult> {
  const state = text(form, "state");
  return run(() =>
    apiSend("POST", `${P(form)}/reference-reviews/${text(form, "review_id")}/judgments`, {
      state,
      directness: text(form, "directness"),
      reservation_type: state === "RESERVED" ? text(form, "reservation_type") : null,
      rationale: text(form, "rationale"),
    }),
  );
}

export async function launchAITask(_: ActionResult, form: FormData): Promise<ActionResult> {
  const targetId = optionalText(form, "target_id");
  const search =
    text(form, "task") === "web_search"
      ? {
          plan_id: optionalText(form, "plan_id") ?? null,
          track: optionalText(form, "track") ?? null,
          queries: listField(form, "queries"),
          languages: listField(form, "languages"),
        }
      : {};
  return run(() =>
    apiSend("POST", `${P(form)}/ai-tasks`, {
      task: text(form, "task"),
      target_type: targetId ? text(form, "target_type") : null,
      target_id: targetId ?? null,
      ...search,
    }),
  );
}

const TRACKS = ["SUPPORT", "CHALLENGE", "ALTERNATIVE_EXPLANATION"] as const;

export async function createResearchPlan(_: ActionResult, form: FormData): Promise<ActionResult> {
  const budget = optionalText(form, "max_web_searches");
  return run(() =>
    apiSend("POST", `${P(form)}/research-plans`, {
      question: text(form, "question"),
      decision_served: text(form, "decision_served"),
      question_type: text(form, "question_type"),
      risk_impact: text(form, "risk_impact"),
      desired_evidence_types: listField(form, "desired_evidence_types"),
      languages: listField(form, "languages"),
      tracks: TRACKS.map((track) => ({ track, approach: text(form, `approach_${track}`) })),
      sufficiency_criteria: listField(form, "sufficiency_criteria"),
      max_web_searches: budget ? Number(budget) : null,
    }),
  );
}

export async function searchLocalLibrary(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/searches/local`, {
      plan_id: text(form, "plan_id"),
      track: optionalText(form, "track") ?? null,
      queries: listField(form, "queries"),
      languages: listField(form, "languages"),
    }),
  );
}

const CONSIDERATIONS = [
  "support_evidence",
  "counter_evidence",
  "alternative_explanations",
  "independence",
  "diversity",
  "context_fit",
  "critical_unknowns",
  "impact",
  "reversibility",
  "remaining_uncertainty",
] as const;

export async function assessSufficiency(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/research-plans/${text(form, "plan_id")}/sufficiency`, {
      result: text(form, "result"),
      considerations: Object.fromEntries(CONSIDERATIONS.map((k) => [k, text(form, k)])),
      rationale: text(form, "rationale"),
      recommend_experiment: form.get("recommend_experiment") === "on",
    }),
  );
}

export async function importQuranDataset(_: ActionResult, form: FormData): Promise<ActionResult> {
  const file = form.get("file");
  if (!(file instanceof File) || file.size === 0) return { ok: false, message: "Choose the dataset file to import." };
  return run(async () => {
    // The Qur'an text is catalogued in its own authority layer, then staged; nothing is served until approved.
    const work = await apiSend<{ editions: { id: string }[]; id: string }>("POST", "/api/v1/sources", {
      work: { title: text(form, "title"), authors: [], authority_layer: "QURAN" },
      edition: { edition_label: text(form, "edition_version"), language: "ar", publisher: optionalText(form, "publisher") },
    });
    const payload = new FormData();
    payload.set("work_id", work.id);
    payload.set("edition_version", text(form, "edition_version"));
    payload.set("file", file, file.name);
    await apiUpload("/api/v1/reference/quran-datasets", payload);
  });
}

export async function approveFoundational(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `/api/v1/reference/foundational-sources/${text(form, "source_id")}/approve`, {
      reason: text(form, "reason"),
    }),
  );
}

// --- Design synthesis (PRD §32): requirements before solutions; selection is a human decision ---

const D = (form: FormData) => `${P(form)}/design`;

export async function createDesignRequirement(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${D(form)}/requirements`, {
      statement: text(form, "statement"),
      priority: text(form, "priority"),
      traces: [{ basis: text(form, "basis"), note: optionalText(form, "note") }],
    }),
  );
}

export async function confirmDesignRequirement(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() => apiSend("POST", `${D(form)}/requirements/${text(form, "requirement_id")}/confirm`, {}));
}

export async function withdrawDesignRequirement(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${D(form)}/requirements/${text(form, "requirement_id")}/withdraw`, { reason: text(form, "reason") }),
  );
}

export async function createDesignConcept(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${D(form)}/concepts`, {
      title: text(form, "title"),
      description: text(form, "description"),
      origin: text(form, "origin"),
      origin_reference: optionalText(form, "origin_reference"),
      hypothesis_ids: form.getAll("hypothesis_ids").map(String),
      mechanism_ids: form.getAll("mechanism_ids").map(String),
      derived_from_concept_ids: form.getAll("derived_from_concept_ids").map(String),
    }),
  );
}

export async function setDesignCoverage(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("PUT", `${D(form)}/concepts/${text(form, "concept_id")}/coverage`, {
      requirement_id: text(form, "requirement_id"),
      coverage: text(form, "coverage"),
      note: optionalText(form, "note"),
    }),
  );
}

export async function evaluateDesignReadiness(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() => apiSend("POST", `${D(form)}/concepts/${text(form, "concept_id")}/readiness`, {}));
}

export async function selectDesignConcept(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${D(form)}/concepts/${text(form, "concept_id")}/select`, {
      reason: optionalText(form, "reason"),
      acknowledge_reservations: form.get("acknowledge_reservations") === "on",
    }),
  );
}

export async function rejectDesignConcept(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${D(form)}/concepts/${text(form, "concept_id")}/reject`, {
      ground: text(form, "ground"),
      reason: text(form, "reason"),
      reusable_mechanism_ids: form.getAll("reusable_mechanism_ids").map(String),
    }),
  );
}

// --- Design hypotheses and experiments (PRD §33-34) ---

const CONTENT_TEXT = ["intervention", "target_population", "context", "mechanism", "expected_outcome", "measurement_plan"] as const;
const CONTENT_LISTS = ["failure_conditions", "side_effects", "stop_conditions"] as const;
const PROTOCOL = ["method", "sample", "duration", "data_collected", "analysis_plan", "success_criteria"] as const;
const X = (form: FormData) => `${P(form)}/experiments/${text(form, "experiment_id")}`;

export async function createDesignHypothesis(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/design-hypotheses`, {
      concept_id: text(form, "concept_id"),
      affects_people: form.get("affects_people") === "on",
      content: {
        ...Object.fromEntries(CONTENT_TEXT.map((k) => [k, text(form, k)])),
        ...Object.fromEntries(CONTENT_LISTS.map((k) => [k, listField(form, k)])),
      },
    }),
  );
}

export async function assessDesignHypothesis(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/design-hypotheses/${text(form, "design_hypothesis_id")}/assess`, {
      epistemic_state: text(form, "epistemic_state"),
      reason: text(form, "reason"),
    }),
  );
}

function protocolFromForm(form: FormData) {
  return Object.fromEntries(PROTOCOL.map((k) => [k, text(form, k)]));
}

export async function createExperiment(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/experiments`, {
      design_hypothesis_id: text(form, "design_hypothesis_id"),
      title: text(form, "title"),
      protocol: protocolFromForm(form),
    }),
  );
}

export async function updateProtocol(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() => apiSend("PUT", `${X(form)}/protocol`, { protocol: protocolFromForm(form), reason: text(form, "reason") || "Protocol updated" }));
}

export async function transitionExperiment(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${X(form)}/transition`, {
      target: text(form, "target"),
      reason: optionalText(form, "reason"),
      acknowledge_reservations: form.get("acknowledge_reservations") === "on",
    }),
  );
}

export async function assessHumanImpact(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${X(form)}/human-impact`, {
      dimension: text(form, "dimension"),
      finding: text(form, "finding"),
      note: text(form, "note"),
      external_authority: optionalText(form, "external_authority"),
    }),
  );
}

export async function recordObservation(_: ActionResult, form: FormData): Promise<ActionResult> {
  const observed = text(form, "observed_at");
  return run(() =>
    apiSend("POST", `${X(form)}/observations`, {
      description: text(form, "description"),
      observed_at: observed ? new Date(observed).toISOString() : new Date().toISOString(),
    }),
  );
}

export async function recordResult(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${X(form)}/results`, {
      observation_ids: form.getAll("observation_ids").map(String),
      method: text(form, "method"),
      summary: text(form, "summary"),
    }),
  );
}

export async function recordInterpretation(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${X(form)}/interpretations`, {
      result_ids: form.getAll("result_ids").map(String),
      outcome: text(form, "outcome"),
      statement: text(form, "statement"),
      limitations: optionalText(form, "limitations"),
    }),
  );
}

// --- Learning reviews and local knowledge (PRD §28-29, §35) ---

export async function recordLearningReview(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${X(form)}/learning-reviews`, {
      learned: text(form, "learned"),
      hypothesis_effect: text(form, "hypothesis_effect"),
      surprises: optionalText(form, "surprises"),
      limitations: listField(form, "limitations"),
      validity_threats: listField(form, "validity_threats"),
      next_steps: listField(form, "next_steps"),
    }),
  );
}

const KN = (form: FormData) => `${P(form)}/knowledge/${text(form, "knowledge_id")}`;

export async function createKnowledge(_: ActionResult, form: FormData): Promise<ActionResult> {
  const interval = optionalText(form, "revalidation_interval_days");
  return run(() =>
    apiSend("POST", `${P(form)}/knowledge`, {
      statement: text(form, "statement"),
      scope: text(form, "scope"),
      contexts: listField(form, "contexts"),
      evidence_basis: form.getAll("basis").map((value) => {
        const [entity_type, entity_id] = String(value).split(":");
        return { entity_type, entity_id };
      }),
      contrary_evidence_searched: form.get("contrary_evidence_searched") === "on",
      confidence: text(form, "confidence"),
      temporal_profile: text(form, "temporal_profile"),
      revalidation_interval_days: interval ? Number(interval) : null,
    }),
  );
}

export async function promoteKnowledge(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${KN(form)}/promote`, {
      target: text(form, "target"),
      reason: optionalText(form, "reason"),
      acknowledge_reservations: form.get("acknowledge_reservations") === "on",
    }),
  );
}

export async function changeKnowledgeStanding(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${KN(form)}/standing`, {
      action: text(form, "action"),
      reason: text(form, "reason"),
      target_stage: optionalText(form, "target_stage") ?? null,
    }),
  );
}

export async function reuseKnowledge(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${KN(form)}/reuse`, {
      target_project_id: text(form, "target_project_id"),
      transferability: text(form, "transferability"),
      rationale: text(form, "rationale"),
      differences: optionalText(form, "differences"),
    }),
  );
}

// --- Terminology and translation integrity (PRD §36) ---

export async function proposeTerm(_: ActionResult, form: FormData): Promise<ActionResult> {
  const alternatives = listField(form, "alternatives").map((line) => {
    const [language = "", ...rest] = line.split(":");
    return { language: language.trim(), text: rest.join(":").trim() };
  });
  return run(() =>
    apiSend("POST", "/api/v1/terminology", {
      term: text(form, "term"),
      original_language: text(form, "original_language"),
      domain: text(form, "domain"),
      definition: text(form, "definition"),
      translations: { ar: optionalText(form, "ar"), en: optionalText(form, "en"), fr: optionalText(form, "fr") },
      alternatives,
      retain_original: form.get("retain_original") === "on",
      source_authority: optionalText(form, "source_authority"),
    }),
  );
}

export async function decideTerm(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `/api/v1/terminology/${text(form, "term_id")}/${text(form, "decision")}`, { reason: optionalText(form, "reason") }),
  );
}

export async function checkTranslation(_: ActionResult, form: FormData): Promise<ActionResult> {
  try {
    const result = await apiSend<Record<string, unknown>>("POST", "/api/v1/integrity/translation-check", {
      source_text: text(form, "source_text"),
      source_language: text(form, "source_language"),
      translated_text: text(form, "translated_text"),
      target_language: text(form, "target_language"),
      domain: optionalText(form, "domain"),
    });
    return { ok: true, details: result };
  } catch (error) {
    if (error instanceof ApiError) return { ok: false, message: error.message, details: error.details };
    return { ok: false, message: "The research service is unreachable." };
  }
}

// --- Project closure and reopening (Core §66-67) ---

export async function closeProject(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/close`, {
      closure_type: text(form, "closure_type"),
      resolved: listField(form, "resolved"),
      unresolved: listField(form, "unresolved"),
      confidence_scope: text(form, "confidence_scope"),
      limitations: listField(form, "limitations"),
      open_questions: listField(form, "open_questions"),
      reopen_triggers: listField(form, "reopen_triggers"),
      acknowledge_reservations: form.get("acknowledge_reservations") === "on",
      override_reason: optionalText(form, "override_reason"),
    }),
  );
}

export async function reopenProject(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() => apiSend("POST", `${P(form)}/reopen`, { trigger: text(form, "trigger") }));
}

// --- Outputs (PRD §37) ---

const O = (form: FormData) => `${P(form)}/outputs/${text(form, "output_id")}`;

export async function createOutput(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/outputs`, {
      output_type: text(form, "output_type"),
      title: text(form, "title"),
      language: text(form, "language"),
      mode: text(form, "mode"),
      subject_id: optionalText(form, "subject_id") ?? null,
    }),
  );
}

export async function recomposeOutput(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() => apiSend("POST", `${O(form)}/recompose`, {}));
}

export async function setOutputMode(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() => apiSend("PATCH", O(form), { mode: text(form, "mode") }));
}

export async function approveOutputVersion(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${O(form)}/versions/${text(form, "version_id")}/approve`, {
      reason: optionalText(form, "reason"),
      acknowledge_warnings: form.get("acknowledge_warnings") === "on",
    }),
  );
}

export async function runOutputIntegrity(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() => apiSend("POST", `${O(form)}/versions/${text(form, "version_id")}/integrity`, {}));
}

// --- Research Core Package import (PRD §45) ---

export async function importPackage(_: ActionResult, form: FormData): Promise<ActionResult> {
  const file = form.get("file");
  if (!(file instanceof File) || file.size === 0) return { ok: false, message: "Choose the package file." };
  const payload = new FormData();
  payload.set("file", file, file.name);
  try {
    const report = await apiUpload<Record<string, unknown>>("/api/v1/packages/import", payload);
    revalidatePath("/", "layout");
    return { ok: true, details: report };
  } catch (error) {
    if (error instanceof ApiError) return { ok: false, message: error.message, details: error.details };
    return { ok: false, message: "The research service is unreachable. Your data is unchanged." };
  }
}

export async function stageInWorkspace(_: ActionResult, form: FormData): Promise<ActionResult> {
  const items = form
    .getAll("items")
    .filter((v): v is string => typeof v === "string" && v.includes(":"))
    .map((v) => {
      const [entity_type, entity_id] = v.split(":");
      return { entity_type, entity_id };
    });
  if (items.length === 0) return { ok: false, message: "Select at least one record." };
  const ttl = optionalText(form, "ttl_hours");
  return run(() =>
    apiSend("POST", `${P(form)}/workspace/stagings`, {
      purpose: text(form, "purpose"),
      items,
      ttl_hours: ttl ? Number(ttl) : null,
    }),
  );
}

export async function deleteWorkspaceStaging(_: ActionResult, form: FormData): Promise<ActionResult> {
  return run(() =>
    apiSend("POST", `${P(form)}/workspace/stagings/${text(form, "staging_id")}/delete`, { reason: text(form, "reason") }),
  );
}

export async function runInstallationAudit(): Promise<ActionResult> {
  return run(() => apiSend("POST", "/api/v1/ai/reliability/audit", {}));
}

export async function updateAIPolicy(_: ActionResult, form: FormData): Promise<ActionResult> {
  const budget = (name: string) => optionalText(form, name) ?? null;
  return run(() =>
    apiSend("PUT", `${P(form)}/ai-policy`, {
      cloud_consent: form.get("cloud_consent") === "on",
      allowed_profiles: form.getAll("allowed_profiles").filter((v): v is string => typeof v === "string"),
      preferred_profile: optionalText(form, "preferred_profile") ?? null,
      project_budget_usd: budget("project_budget_usd"),
      task_budget_usd: budget("task_budget_usd"),
    }),
  );
}
