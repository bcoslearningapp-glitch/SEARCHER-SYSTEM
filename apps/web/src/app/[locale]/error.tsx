"use client";

import { useParams } from "next/navigation";

import { getDictionary, isLocale } from "@/lib/i18n";

/** Error state for any page under a locale (DoD §77). The research data is never at risk from a failed page. */
export default function PageError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const params = useParams<{ locale: string }>();
  const locale = params.locale ?? "";
  const dict = getDictionary(isLocale(locale) ? locale : "en");
  return (
    <div className="space-y-3 p-6" data-testid="page-error">
      <p role="alert" className="rounded-md border border-amber-500/50 p-4 text-amber-800 dark:text-amber-300">
        {dict.ui.loadError}
      </p>
      <button type="button" onClick={reset} className="rounded-md border px-3 py-1 text-sm">
        {dict.ui.retry}
      </button>
    </div>
  );
}
