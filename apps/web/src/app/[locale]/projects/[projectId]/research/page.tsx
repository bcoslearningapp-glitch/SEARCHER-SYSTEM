import Link from "next/link";
import { notFound } from "next/navigation";

import { createResearchPlan } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, Select, TextArea, TextInput } from "@/components/fields";
import { ProjectHeader } from "@/components/ProjectHeader";
import { ResearchQuestionTypeValues } from "@/lib/contracts/enums";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveProjectParams, type ProjectParams } from "@/lib/locale-params";
import type { Project, ResearchPlan } from "@/lib/types";

export const dynamic = "force-dynamic";

const TRACKS = ["SUPPORT", "CHALLENGE", "ALTERNATIVE_EXPLANATION"] as const;

/** Research questions and plans (PRD §22): every plan covers support, challenge and alternative tracks. */
export default async function ResearchPage(props: ProjectParams) {
  const { locale, projectId } = await resolveProjectParams(props);
  const dict = getDictionary(locale);
  const r = dict.research;
  const base = `/api/v1/projects/${projectId}`;
  const project = await load<Project>(base);
  if (project === null) notFound();
  const plans = await load<ResearchPlan[]>(`${base}/research-plans`);

  return (
    <AppShell locale={locale} active="map">
      <div className="space-y-6">
        <ProjectHeader project={project} dict={dict} locale={locale} active="research" />
        <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
          <Card title={r.plans} testId="plans">
            {plans?.length ? (
              <ul className="space-y-2 text-sm">
                {plans.map((plan) => (
                  <li key={plan.id} className="rounded-md border border-[var(--color-border)] p-2">
                    <Link href={`/${locale}/projects/${projectId}/research/${plan.id}`} className="font-medium underline" dir="auto">
                      {plan.question}
                    </Link>
                    <div className="mt-1 flex flex-wrap gap-2">
                      <Badge>{plan.question_type}</Badge>
                      <Badge>
                        {r.version} {plan.version_number}
                      </Badge>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{r.noPlans}</Empty>
            )}
          </Card>
          <Card title={r.newPlan} testId="new-plan">
            <ActionForm action={createResearchPlan} submitLabel={r.create} pendingLabel={r.creating}>
              <input type="hidden" name="project_id" value={projectId} />
              <Field label={r.question}>
                <TextArea name="question" rows={2} required />
              </Field>
              <Field label={r.decisionServed}>
                <TextInput name="decision_served" required />
              </Field>
              <Field label={r.questionType}>
                <Select name="question_type" defaultValue="EMPIRICAL">
                  {ResearchQuestionTypeValues.map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </Select>
              </Field>
              <Field label={r.riskImpact}>
                <TextInput name="risk_impact" />
              </Field>
              {TRACKS.map((track) => (
                <Field key={track} label={r.trackApproach[track]}>
                  <TextArea name={`approach_${track}`} rows={2} required />
                </Field>
              ))}
              <Field label={r.evidenceTypes} hint={r.queriesHint}>
                <TextArea name="desired_evidence_types" rows={2} />
              </Field>
              <Field label={r.languages} hint={r.languagesHint}>
                <TextArea name="languages" rows={2} />
              </Field>
              <Field label={r.sufficiencyCriteria} hint={r.queriesHint}>
                <TextArea name="sufficiency_criteria" rows={2} required />
              </Field>
              <Field label={r.maxWebSearches}>
                <TextInput name="max_web_searches" type="number" min={0} />
              </Field>
            </ActionForm>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
