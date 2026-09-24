import Link from "next/link";

import { createProject } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, Select, TextArea, TextInput } from "@/components/fields";
import { LoadError } from "@/components/LoadError";
import { StatusPanel } from "@/components/StatusPanel";
import { getReadiness } from "@/lib/api";
import { ProjectInputTypeValues, RiskLevelValues, SensitivityLevelValues } from "@/lib/contracts/enums";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveLocale, type LocaleParams } from "@/lib/locale-params";
import type { Project } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function DeskPage(props: LocaleParams) {
  const locale = await resolveLocale(props);
  const dict = getDictionary(locale);
  const ui = dict.ui;
  const [readiness, projects] = await Promise.all([getReadiness(), load<Project[]>("/api/v1/projects")]);
  return (
    <AppShell locale={locale} active="desk">
      <div className="grid gap-6 md:grid-cols-[2fr_1fr]">
        <div className="space-y-6">
          <h1 className="text-2xl font-semibold">{dict.spaces.desk}</h1>
          <Card title={ui.projects} testId="project-list">
            {projects === null ? (
              <LoadError dict={dict} />
            ) : projects.length === 0 ? (
              <Empty>{ui.noProjects}</Empty>
            ) : (
              <ul className="divide-y divide-[var(--color-border)]">
                {projects.map((p) => (
                  <li key={p.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
                    <Link href={`/${locale}/projects/${p.id}`} className="font-medium underline-offset-2 hover:underline" dir="auto">
                      {p.title}
                    </Link>
                    <span className="flex gap-2">
                      <Badge>{p.status}</Badge>
                      <Badge>{p.research_mode}</Badge>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
          <Card title={ui.newProject} testId="new-project">
            <ActionForm action={createProject} submitLabel={ui.create} pendingLabel={ui.creating}>
              <input type="hidden" name="locale" value={locale} />
              <Field label={ui.title}>
                <TextInput name="title" required maxLength={500} />
              </Field>
              <Field label={ui.initialInput} hint={ui.initialInputHint}>
                <TextArea name="initial_input" required />
              </Field>
              <div className="grid gap-3 sm:grid-cols-3">
                <Field label={ui.inputType}>
                  <Select name="input_type" defaultValue="RAW_QUESTION">
                    {ProjectInputTypeValues.map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </Select>
                </Field>
                <Field label={ui.sensitivity}>
                  <Select name="sensitivity" defaultValue="NORMAL">
                    {SensitivityLevelValues.map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </Select>
                </Field>
                <Field label={ui.riskLevel}>
                  <Select name="risk_level" defaultValue="L1_EXPLORATORY">
                    {RiskLevelValues.map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </Select>
                </Field>
              </div>
            </ActionForm>
          </Card>
        </div>
        <StatusPanel result={readiness} dict={dict} />
      </div>
    </AppShell>
  );
}
