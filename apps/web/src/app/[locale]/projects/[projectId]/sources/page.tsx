
import { requestAccess, respondToAccess } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { CatalogForm } from "@/components/CatalogForm";
import { Badge, Card, Empty, Field, Select, TextArea, TextInput } from "@/components/fields";
import { Pager, pageNumber, pageQuery, pageSlice } from "@/components/Pager";
import { ProjectHeader } from "@/components/ProjectHeader";
import { SourceList } from "@/components/SourceList";
import { AccessResponseFormValues, PriorityValues } from "@/lib/contracts/enums";
import { getDictionary } from "@/lib/i18n";
import { load, loadEntity } from "@/lib/load";
import { resolveProjectParams, type ProjectParams } from "@/lib/locale-params";
import type { AccessRequest, Excerpt, Project, Work } from "@/lib/types";

export const dynamic = "force-dynamic";

const TEXT_FORMS = ["EXACT_TEXT", "RESEARCHER_SUMMARY", "RESEARCHER_ATTESTATION"];

type Props = ProjectParams & { searchParams: Promise<{ page?: string }> };

export default async function ProjectSourcesPage(props: Props) {
  const { locale, projectId } = await resolveProjectParams(props);
  const page = pageNumber((await props.searchParams).page);
  const dict = getDictionary(locale);
  const ui = dict.ui;
  const project = await loadEntity<Project>(`/api/v1/projects/${projectId}`);
  const [listed, library, requests] = await Promise.all([
    load<Work[]>(`/api/v1/sources?project_id=${projectId}&${pageQuery(page)}`),
    load<Work[]>("/api/v1/sources"),
    load<AccessRequest[]>(`/api/v1/projects/${projectId}/access-requests`),
  ]);
  const works = pageSlice(listed ?? []);
  const editionIds = [...new Set((requests ?? []).map((r) => r.edition_id))];
  const excerptLists = await Promise.all(editionIds.map((id) => load<Excerpt[]>(`/api/v1/sources/editions/${id}/excerpts`)));
  const excerpts = excerptLists.flatMap((list) => list ?? []);
  const editions = (library ?? []).flatMap((w) => w.editions.map((e) => ({ work: w, edition: e })));

  return (
    <AppShell locale={locale} active="library">
      <div className="space-y-6">
        <ProjectHeader project={project} dict={dict} locale={locale} active="sources" />
        <Card title={ui.sources}>
          <SourceList works={works.items} dict={dict} />
          <Pager page={page} hasNext={works.hasNext} href={(n) => `/${locale}/projects/${projectId}/sources?page=${n}`} dict={dict} />
          <details className="text-sm">
            <summary className="cursor-pointer font-medium">{ui.catalogSource}</summary>
            <div className="pt-3">
              <CatalogForm dict={dict} projectId={projectId} />
            </div>
          </details>
        </Card>

        <Card title={ui.accessRequests} testId="access-requests">
          {editions.length ? (
            <ActionForm action={requestAccess} submitLabel={ui.requestAccess} pendingLabel={ui.requesting} testId="access-request-form">
              <input type="hidden" name="project_id" value={projectId} />
              <Field label={ui.edition}>
                <Select name="edition_id">
                  {editions.map(({ work, edition }) => (
                    <option key={edition.id} value={edition.id}>
                      {work.title}
                      {edition.edition_label ? ` — ${edition.edition_label}` : ""} ({edition.available ? ui.available : ui.unavailable})
                    </option>
                  ))}
                </Select>
              </Field>
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label={ui.reason}>
                  <TextInput name="reason" required />
                </Field>
                <Field label={ui.scope}>
                  <TextInput name="requested_scope" required />
                </Field>
              </div>
              <fieldset className="text-sm">
                <legend className="font-medium">{ui.acceptableForms}</legend>
                <div className="flex flex-wrap gap-3 pt-1">
                  {AccessResponseFormValues.map((form) => (
                    <label key={form} className="flex items-center gap-1">
                      <input type="checkbox" name="acceptable_forms" value={form} defaultChecked={form === "EXACT_TEXT"} />
                      {form}
                    </label>
                  ))}
                </div>
              </fieldset>
              <Field label={ui.priority}>
                <Select name="priority" defaultValue="MEDIUM">
                  {PriorityValues.map((p) => (
                    <option key={p}>{p}</option>
                  ))}
                </Select>
              </Field>
            </ActionForm>
          ) : (
            <Empty>{ui.noSources}</Empty>
          )}

          {requests?.length ? (
            <ul className="space-y-3">
              {requests.map((request) => {
                const supplied = excerpts.filter((e) => e.access_request_id === request.id);
                const textForms = request.acceptable_forms.filter((f) => TEXT_FORMS.includes(f));
                const open = request.status === "OPEN" || request.status === "PARTIALLY_FULFILLED";
                return (
                  <li key={request.id} className="space-y-2 rounded-md border border-[var(--color-border)] p-3 text-sm" data-testid="access-request">
                    <p className="flex flex-wrap items-center gap-2">
                      <span dir="auto" className="font-medium">
                        {request.requested_scope}
                      </span>
                      <Badge>{request.priority}</Badge>
                      <span data-testid="request-status">
                        <Badge tone={request.status === "FULFILLED" ? "good" : "neutral"}>{request.status}</Badge>
                      </span>
                    </p>
                    <p dir="auto" className="text-[var(--color-muted)]">
                      {request.reason}
                    </p>
                    {supplied.length ? (
                      <ul className="space-y-1">
                        {supplied.map((excerpt) => (
                          <li key={excerpt.id} className="rounded bg-[var(--color-bg)] p-2" data-testid="excerpt">
                            <p dir="auto" className="whitespace-pre-wrap">{excerpt.is_exact_quote ? `“${excerpt.text}”` : excerpt.text}</p>
                            <p className="flex flex-wrap gap-2 pt-1 text-xs">
                              <span>{excerpt.location}</span>
                              <Badge tone={excerpt.is_exact_quote ? "good" : "neutral"}>{excerpt.verification_state}</Badge>
                            </p>
                          </li>
                        ))}
                      </ul>
                    ) : null}
                    {open && textForms.length ? (
                      <ActionForm action={respondToAccess} submitLabel={ui.respond} pendingLabel={ui.saving} testId="respond-form">
                        <input type="hidden" name="project_id" value={projectId} />
                        <input type="hidden" name="request_id" value={request.id} />
                        <div className="grid gap-3 sm:grid-cols-2">
                          <Field label={ui.responseForm}>
                            <Select name="form">
                              {textForms.map((f) => (
                                <option key={f}>{f}</option>
                              ))}
                            </Select>
                          </Field>
                          <Field label={ui.location}>
                            <TextInput name="location" required />
                          </Field>
                        </div>
                        <Field label={ui.excerptText}>
                          <TextArea name="text" required />
                        </Field>
                        <label className="flex items-center gap-2">
                          <input type="checkbox" name="fulfills_request" />
                          {ui.fulfills}
                        </label>
                      </ActionForm>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          ) : null}
        </Card>
      </div>
    </AppShell>
  );
}
