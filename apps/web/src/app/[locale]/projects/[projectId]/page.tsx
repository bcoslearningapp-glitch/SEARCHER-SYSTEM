import { notFound } from "next/navigation";

import { addNote, approveFrame, captureNote, createDecision, resolveDecision, saveFrameDraft } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, Select, TextArea, TextInput } from "@/components/fields";
import { LoadError } from "@/components/LoadError";
import { ProjectHeader } from "@/components/ProjectHeader";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveProjectParams, type ProjectParams } from "@/lib/locale-params";
import {
  FRAME_LIST_FIELDS,
  FRAME_TEXT_FIELDS,
  type AttentionItem,
  type Decision,
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
  const [state, frames, notes, decisions, attention] = await Promise.all([
    load<ResearchState>(`${base}/research-state`),
    load<ProblemFrame[]>(`${base}/problem-frames`),
    load<Note[]>(`${base}/notes`),
    load<Decision[]>(`${base}/decisions`),
    load<AttentionItem[]>(`${base}/attention`),
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
