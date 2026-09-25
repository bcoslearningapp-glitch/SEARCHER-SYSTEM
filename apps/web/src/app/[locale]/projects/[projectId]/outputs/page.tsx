import Link from "next/link";

import { createOutput } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, Select, TextInput } from "@/components/fields";
import { ProjectHeader } from "@/components/ProjectHeader";
import { OutputModeValues, OutputTypeValues } from "@/lib/contracts/enums";
import { getDictionary } from "@/lib/i18n";
import { load, loadEntity } from "@/lib/load";
import { resolveProjectParams, type ProjectParams } from "@/lib/locale-params";
import type { Experiment, Hypothesis, Output, Project } from "@/lib/types";

export const dynamic = "force-dynamic";

/** Outputs composed from canonical project state (PRD §37). */
export default async function OutputsPage(props: ProjectParams) {
  const { locale, projectId } = await resolveProjectParams(props);
  const dict = getDictionary(locale);
  const t = dict.outputs;
  const base = `/api/v1/projects/${projectId}`;
  const project = await loadEntity<Project>(base);
  const [outputs, hypotheses, experiments] = await Promise.all([
    load<Output[]>(`${base}/outputs`),
    load<Hypothesis[]>(`${base}/hypotheses`),
    load<Experiment[]>(`${base}/experiments`),
  ]);

  return (
    <AppShell locale={locale} active="outputs">
      <div className="space-y-6">
        <ProjectHeader project={project} dict={dict} locale={locale} active="outputs" />
        <p className="text-sm text-[var(--color-muted)]">{t.explainer}</p>
        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <Card title={t.outputs} testId="outputs">
            {outputs?.length ? (
              <ul className="space-y-2 text-sm">
                {outputs.map((o) => (
                  <li key={o.id} className="flex flex-wrap items-center gap-2" data-testid="output-row">
                    <Link href={`/${locale}/projects/${projectId}/outputs/${o.id}`} className="font-medium underline" dir="auto">
                      {o.title}
                    </Link>
                    <Badge>{o.output_type}</Badge>
                    <Badge>{o.mode}</Badge>
                    <Badge>{o.language}</Badge>
                    <Badge tone={o.latest.status === "APPROVED" ? "good" : "neutral"}>
                      v{o.current_version} {o.latest.status}
                    </Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{t.noOutputs}</Empty>
            )}
          </Card>
          <Card title={t.newOutput} testId="new-output">
            <ActionForm action={createOutput} submitLabel={t.create} pendingLabel={t.saving}>
              <input type="hidden" name="project_id" value={projectId} />
              <Field label={t.type}>
                <Select name="output_type" defaultValue="RESEARCH_REPORT">
                  {OutputTypeValues.map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </Select>
              </Field>
              <Field label={t.title}>
                <TextInput name="title" required />
              </Field>
              <Field label={t.language}>
                <Select name="language" defaultValue={locale}>
                  {(["en", "fr", "ar"] as const).map((l) => (
                    <option key={l}>{l}</option>
                  ))}
                </Select>
              </Field>
              <Field label={t.mode}>
                <Select name="mode" defaultValue="REFERENCED">
                  {OutputModeValues.map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </Select>
              </Field>
              <Field label={t.subject}>
                <Select name="subject_id" defaultValue="">
                  <option value="">—</option>
                  {(hypotheses ?? []).map((h) => (
                    <option key={h.id} value={h.id}>
                      Hypothesis: {h.content.statement}
                    </option>
                  ))}
                  {(experiments ?? []).map((e) => (
                    <option key={e.id} value={e.id}>
                      Experiment: {e.title}
                    </option>
                  ))}
                </Select>
              </Field>
            </ActionForm>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
