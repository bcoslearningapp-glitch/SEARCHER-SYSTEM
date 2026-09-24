import { AppShell } from "@/components/AppShell";
import { SpacePlaceholder } from "@/components/SpacePlaceholder";
import { resolveLocale, type LocaleParams } from "@/lib/locale-params";

export default async function Page(props: LocaleParams) {
  const locale = await resolveLocale(props);
  return (
    <AppShell locale={locale} active="outputs">
      <SpacePlaceholder locale={locale} space="outputs" />
    </AppShell>
  );
}
