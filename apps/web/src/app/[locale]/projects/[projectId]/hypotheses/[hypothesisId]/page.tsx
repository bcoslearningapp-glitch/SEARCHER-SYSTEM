import { notFound } from "next/navigation";

import {
  addReviewEntry,
  assessEvidence,
  assessHypothesis,
  createReview,
  judgeReview,
  proposeEvidence,
  recordTrack,
  reviseHypothesis,
  transitionHypothesis,
} from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, Select, TextArea, TextInput } from "@/components/fields";
import { ProjectHeader } from "@/components/ProjectHeader";
import {
  DirectnessValues,
  EvidenceRoleValues,
  EvidenceStrengthValues,
  HypothesisEpistemicStateValues,
  HypothesisLifecycleStateValues,
  ReferenceAnalyticalCategoryValues,
  ReferenceJudgmentStateValues,
  ReservationTypeValues,
  ResearchOutcomeKindValues,
  ResearchTrackValues,
} from "@/lib/contracts/enums";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveLocale } from "@/lib/locale-params";
import { projectExcerpts } from "@/lib/project-data";
import type { EvidenceMap, Hypothesis, HypothesisVersion, Project, ReferenceReview, Standing } from "@/lib/types";

export const dynamic = "force-dynamic";

type Props = { params: Promise<{ locale: string; projectId: string; hypothesisId: string }> };

const HUMAN_LAYERS = ["SOURCE_TEXT", "APPROVED_INTERPRETATION", "SYSTEM_SYNTHESIS", "PRACTICAL_JUDGMENT"];

