import Link from "next/link";

import { AppShell } from "@/components/AppShell";
import { Card, Empty } from "@/components/fields";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveLocale, type LocaleParams } from "@/lib/locale-params";
import type { Project } from "@/lib/types";

export const dynamic = "force-dynamic";

/** Outputs space: outputs live with their project, where their evidence is. */
export default async function Page(props: LocaleParams) {
  const locale = await resolveLocale(props);
  const dict = getDictionary(locale);
  const projects = await load<Project[]>("/api/v1/projects");
  return (
    <AppShell locale={locale} active="outputs">
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">{dict.spaces.outputs}</h1>
        <p className="text-[var(--color-muted)]">{dict.spaceDescriptions.outputs}</p>
        <Card title={dict.outputs.projects}>
          {projects?.length ? (
            <ul className="space-y-1 text-sm">
              {projects.map((p) => (
                <li key={p.id}>
                  <Link href={`/${locale}/projects/${p.id}/outputs`} className="underline" dir="auto">
                    {p.title}
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <Empty>{dict.outputs.noOutputs}</Empty>
          )}
        </Card>
      </div>
    </AppShell>
  );
}
