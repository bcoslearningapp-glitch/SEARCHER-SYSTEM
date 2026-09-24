import { notFound } from "next/navigation";

import { changeKnowledgeStanding, createKnowledge, promoteKnowledge, reuseKnowledge } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, Select, TextArea, TextInput } from "@/components/fields";
import { ProjectHeader } from "@/components/ProjectHeader";
import {
  EvidenceStrengthValues,
  KnowledgeLifecycleStageValues,
  TemporalProfileValues,
  TransferabilityStateValues,
} from "@/lib/contracts/enums";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveProjectParams, type ProjectParams } from "@/lib/locale-params";
import type { Experiment, ExperimentRecord, KnowledgeItem, KnowledgeReuse, Project } from "@/lib/types";

export const dynamic = "force-dynamic";

const STANDING_ACTIONS = ["CONTEST", "SUSPEND", "REINSTATE", "REVALIDATE", "DOWNGRADE"] as const;

/** Local knowledge lifecycle, temporal validity and labelled reuse (PRD §28-29, §35). */
export default async function KnowledgePage(props: ProjectParams) {
  const { locale, projectId } = await resolveProjectParams(props);
  const dict = getDictionary(locale);
  const k = dict.knowledge;
  const base = `/api/v1/projects/${projectId}`;
  const project = await load<Project>(base);
  if (project === null) notFound();
  const [items, reused, experiments, projects] = await Promise.all([
    load<KnowledgeItem[]>(`${base}/knowledge`),
    load<KnowledgeReuse[]>(`${base}/reused-knowledge`),
    load<Experiment[]>(`${base}/experiments`),
    load<Project[]>("/api/v1/projects"),
  ]);
  const records = await Promise.all(
    (experiments ?? []).map(async (e) => ({ experiment: e, record: await load<ExperimentRecord>(`${base}/experiments/${e.id}/record`) })),
  );
  const bases = records.flatMap(({ experiment, record }) => [
    ...(record?.interpretations ?? []).map((i) => ({ value: `ExperimentInterpretation:${i.id}`, label: `${experiment.title} — ${i.outcome}: ${i.statement}` })),
    ...(record?.learning_reviews ?? []).map((r) => ({ value: `LearningReview:${r.id}`, label: `${experiment.title} — ${r.learned}` })),
  ]);
  const others = (projects ?? []).filter((p) => p.id !== projectId);
  const hidden = <input type="hidden" name="project_id" value={projectId} />;

  return (
    <AppShell locale={locale} active="lab">
      <div className="space-y-6">
        <ProjectHeader project={project} dict={dict} locale={locale} active="knowledge" />
        <p className="text-sm text-[var(--color-muted)]">{k.explainer}</p>
        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <Card title={k.items} testId="knowledge-items">
            {items?.length ? (
              <ul className="space-y-4 text-sm">
                {items.map((item) => {
                  const index = KnowledgeLifecycleStageValues.indexOf(item.stage);
                  const next = KnowledgeLifecycleStageValues[index + 1];
                  const lower = KnowledgeLifecycleStageValues.slice(0, index);
                  const itemHidden = (
                    <>
                      {hidden}
                      <input type="hidden" name="knowledge_id" value={item.id} />
                    </>
                  );
                  return (
                    <li key={item.id} className="space-y-2 rounded-md border border-[var(--color-border)] p-3" data-testid="knowledge-row">
                      <p dir="auto" className="font-medium">{item.statement}</p>
                      <div className="flex flex-wrap gap-2">
                        <span data-testid="knowledge-stage">
                          <Badge tone={item.stage === "OPERATING_RULE" ? "good" : "neutral"}>{item.stage}</Badge>
                        </span>
                        <Badge tone={item.effective_status === "ACTIVE" ? "good" : "warn"}>{item.effective_status}</Badge>
                        <Badge>{item.confidence}</Badge>
                        <Badge>{item.temporal_profile}</Badge>
                        {item.revalidation_due ? <Badge tone="warn">{k.revalidationDue}</Badge> : null}
                        {item.provenance.kind === "AI_GENERATED" ? <Badge tone="warn">AI</Badge> : null}
                      </div>
                      {item.scope ? (
                        <p dir="auto" className="text-xs">
                          {k.scope}: {item.scope}
                        </p>
                      ) : null}
                      {item.contexts.length ? (
                        <p dir="auto" className="text-xs">
                          {k.contexts}: {item.contexts.join(", ")}
                        </p>
                      ) : null}
                      <div className="grid gap-3 md:grid-cols-3">
                        {next ? (
                          <ActionForm action={promoteKnowledge} submitLabel={k.promote} pendingLabel={k.saving} testId="promote-form">
                            {itemHidden}
                            <input type="hidden" name="target" value={next} />
                            <p className="text-xs">
                              {k.promoteTo} <strong>{next}</strong>
                            </p>
                            <p className="text-xs text-[var(--color-muted)]">{k.promoteExplainer}</p>
                            <Field label={k.reason}>
                              <TextInput name="reason" />
                            </Field>
                            <label className="flex items-center gap-2 text-xs">
                              <input type="checkbox" name="acknowledge_reservations" />
                              {k.acknowledge}
                            </label>
                          </ActionForm>
                        ) : null}
                        <ActionForm action={changeKnowledgeStanding} submitLabel={k.apply} pendingLabel={k.saving}>
                          {itemHidden}
                          <p className="text-xs font-medium">{k.standing}</p>
                          <Field label={k.action}>
                            <Select name="action">
                              {STANDING_ACTIONS.filter((a) => a !== "DOWNGRADE" || lower.length).map((a) => (
                                <option key={a}>{a}</option>
                              ))}
                            </Select>
                          </Field>
                          {lower.length ? (
                            <Field label={k.targetStage}>
                              <Select name="target_stage" defaultValue="">
                                <option value="">—</option>
                                {lower.map((s) => (
                                  <option key={s}>{s}</option>
                                ))}
                              </Select>
                            </Field>
                          ) : null}
                          <Field label={k.reason}>
                            <TextInput name="reason" required />
                          </Field>
                        </ActionForm>
                        {others.length ? (
                          <ActionForm action={reuseKnowledge} submitLabel={k.reuse} pendingLabel={k.saving} testId="reuse-form">
                            {itemHidden}
                            <p className="text-xs text-[var(--color-muted)]">{k.reuseExplainer}</p>
                            <Field label={k.targetProject}>
                              <Select name="target_project_id">
                                {others.map((p) => (
                                  <option key={p.id} value={p.id}>
                                    {p.title}
                                  </option>
                                ))}
                              </Select>
                            </Field>
                            <Field label={k.transferability}>
                              <Select name="transferability" defaultValue="PARTIALLY_TRANSFERABLE">
                                {TransferabilityStateValues.map((v) => (
                                  <option key={v}>{v}</option>
                                ))}
                              </Select>
                            </Field>
                            <Field label={k.rationale}>
                              <TextInput name="rationale" required />
                            </Field>
                            <Field label={k.differences}>
                              <TextInput name="differences" />
                            </Field>
                          </ActionForm>
                        ) : null}
                      </div>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <Empty>{k.noItems}</Empty>
            )}
          </Card>

          <div className="space-y-6">
            <Card title={k.newItem} testId="new-knowledge">
              {bases.length ? (
                <ActionForm action={createKnowledge} submitLabel={k.create} pendingLabel={k.saving}>
                  {hidden}
                  <Field label={k.statement}>
                    <TextArea name="statement" rows={2} required />
                  </Field>
                  <fieldset className="text-sm">
                    <legend className="font-medium">{k.basis}</legend>
                    <p className="text-xs text-[var(--color-muted)]">{k.basisHint}</p>
                    {bases.map((b) => (
                      <label key={b.value} className="flex items-center gap-2">
                        <input type="checkbox" name="basis" value={b.value} />
                        <span dir="auto">{b.label}</span>
                      </label>
                    ))}
                  </fieldset>
                  <Field label={k.scope}>
                    <TextInput name="scope" />
                  </Field>
                  <Field label={k.contexts} hint={k.listHint}>
                    <TextArea name="contexts" rows={2} />
                  </Field>
                  <Field label={k.confidence}>
                    <Select name="confidence" defaultValue="PROMISING">
                      {EvidenceStrengthValues.map((v) => (
                        <option key={v}>{v}</option>
                      ))}
                    </Select>
                  </Field>
                  <Field label={k.temporalProfile}>
                    <Select name="temporal_profile" defaultValue="SLOW_CHANGING">
                      {TemporalProfileValues.map((v) => (
                        <option key={v}>{v}</option>
                      ))}
                    </Select>
                  </Field>
                  <Field label={k.interval}>
                    <TextInput name="revalidation_interval_days" type="number" min={1} />
                  </Field>
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" name="contrary_evidence_searched" />
                    {k.contrarySearched}
                  </label>
                </ActionForm>
              ) : (
                <Empty>{k.noItems}</Empty>
              )}
            </Card>

            <Card title={k.reusedHere} testId="reused-knowledge">
              {reused?.length ? (
                <ul className="space-y-2 text-sm">
                  {reused.map((r) => (
                    <li key={r.id} className="space-y-1">
                      <p dir="auto">{r.statement}</p>
                      <div className="flex flex-wrap gap-2">
                        <Badge tone={r.transferability === "DIRECTLY_RELEVANT" ? "good" : "warn"}>{r.transferability}</Badge>
                        <Badge tone="warn">{k.notEvidence}</Badge>
                        <Badge>{r.effective_status}</Badge>
                      </div>
                      <p className="text-xs">{r.label}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <Empty>{k.noReused}</Empty>
              )}
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
