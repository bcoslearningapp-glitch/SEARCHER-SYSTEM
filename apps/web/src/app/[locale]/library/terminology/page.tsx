import { decideTerm, proposeTerm } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, Select, TextArea, TextInput } from "@/components/fields";
import { TranslationCheck } from "@/components/TranslationCheck";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveLocale, type LocaleParams } from "@/lib/locale-params";
import type { Term } from "@/lib/types";

export const dynamic = "force-dynamic";

/** Canonical terminology (FR-TERM-001/002) and the translation integrity check (FR-TERM-003). */
export default async function TerminologyPage(props: LocaleParams) {
  const locale = await resolveLocale(props);
  const dict = getDictionary(locale);
  const t = dict.terminology;
  const terms = await load<Term[]>("/api/v1/terminology");

  return (
    <AppShell locale={locale} active="library">
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">{t.title}</h1>
        <p className="text-[var(--color-muted)]">{t.explainer}</p>
        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <Card title={t.terms} testId="terms">
            {terms?.length ? (
              <ul className="space-y-3 text-sm">
                {terms.map((term) => (
                  <li key={term.id} className="space-y-1 rounded-md border border-[var(--color-border)] p-2" data-testid="term-row">
                    <div className="flex flex-wrap items-center gap-2">
                      <span dir="auto" className="font-medium">{term.term}</span>
                      <Badge tone={term.status === "APPROVED" ? "good" : "neutral"}>{term.status}</Badge>
                      <Badge>{term.domain}</Badge>
                      <Badge>v{term.version_number}</Badge>
                      {term.retain_original ? <Badge>{t.retainOriginal}</Badge> : null}
                      {term.provenance.kind === "AI_GENERATED" ? <Badge tone="warn">AI</Badge> : null}
                    </div>
                    <p dir="auto">{term.definition}</p>
                    <p className="text-xs">
                      ar: <span dir="rtl">{term.translations.ar ?? "—"}</span> · en: {term.translations.en ?? "—"} · fr:{" "}
                      {term.translations.fr ?? "—"}
                    </p>
                    {term.status === "PROPOSED" ? (
                      <div className="flex flex-wrap gap-2">
                        {(["approve", "reject"] as const).map((decision) => (
                          <ActionForm key={decision} action={decideTerm} submitLabel={t[decision]} pendingLabel={t.saving} className="flex items-end gap-2">
                            <input type="hidden" name="term_id" value={term.id} />
                            <input type="hidden" name="decision" value={decision} />
                            <TextInput name="reason" placeholder={t.reason} aria-label={t.reason} />
                          </ActionForm>
                        ))}
                      </div>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{t.noTerms}</Empty>
            )}
          </Card>

          <Card title={t.propose} testId="propose-term">
            <ActionForm action={proposeTerm} submitLabel={t.propose} pendingLabel={t.saving}>
              <Field label={t.term}>
                <TextInput name="term" required dir="auto" />
              </Field>
              <Field label={t.originalLanguage}>
                <Select name="original_language" defaultValue={locale}>
                  {(["en", "fr", "ar"] as const).map((l) => (
                    <option key={l}>{l}</option>
                  ))}
                </Select>
              </Field>
              <Field label={t.domain}>
                <TextInput name="domain" required />
              </Field>
              <Field label={t.definition}>
                <TextArea name="definition" rows={2} required dir="auto" />
              </Field>
              {(["ar", "en", "fr"] as const).map((l) => (
                <Field key={l} label={l}>
                  <TextInput name={l} dir={l === "ar" ? "rtl" : "ltr"} />
                </Field>
              ))}
              <Field label={t.alternatives} hint={t.alternativesHint}>
                <TextArea name="alternatives" rows={2} />
              </Field>
              <Field label={t.sourceAuthority}>
                <TextInput name="source_authority" />
              </Field>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" name="retain_original" />
                {t.retainOriginal}
              </label>
            </ActionForm>
          </Card>
        </div>

        <Card title={t.checkTitle} testId="translation-integrity">
          <p className="text-sm text-[var(--color-muted)]">{t.checkExplainer}</p>
          <TranslationCheck t={t} />
        </Card>
      </div>
    </AppShell>
  );
}
