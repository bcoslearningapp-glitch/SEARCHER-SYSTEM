"use client";

import { useActionState } from "react";

import { checkTranslation } from "@/app/actions";
import { Badge, Field, Select, TextArea, TextInput } from "@/components/fields";
import type { TerminologyStrings } from "@/lib/i18n-terminology";
import { INITIAL_RESULT } from "@/lib/form";
import type { TranslationCheck as Check } from "@/lib/types";

const LANGUAGES = ["en", "fr", "ar"] as const;

/** Deterministic claim-strength and terminology screen (FR-TERM-003); results are for a person to review. */
export function TranslationCheck({ t }: { t: TerminologyStrings }) {
  const [state, action, pending] = useActionState(checkTranslation, INITIAL_RESULT);
  const result = state.ok ? (state.details as unknown as Check) : null;
  return (
    <div className="space-y-3">
      <form action={action} className="space-y-3" data-testid="translation-check">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="space-y-2">
            <Field label={t.sourceLanguage}>
              <Select name="source_language" defaultValue="en">
                {LANGUAGES.map((l) => (
                  <option key={l}>{l}</option>
                ))}
              </Select>
            </Field>
            <Field label={t.sourceText}>
              <TextArea name="source_text" rows={4} required dir="auto" />
            </Field>
          </div>
          <div className="space-y-2">
            <Field label={t.targetLanguage}>
              <Select name="target_language" defaultValue="fr">
                {LANGUAGES.map((l) => (
                  <option key={l}>{l}</option>
                ))}
              </Select>
            </Field>
            <Field label={t.translatedText}>
              <TextArea name="translated_text" rows={4} required dir="auto" />
            </Field>
          </div>
        </div>
        <Field label={t.domain}>
          <TextInput name="domain" />
        </Field>
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-sm font-medium text-white disabled:opacity-60 dark:text-black"
        >
          {pending ? t.checking : t.check}
        </button>
      </form>
      {!state.ok && state.message ? (
        <p role="alert" className="text-sm text-amber-800 dark:text-amber-200">
          {state.message}
        </p>
      ) : null}
      {result ? (
        <div className="space-y-2 text-sm" data-testid="check-result">
          <Badge tone={result.passed ? "good" : "warn"}>{result.passed ? t.noDrift : t.review}</Badge>
          <p className="text-xs text-[var(--color-muted)]">{t.screenNote}</p>
          <p>
            {t.source}: {result.source_profile.relation} · {result.source_profile.certainty} · {result.source_profile.scope}
            <br />
            {t.translation}: {result.translation_profile.relation} · {result.translation_profile.certainty} ·{" "}
            {result.translation_profile.scope}
          </p>
          {result.strength_drift.length ? (
            <ul className="list-disc ps-5" data-testid="drift">
              {result.strength_drift.map((d) => (
                <li key={d.axis}>
                  <strong>{d.direction}</strong> ({d.axis}: {d.source_level} → {d.translation_level}) — {d.message}
                </li>
              ))}
            </ul>
          ) : null}
          {result.terminology.length ? (
            <ul className="list-disc ps-5" data-testid="term-findings">
              {result.terminology.map((f) => (
                <li key={f.term_id}>
                  <span dir="auto">{f.term}</span>: {f.found ? "✓" : "✗"} {f.message} ({f.expected.join(" / ")})
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
