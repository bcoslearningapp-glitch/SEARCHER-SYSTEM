import { notFound } from "next/navigation";

import {
  addNote,
  approveFrame,
  captureNote,
  closeProject,
  createDecision,
  reopenProject,
  resolveDecision,
  saveFrameDraft,
  updateAIPolicy,
} from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AITasks } from "@/components/AITasks";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, Select, TextArea, TextInput } from "@/components/fields";
import { LoadError } from "@/components/LoadError";
import { ProjectHeader } from "@/components/ProjectHeader";
import { ClosureTypeValues } from "@/lib/contracts/enums";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveProjectParams, type ProjectParams } from "@/lib/locale-params";
import {
  FRAME_LIST_FIELDS,
  FRAME_TEXT_FIELDS,
  type AIPolicy,
  type AIProfile,
  type AttentionItem,
  type Closure,
  type Decision,
  type Job,
  type Note,
  type ProblemFrame,
  type Project,
  type ResearchState,
} from "@/lib/types";

export const dynamic = "force-dynamic";

function List({ items, empty }: { items: string[]; empty: string }) {
  if (!items.length) return <Empty>{empty}</Empty>;
  return (
    <ul className="list-disc space-y-1 ps-5 text-sm">
      {items.map((item) => (
        <li key={item} dir="auto">
          {item}
        </li>
      ))}
    </ul>
  );
}

