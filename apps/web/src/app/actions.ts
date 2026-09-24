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
