import { notFound } from "next/navigation";

import {
  confirmDesignRequirement,
  createDesignConcept,
  createDesignRequirement,
  evaluateDesignReadiness,
  rejectDesignConcept,
  selectDesignConcept,
  setDesignCoverage,
  withdrawDesignRequirement,
} from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, Select, TextArea, TextInput } from "@/components/fields";
import { ProjectHeader } from "@/components/ProjectHeader";
import {
  DesignOriginValues,
  DesignRequirementBasisValues,
  RejectionGroundValues,
  RequirementCoverageValues,
  RequirementPriorityValues,
} from "@/lib/contracts/enums";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveProjectParams, type ProjectParams } from "@/lib/locale-params";
import type { DesignConcept, DesignRequirement, GateEvaluation, Hypothesis, Mechanism, Project } from "@/lib/types";

export const dynamic = "force-dynamic";

const OPEN = new Set(["PROPOSED", "UNDER_REVIEW"]);
// AI-originated concepts are recorded by the AI with its provenance, never typed in by a researcher.
const HUMAN_ORIGINS = DesignOriginValues.filter((o) => o !== "AI");

function gateTone(result: string): "good" | "warn" | "neutral" {
  if (result === "PASS") return "good";
  return result === "PASS_WITH_RESERVATIONS" ? "neutral" : "warn";
}

