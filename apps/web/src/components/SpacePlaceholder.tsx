import { getDictionary, type Locale, type Space } from "@/lib/i18n";

export function SpacePlaceholder({ locale, space }: { locale: Locale; space: Space }) {
  const dict = getDictionary(locale);
  return (
    <section className="space-y-2">
      <h1 className="text-2xl font-semibold">{dict.spaces[space]}</h1>
      <p className="text-[var(--color-muted)]">{dict.spaceDescriptions[space]}</p>
      <p className="rounded-md border border-dashed border-[var(--color-border)] p-6 text-center text-[var(--color-muted)]">
        {dict.notYetAvailable}
      </p>
    </section>
  );
}
