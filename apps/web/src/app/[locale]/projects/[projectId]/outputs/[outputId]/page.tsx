import { notFound } from "next/navigation";

import { approveOutputVersion, recomposeOutput, setOutputMode } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Field, Select, TextInput } from "@/components/fields";
import { OutputBlocks } from "@/components/OutputBlocks";
import { ProjectHeader } from "@/components/ProjectHeader";
import { OutputModeValues } from "@/lib/contracts/enums";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveLocale } from "@/lib/locale-params";
import type { Output, OutputVersion, Project } from "@/lib/types";

export const dynamic = "force-dynamic";

type Props = { params: Promise<{ locale: string; projectId: string; outputId: string }> };

export default async function OutputPage(props: Props) {
  const { projectId, outputId } = await props.params;
  const locale = await resolveLocale({ params: props.params });
  if (!/^[0-9a-f-]{36}$/i.test(projectId) || !/^[0-9a-f-]{36}$/i.test(outputId)) notFound();
  const dict = getDictionary(locale);
  const t = dict.outputs;
  const base = `/api/v1/projects/${projectId}`;
  const [project, output, versions] = await Promise.all([
    load<Project>(base),
    load<Output>(`${base}/outputs/${outputId}`),
    load<OutputVersion[]>(`${base}/outputs/${outputId}/versions`),
  ]);
  if (project === null || output === null) notFound();
  const hidden = (
    <>
      <input type="hidden" name="project_id" value={projectId} />
      <input type="hidden" name="output_id" value={outputId} />
    </>
  );

  return (
    <AppShell locale={locale} active="outputs">
      <div className="space-y-6">
        <ProjectHeader project={project} dict={dict} locale={locale} active="outputs" />
        <div className="flex flex-wrap items-center gap-2">
          <h2 dir="auto" className="text-xl font-semibold">{output.title}</h2>
          <Badge>{output.output_type}</Badge>
          <Badge>{output.mode}</Badge>
          <span data-testid="output-status">
            <Badge tone={output.latest.status === "APPROVED" ? "good" : "neutral"}>
              v{output.current_version} {output.latest.status}
            </Badge>
          </span>
        </div>
        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <Card title={`${t.version} ${output.latest.version_number}`} testId="output-version">
            <OutputBlocks output={output} blocks={output.latest.blocks} t={t} />
          </Card>
          <div className="space-y-6">
            <Card title={t.approve} testId="approve-output">
              {output.latest.status === "DRAFT" ? (
                <ActionForm action={approveOutputVersion} submitLabel={t.approve} pendingLabel={t.saving}>
                  {hidden}
                  <input type="hidden" name="version_id" value={output.latest.id} />
                  <p className="text-xs text-[var(--color-muted)]">{t.approveExplainer}</p>
                  <Field label={t.reason}>
                    <TextInput name="reason" />
                  </Field>
                </ActionForm>
              ) : (
                <Badge tone="good">{output.latest.status}</Badge>
              )}
              <ActionForm action={recomposeOutput} submitLabel={t.recompose} pendingLabel={t.saving}>
                {hidden}
              </ActionForm>
              <ActionForm action={setOutputMode} submitLabel={t.setMode} pendingLabel={t.saving}>
                {hidden}
                <Field label={t.mode}>
                  <Select name="mode" defaultValue={output.mode}>
                    {OutputModeValues.map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </Select>
                </Field>
              </ActionForm>
            </Card>
            <Card title={t.versions} testId="output-versions">
              <ol className="space-y-1 text-sm">
                {(versions ?? []).map((v) => (
                  <li key={v.id}>
                    v{v.version_number} <Badge tone={v.status === "APPROVED" ? "good" : "neutral"}>{v.status}</Badge>{" "}
                    <span dir="auto">{v.change_reason}</span>
                  </li>
                ))}
              </ol>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
