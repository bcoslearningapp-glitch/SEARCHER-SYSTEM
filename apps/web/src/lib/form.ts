/** Pure helpers for turning form fields into API payloads. */
import { FRAME_LIST_FIELDS, FRAME_TEXT_FIELDS, type FrameContent } from "@/lib/types";

export type ActionResult = { ok: boolean; message?: string; details?: Record<string, unknown> };

export const INITIAL_RESULT: ActionResult = { ok: false };

export function text(form: FormData, name: string): string {
  const value = form.get(name);
  return typeof value === "string" ? value.trim() : "";
}

export function optionalText(form: FormData, name: string): string | undefined {
  return text(form, name) || undefined;
}

/** One item per non-empty line. */
export function lines(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

export function frameFromForm(form: FormData): FrameContent {
  const content = {} as FrameContent;
  for (const field of FRAME_TEXT_FIELDS) content[field] = text(form, field);
  for (const field of FRAME_LIST_FIELDS) content[field] = lines(text(form, field));
  return content;
}