export default async function ProjectPage(props: ProjectParams) {
  const { locale, projectId } = await resolveProjectParams(props);
  const dict = getDictionary(locale);
  const ui = dict.ui;
  const base = `/api/v1/projects/${projectId}`;
  const project = await load<Project>(base);
  if (project === null) {
    const exists = await load<Project[]>("/api/v1/projects");
    if (exists !== null) notFound();
    return (
      <AppShell locale={locale} active="desk">
        <LoadError dict={dict} />
      </AppShell>
    );
  }
  const closures = await load<Closure[]>(`${base}/closures`);
  const [state, frames, notes, decisions, attention, profiles, aiJobs, aiPolicy] = await Promise.all([
    load<ResearchState>(`${base}/research-state`),
    load<ProblemFrame[]>(`${base}/problem-frames`),
    load<Note[]>(`${base}/notes`),
    load<Decision[]>(`${base}/decisions`),
    load<AttentionItem[]>(`${base}/attention`),
    load<AIProfile[]>("/api/v1/ai/profiles"),
    load<Job[]>(`${base}/ai-tasks`),
    load<AIPolicy>(`${base}/ai-policy`),
  ]);
  const draft = frames?.find((f) => f.status === "DRAFT");
  const approved = frames?.find((f) => f.status === "APPROVED");
  const editing = draft ?? approved;

  return (
    <AppShell locale={locale} active="desk">
      <div className="space-y-6">
        <ProjectHeader project={project} dict={dict} locale={locale} active="desk" />
        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <div className="space-y-6">
            <Card title={dict.ai.title} testId="ai-assistance">
              <AITasks
                ai={dict.ai}
                projectId={project.id}
                profiles={profiles}
                jobs={aiJobs}
                launchers={[
                  { task: "draft_problem_frame", label: dict.ai.draftFrame },
                  { task: "detect_assumptions", label: dict.ai.detectAssumptions },
                ]}
              />
            </Card>

            {aiPolicy ? (
              <Card title={dict.ai.policy} testId="ai-policy">
                <p className="mb-3 text-sm text-[var(--color-muted)]">{dict.ai.policyExplainer}</p>
                <ActionForm action={updateAIPolicy} submitLabel={dict.ai.savePolicy} pendingLabel={dict.ai.saving} successMessage={ui.saved}>
                  <input type="hidden" name="project_id" value={project.id} />
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" name="cloud_consent" defaultChecked={aiPolicy.cloud_consent} />
                    {dict.ai.cloudConsent}
                  </label>
                  <fieldset className="space-y-1 text-sm">
                    <legend className="font-medium">{dict.ai.allowedProfiles}</legend>
                    <p className="text-[var(--color-muted)]">{dict.ai.anyProfile}</p>
                    {(profiles ?? []).map((p) => (
                      <label key={p.name} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          name="allowed_profiles"
                          value={p.name}
                          defaultChecked={aiPolicy.allowed_profiles.includes(p.name)}
                        />
                        <span dir="ltr">{p.name}</span>
                      </label>
                    ))}
                  </fieldset>
                  <Field label={dict.ai.preferredProfile}>
                    <Select name="preferred_profile" defaultValue={aiPolicy.preferred_profile ?? ""}>
                      <option value="">—</option>
                      {(profiles ?? []).map((p) => (
                        <option key={p.name}>{p.name}</option>
                      ))}
                    </Select>
                  </Field>
                  <Field label={dict.ai.projectBudget}>
                    <TextInput name="project_budget_usd" type="number" min={0} step="0.01" defaultValue={aiPolicy.project_budget_usd ?? ""} />
                  </Field>
                  <Field label={dict.ai.taskBudget}>
                    <TextInput name="task_budget_usd" type="number" min={0} step="0.01" defaultValue={aiPolicy.task_budget_usd ?? ""} />
                  </Field>
                  <p className="text-sm">
                    {dict.ai.spent}: <span dir="ltr">${Number(aiPolicy.spent_usd).toFixed(4)}</span>
                  </p>
                </ActionForm>
              </Card>
            ) : null}

            <Card title={ui.problemFrame} testId="problem-frame">
              <ActionForm action={saveFrameDraft} submitLabel={ui.saveDraft} pendingLabel={ui.saving} successMessage={ui.saved} testId="frame-form">
                <input type="hidden" name="project_id" value={project.id} />
                <div className="grid gap-3 sm:grid-cols-2">
                  {FRAME_TEXT_FIELDS.map((field) => (
                    <Field key={field} label={ui.frameFields[field]}>
                      <TextArea name={field} rows={2} defaultValue={editing?.content[field] ?? ""} />
                    </Field>
                  ))}
                  {FRAME_LIST_FIELDS.map((field) => (
                    <Field key={field} label={ui.frameFields[field]} hint={ui.listHint}>
                      <TextArea name={field} rows={3} defaultValue={(editing?.content[field] ?? []).join("\n")} />
                    </Field>
                  ))}
                </div>
              </ActionForm>
              {draft ? (
                <div className="space-y-2 border-t border-[var(--color-border)] pt-3">
                  <p className="text-sm text-[var(--color-muted)]">{ui.approvalExplainer}</p>
                  <ActionForm action={approveFrame} submitLabel={ui.approve} pendingLabel={ui.approving} successMessage={ui.approvedMessage} testId="approve-form">
                    <input type="hidden" name="project_id" value={project.id} />
                    <input type="hidden" name="version_id" value={draft.id} />
                    <label className="flex items-center gap-2 text-sm">
                      <input type="checkbox" name="acknowledge_reservations" />
                      {ui.acknowledgeReservations}
                    </label>
                    <Field label={ui.approvalReason}>
                      <TextInput name="reason" />
                    </Field>
                  </ActionForm>
                </div>
              ) : null}
              {frames && frames.length ? (
                <div className="border-t border-[var(--color-border)] pt-3">
                  <h3 className="mb-1 text-sm font-semibold">{ui.frameHistory}</h3>
                  <ul className="space-y-1 text-sm" data-testid="frame-history">
                    {frames.map((f) => (
                      <li key={f.id} className="flex items-center gap-2">
                        <span>v{f.version_number}</span>
                        <Badge tone={f.status === "APPROVED" ? "good" : "neutral"}>{f.status}</Badge>
                        <Badge>{f.provenance.kind}</Badge>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </Card>

            <Card title={ui.notes} testId="notes">
              <p className="text-sm text-[var(--color-muted)]">{ui.notesExplainer}</p>
              <ActionForm action={addNote} submitLabel={ui.add} pendingLabel={ui.adding}>
                <input type="hidden" name="project_id" value={project.id} />
                <Field label={ui.noteBody}>
                  <TextArea name="body" required rows={2} />
                </Field>
              </ActionForm>
              {notes?.length ? (
                <ul className="space-y-2">
                  {notes.map((note) => (
                    <li key={note.id} className="rounded-md border border-[var(--color-border)] p-2 text-sm">
                      <p dir="auto" className="whitespace-pre-wrap">
                        {note.body}
                      </p>
                      {note.captured_as ? (
                        <Badge tone="good">
                          {ui.captured}: {ui.captureAs[note.captured_as as keyof typeof ui.captureAs] ?? note.captured_as}
                        </Badge>
                      ) : (
                        <ActionForm action={captureNote} submitLabel={ui.capture} pendingLabel={ui.saving} className="mt-2 flex flex-wrap items-end gap-2">
                          <input type="hidden" name="project_id" value={project.id} />
                          <input type="hidden" name="note_id" value={note.id} />
                          <Select name="target" aria-label={ui.capture} defaultValue="unresolved_item">
                            {(Object.keys(ui.captureAs) as (keyof typeof ui.captureAs)[]).map((k) => (
                              <option key={k} value={k}>
                                {ui.captureAs[k]}
                              </option>
                            ))}
                          </Select>
                        </ActionForm>
                      )}
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>

            <Card title={ui.decisions} testId="decisions">
              {decisions?.length ? (
                <ul className="space-y-3">
                  {decisions.map((d) => (
                    <li key={d.id} className="space-y-2 rounded-md border border-[var(--color-border)] p-2 text-sm">
                      <p dir="auto" className="font-medium">
                        {d.question} {d.blocking ? <Badge tone="warn">{ui.blocking}</Badge> : null} <Badge>{d.status}</Badge>
                      </p>
                      {d.ai_recommendation ? (
                        <p className="text-[var(--color-muted)]">
                          {ui.aiRecommendation}: {d.ai_recommendation.option} — {d.ai_recommendation.rationale}
                        </p>
                      ) : null}
                      {d.status === "DECIDED" ? (
                        <p>
                          {ui.finalDecision}: <strong>{d.final_decision}</strong> — {d.human_justification}
                        </p>
                      ) : d.status === "OPEN" ? (
                        <ActionForm action={resolveDecision} submitLabel={ui.resolve} pendingLabel={ui.saving}>
                          <input type="hidden" name="project_id" value={project.id} />
                          <input type="hidden" name="decision_id" value={d.id} />
                          <Field label={ui.finalDecision}>
                            <Select name="final_decision">
                              {d.options.map((o) => (
                                <option key={o}>{o}</option>
                              ))}
                            </Select>
                          </Field>
                          <Field label={ui.justification}>
                            <TextInput name="human_justification" required />
                          </Field>
                        </ActionForm>
                      ) : null}
                    </li>
                  ))}
                </ul>
              ) : null}
              <ActionForm action={createDecision} submitLabel={ui.createDecision} pendingLabel={ui.saving}>
                <input type="hidden" name="project_id" value={project.id} />
                <Field label={ui.question}>
                  <TextInput name="question" required />
                </Field>
                <Field label={ui.options} hint={ui.optionsHint}>
                  <TextArea name="options" required rows={2} />
                </Field>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" name="blocking" />
                  {ui.blocking}
                </label>
              </ActionForm>
            </Card>
          </div>

          <div className="space-y-6">
            <Card title={ui.researchState} testId="research-state">
              {state === null ? (
                <LoadError dict={dict} />
              ) : (
                <dl className="space-y-3 text-sm">
                  <div>
                    <dt className="font-medium">{ui.currentQuestion}</dt>
                    <dd data-testid="current-question" dir="auto">{state.current_question ?? <Empty>{ui.none}</Empty>}</dd>
                  </div>
                  <div>
                    <dt className="font-medium">{ui.nextAction}</dt>
                    <dd dir="auto">{state.next_action}</dd>
                    {state.next_action_reason ? (
                      <dd className="text-[var(--color-muted)]">
                        {ui.why}: {state.next_action_reason}
                      </dd>
                    ) : null}
                  </div>
                  <div>
                    <dt className="font-medium">{ui.unresolved}</dt>
                    <dd>
                      <List items={state.unresolved_items} empty={ui.none} />
                    </dd>
                  </div>
                  <div>
                    <dt className="font-medium">{ui.findings}</dt>
                    <dd>
                      <List items={state.established_findings} empty={ui.none} />
                    </dd>
                  </div>
                </dl>
              )}
            </Card>
            {project.status === "READY_TO_CLOSE" || project.status === "CLOSED" || closures?.length ? (
              <Card title={dict.closure.title} testId="closure">
                <p className="text-sm text-[var(--color-muted)]">{dict.closure.explainer}</p>
                {project.status === "READY_TO_CLOSE" ? (
                  <ActionForm action={closeProject} submitLabel={dict.closure.close} pendingLabel={dict.closure.closing} testId="close-form">
                    <input type="hidden" name="project_id" value={projectId} />
                    <Field label={dict.closure.closureType}>
                      <Select name="closure_type" defaultValue="KNOWLEDGE_CONCLUSION">
                        {ClosureTypeValues.map((v) => (
                          <option key={v}>{v}</option>
                        ))}
                      </Select>
                    </Field>
                    <Field label={dict.closure.resolved} hint={dict.closure.listHint}>
                      <TextArea name="resolved" rows={2} required />
                    </Field>
                    <Field label={dict.closure.confidenceScope}>
                      <TextInput name="confidence_scope" required />
                    </Field>
                    {(["unresolved", "limitations", "open_questions", "reopen_triggers"] as const).map((f) => (
                      <Field
                        key={f}
                        label={
                          {
                            unresolved: dict.closure.unresolved,
                            limitations: dict.closure.limitations,
                            open_questions: dict.closure.openQuestions,
                            reopen_triggers: dict.closure.reopenTriggers,
                          }[f]
                        }
                        hint={dict.closure.listHint}
                      >
                        <TextArea name={f} rows={2} />
                      </Field>
                    ))}
                    <label className="flex items-center gap-2 text-xs">
                      <input type="checkbox" name="acknowledge_reservations" />
                      {dict.closure.acknowledge}
                    </label>
                    <Field label={dict.closure.overrideReason}>
                      <TextInput name="override_reason" />
                    </Field>
                  </ActionForm>
                ) : null}
                {project.status === "CLOSED" ? (
                  <ActionForm action={reopenProject} submitLabel={dict.closure.reopen} pendingLabel={dict.closure.closing} testId="reopen-form">
                    <input type="hidden" name="project_id" value={projectId} />
                    <p className="text-xs text-[var(--color-muted)]">{dict.closure.reopenExplainer}</p>
                    <Field label={dict.closure.reopenTrigger}>
                      <TextInput name="trigger" required />
                    </Field>
                  </ActionForm>
                ) : null}
                {closures?.length ? (
                  <div data-testid="closure-history">
                    <p className="text-sm font-medium">{dict.closure.history}</p>
                    <ul className="space-y-1 text-sm">
                      {closures.map((c) => (
                        <li key={c.id}>
                          <Badge>{c.closure_type}</Badge> <span dir="auto">{c.record.confidence_scope}</span>
                          {c.reopen_trigger ? (
                            <span className="block text-xs" dir="auto">
                              {dict.closure.reopenedBecause}: {c.reopen_trigger}
                            </span>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </Card>
            ) : null}
            <Card title={ui.attention} testId="attention">
              {attention === null ? (
                <LoadError dict={dict} />
              ) : attention.length === 0 ? (
                <Empty>{ui.nothingNeedsAttention}</Empty>
              ) : (
                <ul className="space-y-2 text-sm">
                  {attention.map((item) => (
                    <li key={item.entity_id} className="flex items-start gap-2">
                      <Badge tone={item.level === "BLOCKING" ? "warn" : "neutral"}>{item.level}</Badge>
                      <span dir="auto">{item.title}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
