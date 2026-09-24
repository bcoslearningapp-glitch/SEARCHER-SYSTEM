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

function apiBaseUrl(): string {
  return process.env.API_INTERNAL_URL ?? "http://localhost:8000";
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