/** Design synthesis (PRD §32): requirements before solutions, concepts with origins, human selection. */
export default async function DesignPage(props: ProjectParams) {
  const { locale, projectId } = await resolveProjectParams(props);
  const dict = getDictionary(locale);
  const d = dict.design;
  const base = `/api/v1/projects/${projectId}`;
  const project = await load<Project>(base);
  if (project === null) notFound();
  const [requirements, concepts, hypotheses, mechanisms] = await Promise.all([
    load<DesignRequirement[]>(`${base}/design/requirements`),
    load<DesignConcept[]>(`${base}/design/concepts`),
    load<Hypothesis[]>(`${base}/hypotheses`),
    load<Mechanism[]>(`${base}/mechanisms`),
  ]);
  const gates = await Promise.all(
    (concepts ?? []).map((c) => load<GateEvaluation | null>(`${base}/design/concepts/${c.id}/readiness`)),
  );
  const current = requirements ?? [];
  const mechanismName = new Map((mechanisms ?? []).map((m) => [m.id, m.name]));
  const hidden = <input type="hidden" name="project_id" value={projectId} />;

  return (
    <AppShell locale={locale} active="lab">
      <div className="space-y-6">
        <ProjectHeader project={project} dict={dict} locale={locale} active="design" />
        <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
          <Card title={d.requirements} testId="design-requirements">
            <p className="text-sm text-[var(--color-muted)]">{d.requirementsExplainer}</p>
            {current.length ? (
              <ul className="space-y-3 text-sm">
                {current.map((req) => (
                  <li key={req.id} className="space-y-1 rounded-md border border-[var(--color-border)] p-2" data-testid="requirement-row">
                    <p dir="auto" className="font-medium">{req.statement}</p>
                    <div className="flex flex-wrap gap-2">
                      <Badge tone={req.priority === "MUST" ? "warn" : "neutral"}>{req.priority}</Badge>
                      <Badge tone={req.status === "ACTIVE" ? "good" : "neutral"}>{req.status}</Badge>
                      <Badge>
                        {d.version} {req.version_number}
                      </Badge>
                      {req.traces.map((t, i) => (
                        <Badge key={i}>{t.basis}</Badge>
                      ))}
                    </div>
                    {req.status === "PROPOSED" ? (
                      <div className="space-y-1">
                        <p className="text-xs text-amber-700 dark:text-amber-300">{d.proposedByAI}</p>
                        <ActionForm action={confirmDesignRequirement} submitLabel={d.confirm} pendingLabel={d.saving}>
                          {hidden}
                          <input type="hidden" name="requirement_id" value={req.id} />
                        </ActionForm>
                      </div>
                    ) : null}
                    <details>
                      <summary className="cursor-pointer text-xs">{d.withdraw}</summary>
                      <ActionForm action={withdrawDesignRequirement} submitLabel={d.withdraw} pendingLabel={d.saving}>
                        {hidden}
                        <input type="hidden" name="requirement_id" value={req.id} />
                        <Field label={d.withdrawReason}>
                          <TextInput name="reason" required />
                        </Field>
                      </ActionForm>
                    </details>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{d.noRequirements}</Empty>
            )}
            <ActionForm action={createDesignRequirement} submitLabel={d.addRequirement} pendingLabel={d.saving} testId="new-requirement">
              {hidden}
              <Field label={d.statement}>
                <TextArea name="statement" rows={2} required />
              </Field>
              <Field label={d.priority}>
                <Select name="priority" defaultValue="MUST">
                  {RequirementPriorityValues.map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </Select>
              </Field>
              <Field label={d.basis}>
                <Select name="basis" defaultValue="PURPOSE">
                  {DesignRequirementBasisValues.map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </Select>
              </Field>
              <Field label={d.traceNote}>
                <TextInput name="note" />
              </Field>
            </ActionForm>
          </Card>

          <Card title={d.concepts} testId="design-concepts">
            <p className="text-sm text-[var(--color-muted)]">{d.conceptsExplainer}</p>
            {concepts?.length ? (
              <ul className="space-y-4 text-sm">
                {concepts.map((concept, index) => {
                  const gate = gates[index];
                  const open = OPEN.has(concept.status);
                  return (
                    <li key={concept.id} className="space-y-2 rounded-md border border-[var(--color-border)] p-3" data-testid="concept-row">
                      <div className="flex flex-wrap items-center gap-2">
                        <span dir="auto" className="font-medium">{concept.title}</span>
                        <Badge tone={concept.status === "SELECTED" ? "good" : concept.status === "REJECTED" ? "warn" : "neutral"}>
                          {concept.status}
                        </Badge>
                        <Badge tone={concept.origin === "AI" ? "warn" : "neutral"}>{concept.origin}</Badge>
                      </div>
                      <p dir="auto">{concept.description}</p>
                      {concept.mechanism_ids.length ? (
                        <p className="text-xs">
                          {d.mechanisms}: {concept.mechanism_ids.map((id) => mechanismName.get(id) ?? id).join(", ")}
                        </p>
                      ) : null}
                      {concept.rejection ? (
                        <p className="text-xs" data-testid="concept-rejection">
                          {d.rejectedBecause} ({concept.rejection.ground}): <span dir="auto">{concept.rejection.reason}</span>
                          {concept.rejection.reusable_mechanism_ids.length
                            ? ` — ${d.reusableMechanisms}: ${concept.rejection.reusable_mechanism_ids.map((id) => mechanismName.get(id) ?? id).join(", ")}`
                            : ""}
                        </p>
                      ) : null}

                      <div>
                        <p className="font-medium">{d.coverage}</p>
                        <ul className="space-y-1">
                          {current
                            .filter((r) => r.status === "ACTIVE")
                            .map((req) => {
                              const covered = concept.coverage.find((c) => c.requirement_series_id === req.series_id);
                              return (
                                <li key={req.id} className="flex flex-wrap items-center gap-2" data-testid="coverage-row">
                                  <span dir="auto" className="min-w-0 flex-1 truncate">
                                    {req.statement}
                                  </span>
                                  {covered ? <Badge tone={covered.coverage === "MEETS" ? "good" : "warn"}>{covered.coverage}</Badge> : null}
                                  {covered?.stale ? <Badge tone="warn">{d.stale}</Badge> : null}
                                  {open ? (
                                    <ActionForm action={setDesignCoverage} submitLabel={d.recordCoverage} pendingLabel={d.saving} className="flex items-center gap-2">
                                      {hidden}
                                      <input type="hidden" name="concept_id" value={concept.id} />
                                      <input type="hidden" name="requirement_id" value={req.id} />
                                      <Select name="coverage" defaultValue={covered?.coverage ?? "MEETS"} aria-label={d.coverage}>
                                        {RequirementCoverageValues.map((v) => (
                                          <option key={v}>{v}</option>
                                        ))}
                                      </Select>
                                    </ActionForm>
                                  ) : null}
                                </li>
                              );
                            })}
                        </ul>
                      </div>

                      <div className="space-y-1" data-testid="readiness">
                        <p className="font-medium">{d.readiness}</p>
                        {gate ? (
                          <>
                            <Badge tone={gateTone(gate.result)}>{gate.result}</Badge>
                            <ul className="list-disc ps-5 text-xs">
                              {gate.findings.map((f) => (
                                <li key={f.code + f.message}>
                                  {f.severity}: {f.message}
                                </li>
                              ))}
                            </ul>
                          </>
                        ) : (
                          <Empty>{d.notEvaluated}</Empty>
                        )}
                        <ActionForm action={evaluateDesignReadiness} submitLabel={d.evaluate} pendingLabel={d.saving}>
                          {hidden}
                          <input type="hidden" name="concept_id" value={concept.id} />
                        </ActionForm>
                      </div>

                      {open ? (
                        <div className="grid gap-3 md:grid-cols-2">
                          <ActionForm action={selectDesignConcept} submitLabel={d.select} pendingLabel={d.saving} testId="select-concept">
                            {hidden}
                            <input type="hidden" name="concept_id" value={concept.id} />
                            <p className="text-xs text-[var(--color-muted)]">{d.selectExplainer}</p>
                            <Field label={d.reason}>
                              <TextInput name="reason" />
                            </Field>
                            <label className="flex items-center gap-2 text-xs">
                              <input type="checkbox" name="acknowledge_reservations" />
                              {d.acknowledge}
                            </label>
                          </ActionForm>
                          <ActionForm action={rejectDesignConcept} submitLabel={d.reject} pendingLabel={d.saving} testId="reject-concept">
                            {hidden}
                            <input type="hidden" name="concept_id" value={concept.id} />
                            <Field label={d.ground}>
                              <Select name="ground" defaultValue="REFERENCE">
                                {RejectionGroundValues.map((v) => (
                                  <option key={v}>{v}</option>
                                ))}
                              </Select>
                            </Field>
                            <Field label={d.reason}>
                              <TextInput name="reason" required />
                            </Field>
                            {concept.mechanism_ids.length ? (
                              <fieldset className="text-xs">
                                <legend>{d.reusableMechanisms}</legend>
                                {concept.mechanism_ids.map((id) => (
                                  <label key={id} className="flex items-center gap-2">
                                    <input type="checkbox" name="reusable_mechanism_ids" value={id} defaultChecked />
                                    {mechanismName.get(id) ?? id}
                                  </label>
                                ))}
                              </fieldset>
                            ) : null}
                          </ActionForm>
                        </div>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            ) : (
              <Empty>{d.noConcepts}</Empty>
            )}

            <ActionForm action={createDesignConcept} submitLabel={d.addConcept} pendingLabel={d.saving} testId="new-concept">
              {hidden}
              <Field label={d.title}>
                <TextInput name="title" required />
              </Field>
              <Field label={d.description}>
                <TextArea name="description" rows={3} required />
              </Field>
              <Field label={d.origin}>
                <Select name="origin" defaultValue="RESEARCHER">
                  {HUMAN_ORIGINS.map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </Select>
              </Field>
              <Field label={d.originReference}>
                <TextInput name="origin_reference" />
              </Field>
              {hypotheses?.length ? (
                <fieldset className="text-sm">
                  <legend className="font-medium">{d.hypotheses}</legend>
                  {hypotheses.map((h) => (
                    <label key={h.id} className="flex items-center gap-2">
                      <input type="checkbox" name="hypothesis_ids" value={h.id} />
                      <span dir="auto">{h.content.statement}</span> <Badge>{h.lifecycle_state}</Badge>
                    </label>
                  ))}
                </fieldset>
              ) : null}
              {mechanisms?.length ? (
                <fieldset className="text-sm">
                  <legend className="font-medium">{d.mechanisms}</legend>
                  {mechanisms.map((m) => (
                    <label key={m.id} className="flex items-center gap-2">
                      <input type="checkbox" name="mechanism_ids" value={m.id} />
                      <span dir="auto">{m.name}</span>
                    </label>
                  ))}
                </fieldset>
              ) : null}
              {concepts?.length ? (
                <fieldset className="text-sm">
                  <legend className="font-medium">{d.derivedFrom}</legend>
                  {concepts.map((c) => (
                    <label key={c.id} className="flex items-center gap-2">
                      <input type="checkbox" name="derived_from_concept_ids" value={c.id} />
                      <span dir="auto">{c.title}</span> <Badge>{c.status}</Badge>
                    </label>
                  ))}
                </fieldset>
              ) : null}
            </ActionForm>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
