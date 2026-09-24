"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

/** Re-renders the page from the server while background work is in flight. Status lives in the API, not here. */
export function AutoRefresh({ active, intervalMs = 2000 }: { active: boolean; intervalMs?: number }) {
  const router = useRouter();
  useEffect(() => {
    if (!active) return;
    const timer = setInterval(() => router.refresh(), intervalMs);
    return () => clearInterval(timer);
  }, [active, intervalMs, router]);
  return null;
}
