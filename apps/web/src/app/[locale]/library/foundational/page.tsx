import { approveFoundational, importQuranDataset } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, TextInput } from "@/components/fields";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveLocale, type LocaleParams } from "@/lib/locale-params";
import type { Ayah, FoundationalSource, Work } from "@/lib/types";

export const dynamic = "force-dynamic";

type Props = LocaleParams & { searchParams: Promise<{ surah?: string; ayah?: string; to?: string }> };

const positive = (value: string | undefined) => (value && /^\d{1,3}$/.test(value) && Number(value) > 0 ? Number(value) : null);

/** Foundational library (PRD §18-20, ADR-009): import, review and approve the Qur'an text; look up ayat. */
export default async function FoundationalPage(props: Props) {
  const locale = await resolveLocale(props);
  const params = await props.searchParams;
  const dict = getDictionary(locale);
  const f = dict.foundational;
  const surah = positive(params.surah);
  const ayah = positive(params.ayah);
  const to = positive(params.to);
  const [sources, works, ayat] = await Promise.all([
    load<FoundationalSource[]>("/api/v1/reference/foundational-sources"),
    load<Work[]>("/api/v1/sources"),
    surah && ayah
      ? load<Ayah[]>(`/api/v1/reference/quran/${surah}/${ayah}${to && to > ayah ? `?to=${to}` : ""}`)
      : Promise.resolve(null),
  ]);
  const titles = new Map((works ?? []).map((w) => [w.id, w.title]));
  const hasApproved = (sources ?? []).some((s) => s.authority_layer === "QURAN" && s.status === "APPROVED");

  return (
    <AppShell locale={locale} active="library">
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">{f.title}</h1>
        <p className="text-[var(--color-muted)]">{f.explainer}</p>

        <Card title={f.sources} testId="foundational-sources">
          {sources?.length ? (
            <ul className="space-y-3 text-sm">
              {sources.map((s) => (
                <li key={s.id} className="space-y-2 rounded-md border border-[var(--color-border)] p-3" data-testid="foundational-source">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium" dir="auto">
                      {titles.get(s.work_id) ?? s.work_id}
                    </span>
                    <Badge>{s.authority_layer}</Badge>
                    <Badge tone={s.status === "APPROVED" ? "good" : s.status === "STAGED" ? "warn" : "neutral"}>{s.status}</Badge>
                  </div>
                  <dl className="grid gap-1 sm:grid-cols-[12rem_1fr]">
                    <dt className="text-[var(--color-muted)]">{f.version}</dt>
                    <dd dir="auto">{s.edition_version}</dd>
                    <dt className="text-[var(--color-muted)]">{f.fingerprint}</dt>
                    <dd className="font-mono text-xs break-all">{s.sha256}</dd>
                    <dt className="text-[var(--color-muted)]">{f.contents}</dt>
                    <dd>
                      {s.dataset_summary.surahs ?? "—"} {f.surah} · {s.dataset_summary.ayat ?? "—"} {f.ayah}
                      {s.dataset_summary.format ? ` · ${s.dataset_summary.format}` : ""}
                    </dd>
                    {s.approved_by ? (
                      <>
                        <dt className="text-[var(--color-muted)]">{f.approvedBy}</dt>
                        <dd>
                          {s.approved_by.id} · {s.approved_at ? new Date(s.approved_at).toLocaleString(locale) : ""}
                        </dd>
                      </>
                    ) : null}
                  </dl>
                  {s.status === "STAGED" ? (
                    <div className="border-t border-[var(--color-border)] pt-2">
                      <h3 className="text-sm font-semibold">{f.approveTitle}</h3>
                      <p className="text-[var(--color-muted)]">{f.approveExplainer}</p>
                      <ActionForm action={approveFoundational} submitLabel={f.approve} pendingLabel={f.approving} testId="approve-foundational">
                        <input type="hidden" name="source_id" value={s.id} />
                        <Field label={f.reason}>
                          <TextInput name="reason" required />
                        </Field>
                      </ActionForm>
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : (
            <Empty>{f.none}</Empty>
          )}
        </Card>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card title={f.importTitle} testId="import-quran">
            <p className="text-sm text-[var(--color-muted)]">{f.importExplainer}</p>
            <ActionForm action={importQuranDataset} submitLabel={f.import} pendingLabel={f.importing} successMessage={f.imported}>
              <Field label={f.workTitle}>
                <TextInput name="title" required defaultValue="القرآن الكريم — The Qur'an" />
              </Field>
              <Field label={f.editionVersion} hint={f.editionHint}>
                <TextInput name="edition_version" required />
              </Field>
              <Field label={f.publisher}>
                <TextInput name="publisher" defaultValue="King Fahd Glorious Qur'an Printing Complex (KFGQPC)" />
              </Field>
              <Field label={f.file}>
                <input type="file" name="file" required accept=".json,.txt,application/json,text/plain" className="text-sm" />
              </Field>
            </ActionForm>
          </Card>

          <Card title={f.lookup} testId="quran-lookup">
            <form method="get" className="flex flex-wrap items-end gap-2">
              <Field label={f.surah}>
                <TextInput name="surah" type="number" min={1} max={114} defaultValue={surah ?? ""} required />
              </Field>
              <Field label={f.ayah}>
                <TextInput name="ayah" type="number" min={1} defaultValue={ayah ?? ""} required />
              </Field>
              <Field label={f.to}>
                <TextInput name="to" type="number" min={1} defaultValue={to ?? ""} />
              </Field>
              <button type="submit" className="rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-sm font-medium text-white dark:text-black">
                {f.show}
              </button>
            </form>
            {!hasApproved ? <Empty>{f.noApproved}</Empty> : null}
            {ayat?.length ? (
              <div className="space-y-2" data-testid="ayat">
                {/* Exact approved text, never re-typed or generated. Shown as published: some datasets
                    (e.g. KFGQPC) already end each ayah with its number, so none is added here. */}
                <p lang="ar" dir="rtl" className="quran-text" data-testid="ayah-text">
                  {ayat.map((a) => (
                    <span key={a.ayah_number} data-ayah={a.ayah_number}>
                      {a.text}{" "}
                    </span>
                  ))}
                </p>
                <p className="text-xs text-[var(--color-muted)]">
                  <span dir="auto">{ayat[0]!.surah_name}</span> {ayat[0]!.surah_number}:{ayat[0]!.ayah_number}
                  {ayat.length > 1 ? `–${ayat[ayat.length - 1]!.ayah_number}` : ""} · {f.servedFrom}{" "}
                  <span dir="auto">{ayat[0]!.source_version}</span> ·{" "}
                  <span className="font-mono">{ayat[0]!.source_sha256.slice(0, 12)}…</span>
                </p>
              </div>
            ) : null}
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
