import "server-only";

import { apiGet } from "@/lib/api";

/** Load for a server component; returns null on failure so pages render an error state instead of crashing. */
export async function load<T>(path: string): Promise<T | null> {
  try {
    return await apiGet<T>(path);
  } catch {
    return null;
  }
}
