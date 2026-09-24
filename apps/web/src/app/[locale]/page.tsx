import { AppShell } from "@/components/AppShell";
import { StatusPanel } from "@/components/StatusPanel";
import { getReadiness } from "@/lib/api";
import { getDictionary } from "@/lib/i18n";
import { resolveLocale, type LocaleParams } from "@/lib/locale-params";

export const dynamic = "force-dynamic";

export default async function DeskPage(props: LocaleParams) {
  const locale = await resolveLocale(props);
  const dict = getDictionary(locale);
  const readiness = await getReadiness();
  return (
    <AppShell locale={locale} active="desk">
      <div className="grid gap-6 md:grid-cols-[2fr_1fr]">
        <section className="space-y-2">
          <h1 className="text-2xl font-semibold">{dict.spaces.desk}</h1>
          <p className="text-[var(--color-muted)]">{dict.spaceDescriptions.desk}</p>
          <p className="rounded-md border border-dashed border-[var(--color-border)] p-6 text-center text-[var(--color-muted)]">
            {dict.notYetAvailable}
          </p>
        </section>
        <StatusPanel result={readiness} dict={dict} />
      </div>
    </AppShell>
  );
}
