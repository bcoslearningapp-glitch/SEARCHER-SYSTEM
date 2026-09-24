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