export default async function HypothesisPage(props: Props) {
  const { projectId, hypothesisId } = await props.params;
  const locale = await resolveLocale({ params: props.params });
  if (!/^[0-9a-f-]{36}$/i.test(projectId) || !/^[0-9a-f-]{36}$/i.test(hypothesisId)) notFound();
  const dict = getDictionary(locale);
  const lab = dict.lab;
  const base = `/api/v1/projects/${projectId}`;
  const [project, hypothesis] = await Promise.all([
    load<Project>(base),
    load<Hypothesis>(`${base}/hypotheses/${hypothesisId}`),
  ]);
  if (project === null || hypothesis === null) notFound();
  const [versions, map, reviews, standing, excerpts] = await Promise.all([
    load<HypothesisVersion[]>(`${base}/hypotheses/${hypothesisId}/versions`),
    load<EvidenceMap>(`${base}/evidence-map/HYPOTHESIS/${hypothesisId}`),
    load<ReferenceReview[]>(`${base}/reference-reviews`),
    load<Standing>(`${base}/standing/HYPOTHESIS/${hypothesisId}`),
    projectExcerpts(projectId),
  ]);
  const ids = (
    <>
      <input type="hidden" name="project_id" value={projectId} />
      <input type="hidden" name="hypothesis_id" value={hypothesisId} />
    </>
  );
  const target = (
    <>
      <input type="hidden" name="project_id" value={projectId} />
      <input type="hidden" name="target_type" value="HYPOTHESIS" />
      <input type="hidden" name="target_id" value={hypothesisId} />
    </>
  );
  const index = HypothesisLifecycleStateValues.indexOf(hypothesis.lifecycle_state as (typeof HypothesisLifecycleStateValues)[number]);
  const stages = HypothesisLifecycleStateValues.filter((_, i) => i === index + 1 || i < index);
  const hypothesisReviews = (reviews ?? []).filter((r) => r.target_type === "HYPOTHESIS" && r.target_id === hypothesisId);
  const c = hypothesis.content;

  return (
    <AppShell locale={locale} active="lab">
      <div className="space-y-6">
        <ProjectHeader project={project} dict={dict} locale={locale} active="lab" />
        <header className="space-y-2">
          <h2 dir="auto" className="text-xl font-semibold">
            {c.statement}
          </h2>
          <p className="flex flex-wrap gap-2 text-sm">
            <span data-testid="hypothesis-stage">
              <Badge>{hypothesis.lifecycle_state}</Badge>
            </span>
            <span data-testid="hypothesis-assessment">
              <Badge tone={["CONTESTED", "WEAKENED", "REFUTED"].includes(hypothesis.epistemic_state) ? "warn" : "neutral"}>
                {hypothesis.epistemic_state}
              </Badge>
            </span>
            <span>
              {lab.suggested}: <Badge>{hypothesis.suggested_epistemic_state}</Badge>
            </span>
            <span data-testid="counter-evidence">
              {lab.counterEvidence}:{" "}
              <Badge tone={hypothesis.counter_evidence_search_complete ? "good" : "warn"}>
                {hypothesis.counter_evidence_search_complete ? lab.complete : lab.incomplete}
              </Badge>
            </span>
          </p>
        </header>

        <div className="grid gap-6 lg:grid-cols-[3fr_2fr]">
          <div className="space-y-6">
            <Card title={lab.evidenceMap} testId="evidence-map">
              {map ? (
                <div className="space-y-3 text-sm">
                  <p>
                    {lab.independentOrigins}: <strong data-testid="support-origins">{map.support_origins}</strong> SUPPORTS /{" "}
                    <strong>{map.contra_origins}</strong> CONTRADICTS
                    {map.meaningful_conflict ? <span className="ms-2"><Badge tone="warn">{lab.meaningfulConflict}</Badge></span> : null}
                  </p>
                  {EvidenceRoleValues.map((role) =>
                    (map.by_role[role] ?? []).length ? (
                      <div key={role}>
                        <h3 className="font-medium">{role}</h3>
                        <ul className="list-disc space-y-1 ps-5">
                          {(map.by_role[role] ?? []).map((e) => (
                            <li key={e.id} dir="auto" data-testid="accepted-evidence">
                              {e.finding} <Badge>{e.assessment?.strength ?? ""}</Badge>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : null,
                  )}
                  {map.candidates.length ? (
                    <div className="space-y-2">
                      <h3 className="font-medium">{lab.candidates}</h3>
                      {map.candidates.map((e) => (
                        <div key={e.id} className="rounded-md border border-[var(--color-border)] p-2" data-testid="evidence-candidate">
                          <p dir="auto">
                            <Badge>{e.role}</Badge> {e.finding} {e.provenance.kind === "AI_GENERATED" ? <Badge tone="warn">AI</Badge> : null}
                          </p>
                          <ActionForm action={assessEvidence} submitLabel={lab.save} pendingLabel={lab.saving} className="mt-2 flex flex-wrap items-end gap-2">
                            <input type="hidden" name="project_id" value={projectId} />
                            <input type="hidden" name="evidence_id" value={e.id} />
                            <Select name="decision" aria-label={lab.accept}>
                              <option value="ACCEPT">{lab.accept}</option>
                              <option value="REJECT">{lab.reject}</option>
                            </Select>
                            <Select name="strength" aria-label={lab.strength} defaultValue="PROMISING">
                              {EvidenceStrengthValues.map((v) => (
                                <option key={v}>{v}</option>
                              ))}
                            </Select>
                          </ActionForm>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : (
                <Empty>{dict.ui.loadError}</Empty>
              )}
              {excerpts.length ? (
                <ActionForm action={proposeEvidence} submitLabel={lab.addEvidence} pendingLabel={lab.saving} testId="add-evidence">
                  {target}
                  <Field label={lab.excerpt}>
                    <Select name="excerpt_id">
                      {excerpts.map((x) => (
                        <option key={x.id} value={x.id}>
                          {x.label}
                        </option>
                      ))}
                    </Select>
                  </Field>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Field label={lab.role}>
                      <Select name="role">
                        {EvidenceRoleValues.map((v) => (
                          <option key={v}>{v}</option>
                        ))}
                      </Select>
                    </Field>
                    <Field label={lab.track}>
                      <Select name="track" defaultValue="SUPPORT">
                        {ResearchTrackValues.map((v) => (
                          <option key={v}>{v}</option>
                        ))}
                      </Select>
                    </Field>
                  </div>
                  <Field label={lab.finding}>
                    <TextArea name="finding" required rows={2} />
                  </Field>
                </ActionForm>
              ) : (
                <Empty>{lab.noExcerpts}</Empty>
              )}
            </Card>

            <Card title={lab.searches} testId="searches">
              <ul className="space-y-1 text-sm">
                {(map?.tracks ?? []).map((t) => (
                  <li key={t.track} data-testid={`track-${t.track}`}>
                    {t.track}:{" "}
                    <Badge tone={t.searched ? "good" : t.execution_failed ? "warn" : "neutral"}>
                      {t.searched ? lab.searched : t.execution_failed ? lab.failed : lab.notSearched}
                    </Badge>
                  </li>
                ))}
              </ul>
              <ActionForm action={recordTrack} submitLabel={lab.recordSearch} pendingLabel={lab.saving} testId="record-search">
                {target}
                <div className="grid gap-3 sm:grid-cols-2">
                  <Field label={lab.track}>
                    <Select name="track" defaultValue="CHALLENGE">
                      {ResearchTrackValues.map((v) => (
                        <option key={v}>{v}</option>
                      ))}
                    </Select>
                  </Field>
                  <Field label={lab.outcome}>
                    <Select name="outcome" defaultValue="NO_RELEVANT_EVIDENCE_FOUND">
                      {ResearchOutcomeKindValues.map((v) => (
                        <option key={v}>{v}</option>
                      ))}
                    </Select>
                  </Field>
                </div>
                <Field label={lab.searchScope}>
                  <TextInput name="scope" required />
                </Field>
              </ActionForm>
            </Card>

            <Card title={lab.reference} testId="reference">
              {standing ? (
                <div className="space-y-1 text-sm" data-testid="standing">
                  <p>
                    {lab.standing}: <Badge tone={standing.reference.result === "PASS" ? "good" : standing.reference.result === "BLOCKED" ? "warn" : "neutral"}>{standing.reference.result}</Badge>{" "}
                    {standing.operational.execution_ready ? null : <Badge tone="warn">BLOCKS_CURRENT_EXECUTION</Badge>}
                  </p>
                  <p className="text-[var(--color-muted)]">{standing.summary}</p>
                </div>
              ) : null}
              {hypothesisReviews.map((review) => (
                <div key={review.id} className="space-y-2 rounded-md border border-[var(--color-border)] p-2 text-sm" data-testid="review">
                  <p className="font-medium" dir="auto">
                    {review.question} <Badge>{review.analytical_category}</Badge>
                  </p>
                  <ul className="space-y-1">
                    {review.entries.map((e) => (
                      <li key={e.id}>
                        <Badge>{e.layer}</Badge> <span dir="auto">{e.content}</span>
                      </li>
                    ))}
                  </ul>
                  {review.current_judgment ? (
                    <p data-testid="current-judgment">
                      <Badge>{review.current_judgment.state}</Badge>{" "}
                      {review.current_judgment.reservation_type ? <Badge tone="warn">{review.current_judgment.reservation_type}</Badge> : null}{" "}
                      <span dir="auto">{review.current_judgment.rationale}</span>
                    </p>
                  ) : null}
                  <ActionForm action={addReviewEntry} submitLabel={lab.addEntry} pendingLabel={lab.saving}>
                    <input type="hidden" name="project_id" value={projectId} />
                    <input type="hidden" name="review_id" value={review.id} />
                    <div className="grid gap-3 sm:grid-cols-2">
                      <Field label={lab.layer}>
                        <Select name="layer" defaultValue="PRACTICAL_JUDGMENT">
                          {HUMAN_LAYERS.map((v) => (
                            <option key={v}>{v}</option>
                          ))}
                        </Select>
                      </Field>
                      <Field label={lab.quranRef}>
                        <TextInput name="quran_ref" placeholder="2:255" dir="ltr" />
                      </Field>
                    </div>
                    <Field label={lab.description}>
                      <TextArea name="content" rows={2} />
                    </Field>
                  </ActionForm>
                  <ActionForm action={judgeReview} submitLabel={lab.judge} pendingLabel={lab.saving} testId="judge-form">
                    <input type="hidden" name="project_id" value={projectId} />
                    <input type="hidden" name="review_id" value={review.id} />
                    <div className="grid gap-3 sm:grid-cols-3">
                      <Field label={lab.epistemic}>
                        <Select name="state" defaultValue="NOT_IN_CONFLICT">
                          {ReferenceJudgmentStateValues.map((v) => (
                            <option key={v}>{v}</option>
                          ))}
                        </Select>
                      </Field>
                      <Field label={lab.directness}>
                        <Select name="directness" defaultValue="INFERENTIAL">
                          {DirectnessValues.map((v) => (
                            <option key={v}>{v}</option>
                          ))}
                        </Select>
                      </Field>
                      <Field label={lab.reservation}>
                        <Select name="reservation_type" defaultValue="NON_BLOCKING_RESERVATION">
                          {ReservationTypeValues.map((v) => (
                            <option key={v}>{v}</option>
                          ))}
                        </Select>
                      </Field>
                    </div>
                    <Field label={lab.rationale}>
                      <TextArea name="rationale" required rows={2} />
                    </Field>
                  </ActionForm>
                </div>
              ))}
              <ActionForm action={createReview} submitLabel={lab.newReview} pendingLabel={lab.saving} testId="new-review">
                {target}
                <Field label={lab.question}>
                  <TextInput name="question" required />
                </Field>
                <Field label={lab.category}>
                  <Select name="analytical_category">
                    {ReferenceAnalyticalCategoryValues.map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </Select>
                </Field>
              </ActionForm>
            </Card>
          </div>

          <div className="space-y-6">
            <Card title={lab.advanceTo} testId="advance">
              <ActionForm action={transitionHypothesis} submitLabel={lab.advanceTo} pendingLabel={lab.saving}>
                {ids}
                <Field label={lab.lifecycle}>
                  <Select name="target" defaultValue={stages.at(-1)}>
                    {stages.map((s) => (
                      <option key={s}>{s}</option>
                    ))}
                  </Select>
                </Field>
                <Field label={lab.reason}>
                  <TextInput name="reason" required />
                </Field>
              </ActionForm>
            </Card>
            <Card title={lab.assess} testId="assess">
              <ActionForm action={assessHypothesis} submitLabel={lab.assess} pendingLabel={lab.saving}>
                {ids}
                <Field label={lab.epistemic}>
                  <Select name="epistemic_state" defaultValue={hypothesis.suggested_epistemic_state}>
                    {HypothesisEpistemicStateValues.map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </Select>
                </Field>
                <Field label={lab.reason}>
                  <TextInput name="reason" required />
                </Field>
              </ActionForm>
            </Card>
            <Card title={lab.revise} testId="revise">
              <ActionForm action={reviseHypothesis} submitLabel={lab.revise} pendingLabel={lab.saving}>
                {ids}
                <Field label={lab.statement}>
                  <TextArea name="statement" defaultValue={c.statement} rows={2} required />
                </Field>
                <Field label={lab.context}>
                  <TextArea name="context" defaultValue={c.context} rows={2} />
                </Field>
                <Field label={lab.expectedOutcome}>
                  <TextArea name="expected_outcome" defaultValue={c.expected_outcome} rows={2} />
                </Field>
                <Field label={lab.proposedMechanism}>
                  <TextArea name="proposed_mechanism" defaultValue={c.proposed_mechanism} rows={2} />
                </Field>
                <Field label={lab.hypothesisAssumptions} hint={dict.ui.listHint}>
                  <TextArea name="assumptions" defaultValue={c.assumptions.join("\n")} rows={2} />
                </Field>
                <Field label={lab.boundaryConditions} hint={dict.ui.listHint}>
                  <TextArea name="boundary_conditions" defaultValue={c.boundary_conditions.join("\n")} rows={2} />
                </Field>
                <Field label={lab.falsification} hint={dict.ui.listHint}>
                  <TextArea name="falsification_conditions" defaultValue={c.falsification_conditions.join("\n")} rows={2} />
                </Field>
                <Field label={lab.changeReason}>
                  <TextInput name="change_reason" required />
                </Field>
              </ActionForm>
            </Card>
            <Card title={lab.history} testId="versions">
              <ol className="space-y-1 text-sm">
                {(versions ?? []).map((v) => (
                  <li key={v.version_number} className="flex flex-wrap items-center gap-2">
                    <span>v{v.version_number}</span>
                    <Badge>{v.lifecycle_state}</Badge>
                    <Badge>{v.epistemic_state}</Badge>
                    <Badge>{v.actor.kind}</Badge>
                    <span dir="auto" className="text-[var(--color-muted)]">{v.change_reason}</span>
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
