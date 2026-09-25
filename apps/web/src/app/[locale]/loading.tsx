"use client";

import { useParams } from "next/navigation";

import { getDictionary, isLocale } from "@/lib/i18n";

/** Shown while a page's data loads (DoD §77: loading state). */
export default function Loading() {
  const params = useParams<{ locale: string }>();
  const locale = params.locale ?? "";
  const dict = getDictionary(isLocale(locale) ? locale : "en");
  return (
    <div role="status" aria-live="polite" className="p-6 text-sm text-[var(--color-muted)]" data-testid="page-loading">
      {dict.ui.loading}
    </div>
  );
}
