import "server-only";

import { notFound } from "next/navigation";

import { ApiError, apiGet } from "@/lib/api";

/** Load secondary data for a server component; returns null on failure so the page shows a partial state. */
export async function load<T>(path: string): Promise<T | null> {
  try {
    return await apiGet<T>(path);
  } catch {
    return null;
  }
}

/** Service failures reach the route's error boundary, so an outage never reads as "not found". */
export class ServiceUnavailableError extends Error {}

/**
 * Load the entity a page is about. A missing entity is a 404. Any other failure throws to the error boundary,
 * which shows an error state with a retry.
 */
export async function loadEntity<T>(path: string): Promise<T> {
  try {
    return await apiGet<T>(path);
  } catch (error) {
    if (error instanceof ApiError && (error.status === 404 || error.status === 422)) notFound();
    throw new ServiceUnavailableError("The research service could not be reached.");
  }
}
