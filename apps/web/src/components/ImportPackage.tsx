"use client";

import Link from "next/link";
import { useActionState } from "react";

import { importPackage } from "@/app/actions";
import { Field } from "@/components/fields";
import { INITIAL_RESULT } from "@/lib/form";
import type { Locale } from "@/lib/i18n";
import type { PortabilityStrings } from "@/lib/i18n-portability";

type Report = { project_id: string; assets_restored: number; metadata_only_assets: string[]; trust_notes: string[] };

export function ImportPackage({ t, locale }: { t: PortabilityStrings; locale: Locale }) {
  const [state, action, pending] = useActionState(importPackage, INITIAL_RESULT);
  const report = state.ok ? (state.details as unknown as Report) : null;
  return (
    <div className="space-y-3">
      <form action={action} className="space-y-3" data-testid="import-package">
        <p className="text-sm text-[var(--color-muted)]">{t.importExplainer}</p>
        <Field label={t.file}>
          <input type="file" name="file" accept=".zip,application/zip" required className="text-sm" />
        </Field>
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-sm font-medium text-white disabled:opacity-60 dark:text-black"
        >
          {pending ? t.importing : t.import}
        </button>
      </form>
      {!state.ok && state.message ? (
        <p role="alert" className="text-sm text-amber-800 dark:text-amber-200">
          {state.message}
        </p>
      ) : null}
      {report ? (
        <div role="status" className="space-y-1 text-sm" data-testid="import-report">
          <p>
            {t.imported} · {t.assetsRestored}: {report.assets_restored} · {t.metadataOnly}: {report.metadata_only_assets.length}
          </p>
          <ul className="list-disc ps-5 text-xs">
            {report.trust_notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
          <Link href={`/${locale}/projects/${report.project_id}`} className="underline">
            {t.open}
          </Link>
        </div>
      ) : null}
    </div>
  );
}
