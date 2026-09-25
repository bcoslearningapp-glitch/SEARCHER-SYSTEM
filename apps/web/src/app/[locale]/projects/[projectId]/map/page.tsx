import Link from "next/link";

import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty } from "@/components/fields";
import { ProjectHeader } from "@/components/ProjectHeader";
import { getDictionary } from "@/lib/i18n";
import { load, loadEntity } from "@/lib/load";
import { resolveProjectParams, type ProjectParams } from "@/lib/locale-params";
import type { AttentionItem, Decision, Hypothesis, OpenQuestion, ProblemFrame, Project } from "@/lib/types";

export const dynamic = "force-dynamic";

/** Project map with progressive disclosure (PRD §8.2): top level only; details live in the Lab. */
export default async function MapPage(props: ProjectParams) {
  const { locale, projectId } = await resolveProjectParams(props);
  const dict = getDictionary(locale);
  const lab = dict.lab;
  const base = `/api/v1/projects/${projectId}`;
  const project = await loadEntity<Project>(base);
  const [frames, hypotheses, questions, decisions, attention] = await Promise.all([
    load<ProblemFrame[]>(`${base}/problem-frames`),
    load<Hypothesis[]>(`${base}/hypotheses`),
    load<OpenQuestion[]>(`${base}/questions`),
    load<Decision[]>(`${base}/decisions`),
    load<AttentionItem[]>(`${base}/attention`),
  ]);
  const baseline = frames?.find((f) => f.status === "APPROVED");
  const blockers = (attention ?? []).filter((a) => a.level === "BLOCKING");

  return (
    <AppShell locale={locale} active="map">
      <div className="space-y-6">
        <ProjectHeader project={project} dict={dict} locale={locale} active="map" />
        <div className="grid gap-6 md:grid-cols-2">
          <Card title={lab.centralProblem} testId="central-problem">
            {baseline ? (
              <p dir="auto" className="text-sm">
                {baseline.content.central_issue}
              </p>
            ) : (
              <Empty>{dict.ui.none}</Empty>
            )}
          </Card>
          <Card title={lab.blockers} testId="blockers">
            {blockers.length ? (
              <ul className="space-y-1 text-sm">
                {blockers.map((b) => (
                  <li key={b.entity_id} dir="auto">
                    <Badge tone="warn">{b.level}</Badge> {b.title}
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{dict.ui.none}</Empty>
            )}
          </Card>
          <Card title={lab.hypotheses} testId="map-hypotheses">
            {hypotheses?.length ? (
              <ul className="space-y-2 text-sm">
                {hypotheses.map((h) => (
                  <li key={h.id} className="flex flex-wrap items-center gap-2">
                    <Link href={`/${locale}/projects/${projectId}/hypotheses/${h.id}`} dir="auto" className="underline-offset-2 hover:underline">
                      {h.content.statement}
                    </Link>
                    <Badge>{h.epistemic_state}</Badge>
                    {!h.counter_evidence_search_complete ? <Badge tone="warn">{lab.counterEvidence}: {lab.incomplete}</Badge> : null}
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{dict.ui.none}</Empty>
            )}
          </Card>
          <Card title={lab.openQuestions} testId="map-questions">
            {questions?.filter((q) => q.status === "OPEN").length ? (
              <ul className="list-disc space-y-1 ps-5 text-sm">
                {questions
                  .filter((q) => q.status === "OPEN")
                  .map((q) => (
                    <li key={q.id} dir="auto">
                      {q.question} <Badge>{q.question_type}</Badge>
                    </li>
                  ))}
              </ul>
            ) : (
              <Empty>{dict.ui.none}</Empty>
            )}
          </Card>
          <Card title={dict.ui.decisions} testId="map-decisions">
            {decisions?.length ? (
              <ul className="space-y-1 text-sm">
                {decisions.map((d) => (
                  <li key={d.id} dir="auto">
                    <Badge>{d.status}</Badge> {d.question} {d.final_decision ? `→ ${d.final_decision}` : ""}
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{dict.ui.none}</Empty>
            )}
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
