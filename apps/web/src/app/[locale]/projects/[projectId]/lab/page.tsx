import Link from "next/link";
import { notFound } from "next/navigation";

import { createAssumption, createClaim, createHypothesis, createMechanism, reviewAssumption } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, Select, TextArea, TextInput } from "@/components/fields";
import { ProjectHeader } from "@/components/ProjectHeader";
import { ClaimTypeValues, CriticalityValues } from "@/lib/contracts/enums";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveProjectParams, type ProjectParams } from "@/lib/locale-params";
import type { Assumption, Claim, Hypothesis, Mechanism, Project } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function LabPage(props: ProjectParams) {
  const { locale, projectId } = await resolveProjectParams(props);
  const dict = getDictionary(locale);
  const lab = dict.lab;
  const base = `/api/v1/projects/${projectId}`;
  const project = await load<Project>(base);
  if (project === null) notFound();
  const [claims, assumptions, hypotheses, mechanisms] = await Promise.all([
    load<Claim[]>(`${base}/claims`),
    load<Assumption[]>(`${base}/assumptions`),
    load<Hypothesis[]>(`${base}/hypotheses`),
    load<Mechanism[]>(`${base}/mechanisms`),
  ]);
  const hidden = <input type="hidden" name="project_id" value={projectId} />;

  return (
    <AppShell locale={locale} active="lab">
      <div className="space-y-6">
        <ProjectHeader project={project} dict={dict} locale={locale} active="lab" />
        <div className="grid gap-6 lg:grid-cols-2">
          <Card title={lab.hypotheses} testId="hypotheses">
            {hypotheses?.length ? (
              <ul className="space-y-2 text-sm">
                {hypotheses.map((h) => (
                  <li key={h.id} className="flex flex-wrap items-center gap-2" data-testid="hypothesis-row">
                    <Link href={`/${locale}/projects/${projectId}/hypotheses/${h.id}`} dir="auto" className="font-medium underline-offset-2 hover:underline">
                      {h.content.statement}
                    </Link>
                    <Badge>{h.lifecycle_state}</Badge>
                    <Badge tone={h.epistemic_state === "SUPPORTED" ? "good" : ["CONTESTED", "WEAKENED", "REFUTED"].includes(h.epistemic_state) ? "warn" : "neutral"}>
                      {h.epistemic_state}
                    </Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{dict.ui.none}</Empty>
            )}
            <ActionForm action={createHypothesis} submitLabel={lab.newHypothesis} pendingLabel={lab.saving} testId="new-hypothesis">
              {hidden}
              <Field label={lab.statement}>
                <TextArea name="statement" required rows={2} />
              </Field>
            </ActionForm>
          </Card>

          <Card title={lab.claims} testId="claims">
            {claims?.length ? (
              <ul className="space-y-2 text-sm">
                {claims.map((c) => (
                  <li key={c.id} className="flex flex-wrap items-center gap-2">
                    <span dir="auto">{c.statement}</span>
                    <Badge>{c.claim_type}</Badge>
                    <Badge>{c.epistemic_strength}</Badge>
                    {c.statement_origin === "SYSTEM_INFERRED" ? <Badge tone="warn">AI</Badge> : null}
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{dict.ui.none}</Empty>
            )}
            <ActionForm action={createClaim} submitLabel={lab.newClaim} pendingLabel={lab.saving}>
              {hidden}
              <Field label={lab.statement}>
                <TextArea name="statement" required rows={2} />
              </Field>
              <Field label={lab.claimType}>
                <Select name="claim_type" defaultValue="OBSERVATION">
                  {ClaimTypeValues.map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </Select>
              </Field>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" name="important" />
                {lab.important}
              </label>
            </ActionForm>
          </Card>

          <Card title={lab.assumptions} testId="assumptions">
            {assumptions?.length ? (
              <ul className="space-y-2 text-sm">
                {assumptions.map((a) => (
                  <li key={a.id} className="space-y-1">
                    <p className="flex flex-wrap items-center gap-2">
                      <span dir="auto">{a.statement}</span>
                      <Badge>{a.origin}</Badge>
                      <Badge>{a.criticality}</Badge>
                      <Badge tone={a.status === "UNCONFIRMED" ? "warn" : "neutral"}>{a.status}</Badge>
                    </p>
                    {a.status === "UNCONFIRMED" ? (
                      <ActionForm action={reviewAssumption} submitLabel={lab.save} pendingLabel={lab.saving} className="flex flex-wrap items-center gap-2">
                        {hidden}
                        <input type="hidden" name="assumption_id" value={a.id} />
                        <Select name="status" aria-label={lab.origin}>
                          <option value="CONFIRMED">{lab.confirm}</option>
                          <option value="REJECTED">{lab.reject}</option>
                        </Select>
                      </ActionForm>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{dict.ui.none}</Empty>
            )}
            <ActionForm action={createAssumption} submitLabel={lab.newAssumption} pendingLabel={lab.saving}>
              {hidden}
              <Field label={lab.statement}>
                <TextArea name="statement" required rows={2} />
              </Field>
              <Field label={lab.criticality}>
                <Select name="criticality" defaultValue="MEDIUM">
                  {CriticalityValues.map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </Select>
              </Field>
            </ActionForm>
          </Card>

          <Card title={lab.mechanisms} testId="mechanisms">
            {mechanisms?.length ? (
              <ul className="space-y-2 text-sm">
                {mechanisms.map((m) => (
                  <li key={m.id} className="flex flex-wrap items-center gap-2">
                    <span dir="auto" className="font-medium">{m.name}</span>
                    <span dir="auto" className="text-[var(--color-muted)]">{m.description}</span>
                    <Badge>{m.status}</Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{dict.ui.none}</Empty>
            )}
            <ActionForm action={createMechanism} submitLabel={lab.newMechanism} pendingLabel={lab.saving}>
              {hidden}
              <Field label={lab.name}>
                <TextInput name="name" required />
              </Field>
              <Field label={lab.description}>
                <TextArea name="description" required rows={2} />
              </Field>
            </ActionForm>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
