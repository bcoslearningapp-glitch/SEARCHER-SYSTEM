/**
 * Server-side API client. Runs only on the Next.js server; no secrets or
 * internal URLs are shipped to the browser (PRD §68 SEC-002).
 */
import "server-only";

export type Readiness = {
  status: "ready" | "degraded" | "unavailable";
  database: "ok" | "unavailable";
  queue: "ok" | "unavailable";
  ai_providers_configured: string[];
};

export type ReadinessResult = { reachable: true; readiness: Readiness } | { reachable: false };

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly details: Record<string, unknown> = {},
  ) {
    super(message);
  }
}

function apiBaseUrl(): string {
  return process.env.API_INTERNAL_URL ?? "http://localhost:8000";
}

async function parse<T>(response: Response): Promise<T> {
  const body = (await response.json().catch(() => null)) as unknown;
  if (!response.ok) {
    const error = (body as { error?: { message?: string; details?: Record<string, unknown> } } | null)?.error;
    const detail = (body as { detail?: unknown } | null)?.detail;
    const message =
      error?.message ??
      (typeof detail === "string" ? detail : Array.isArray(detail) ? "The submitted data is invalid." : null) ??
      `Request failed (${response.status})`;
    throw new ApiError(response.status, message, error?.details ?? {});
  }
  return body as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, { cache: "no-store", signal: AbortSignal.timeout(10_000) });
  return parse<T>(response);
}

export async function apiSend<T>(method: "POST" | "PUT" | "PATCH", path: string, body: unknown): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
    signal: AbortSignal.timeout(30_000),
  });
  return parse<T>(response);
}

export async function apiUpload<T>(path: string, form: FormData): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    method: "POST",
    body: form,
    cache: "no-store",
    signal: AbortSignal.timeout(120_000),
  });
  return parse<T>(response);
}

export async function getReadiness(): Promise<ReadinessResult> {
  try {
    const response = await fetch(`${apiBaseUrl()}/health/ready`, {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
    // 503 still carries a structured body describing which component failed.
    const readiness = (await response.json()) as Readiness;
    return { reachable: true, readiness };
  } catch {
    return { reachable: false };
  }
}

/** Raw passthrough for downloads (exports); the browser never learns the API's internal URL. */
export async function apiRaw(path: string): Promise<Response> {
  return fetch(`${apiBaseUrl()}${path}`, { cache: "no-store", signal: AbortSignal.timeout(30_000) });
}
