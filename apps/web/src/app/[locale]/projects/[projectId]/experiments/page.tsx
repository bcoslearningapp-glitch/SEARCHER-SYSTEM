import Link from "next/link";

import { assessDesignHypothesis, createDesignHypothesis, createExperiment } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, Select, TextArea, TextInput } from "@/components/fields";
import { ProjectHeader } from "@/components/ProjectHeader";
import { HypothesisEpistemicStateValues } from "@/lib/contracts/enums";
import { getDictionary } from "@/lib/i18n";
import { load, loadEntity } from "@/lib/load";
import { resolveProjectParams, type ProjectParams } from "@/lib/locale-params";
import type { DesignConcept, DesignHypothesis, Experiment, Project } from "@/lib/types";

export const dynamic = "force-dynamic";

const TEXT_FIELDS = ["intervention", "target_population", "context", "mechanism", "expected_outcome", "measurement_plan"] as const;
const LIST_FIELDS = ["failure_conditions", "side_effects", "stop_conditions"] as const;
const PROTOCOL_FIELDS = ["method", "sample", "duration", "data_collected", "analysis_plan", "success_criteria"] as const;

/** Design hypotheses and experiments (PRD §33-34). */
export default async function ExperimentsPage(props: ProjectParams) {
  const { locale, projectId } = await resolveProjectParams(props);
  const dict = getDictionary(locale);
  const x = dict.experiments;
  const base = `/api/v1/projects/${projectId}`;
  const project = await loadEntity<Project>(base);
  const [concepts, hypotheses, experiments] = await Promise.all([
    load<DesignConcept[]>(`${base}/design/concepts`),
    load<DesignHypothesis[]>(`${base}/design-hypotheses`),
    load<Experiment[]>(`${base}/experiments`),
  ]);
  const openConcepts = (concepts ?? []).filter((c) => !["REJECTED", "WITHDRAWN"].includes(c.status));
  const hidden = <input type="hidden" name="project_id" value={projectId} />;

  return (
    <AppShell locale={locale} active="lab">
      <div className="space-y-6">
        <ProjectHeader project={project} dict={dict} locale={locale} active="experiments" />
        <div className="grid gap-6 lg:grid-cols-2">
          <Card title={x.designHypotheses} testId="design-hypotheses">
            {hypotheses?.length ? (
              <ul className="space-y-3 text-sm">
                {hypotheses.map((h) => (
                  <li key={h.id} className="space-y-1 rounded-md border border-[var(--color-border)] p-2" data-testid="design-hypothesis-row">
                    <p dir="auto" className="font-medium">{h.content.intervention}</p>
                    <p dir="auto">
                      {x.content.expected_outcome}: {h.content.expected_outcome}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <Badge tone={h.epistemic_state === "SUPPORTED" ? "good" : "neutral"}>{h.epistemic_state}</Badge>
                      {h.affects_people ? <Badge tone="warn">{x.affectsPeople}</Badge> : null}
                      {h.provenance.kind === "AI_GENERATED" ? <Badge tone="warn">AI</Badge> : null}
                    </div>
                    <details>
                      <summary className="cursor-pointer text-xs">{x.assess}</summary>
                      <ActionForm action={assessDesignHypothesis} submitLabel={x.assess} pendingLabel={x.saving}>
                        {hidden}
                        <input type="hidden" name="design_hypothesis_id" value={h.id} />
                        <p className="text-xs text-[var(--color-muted)]">{x.assessHint}</p>
                        <Select name="epistemic_state" defaultValue={h.epistemic_state} aria-label={x.assess}>
                          {HypothesisEpistemicStateValues.map((v) => (
                            <option key={v}>{v}</option>
                          ))}
                        </Select>
                        <Field label={x.reason}>
                          <TextInput name="reason" required />
                        </Field>
                      </ActionForm>
                    </details>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{x.noDesignHypotheses}</Empty>
            )}
            {openConcepts.length ? (
              <ActionForm action={createDesignHypothesis} submitLabel={x.create} pendingLabel={x.saving} testId="new-design-hypothesis">
                {hidden}
                <p className="font-medium">{x.newDesignHypothesis}</p>
                <Field label={x.concept}>
                  <Select name="concept_id" required>
                    {openConcepts.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.title} ({c.status})
                      </option>
                    ))}
                  </Select>
                </Field>
                {TEXT_FIELDS.map((f) => (
                  <Field key={f} label={x.content[f]}>
                    <TextInput name={f} required />
                  </Field>
                ))}
                {LIST_FIELDS.map((f) => (
                  <Field key={f} label={x.content[f]} hint={x.listHint}>
                    <TextArea name={f} rows={2} />
                  </Field>
                ))}
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" name="affects_people" />
                  {x.affectsPeople}
                </label>
                <p className="text-xs text-[var(--color-muted)]">{x.affectsPeopleHint}</p>
              </ActionForm>
            ) : null}
          </Card>

          <Card title={x.experiments} testId="experiments">
            {experiments?.length ? (
              <ul className="space-y-2 text-sm">
                {experiments.map((e) => (
                  <li key={e.id} className="flex flex-wrap items-center gap-2" data-testid="experiment-row">
                    <Link href={`/${locale}/projects/${projectId}/experiments/${e.id}`} className="font-medium underline" dir="auto">
                      {e.title}
                    </Link>
                    <Badge tone={e.state === "INVALIDATED" || e.state === "ABORTED" ? "warn" : e.state === "CLOSED" ? "good" : "neutral"}>
                      {e.state}
                    </Badge>
                    {e.affects_people ? <Badge tone="warn">{x.affectsPeople}</Badge> : null}
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{x.noExperiments}</Empty>
            )}
            {hypotheses?.length ? (
              <ActionForm action={createExperiment} submitLabel={x.create} pendingLabel={x.saving} testId="new-experiment">
                {hidden}
                <p className="font-medium">{x.newExperiment}</p>
                <Field label={x.designHypothesis}>
                  <Select name="design_hypothesis_id" required>
                    {hypotheses.map((h) => (
                      <option key={h.id} value={h.id}>
                        {h.content.intervention}
                      </option>
                    ))}
                  </Select>
                </Field>
                <Field label={x.title}>
                  <TextInput name="title" required />
                </Field>
                {PROTOCOL_FIELDS.map((f) => (
                  <Field key={f} label={x.protocolFields[f]}>
                    <TextInput name={f} />
                  </Field>
                ))}
              </ActionForm>
            ) : null}
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
