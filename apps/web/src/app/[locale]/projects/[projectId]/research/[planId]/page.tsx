import { notFound } from "next/navigation";

import { assessSufficiency, launchAITask, searchLocalLibrary } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AITasks } from "@/components/AITasks";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, Select, TextArea } from "@/components/fields";
import { ProjectHeader } from "@/components/ProjectHeader";
import { ResearchTrackValues, SufficiencyResultValues } from "@/lib/contracts/enums";
import { getDictionary } from "@/lib/i18n";
import { load, loadEntity } from "@/lib/load";
import { resolveLocale } from "@/lib/locale-params";
import type { AIProfile, Job, PlanOverview, Project, SourceLead } from "@/lib/types";

export const dynamic = "force-dynamic";

type Props = { params: Promise<{ locale: string; projectId: string; planId: string }> };

const CONSIDERATIONS = [
  "support_evidence",
  "counter_evidence",
  "alternative_explanations",
  "independence",
  "diversity",
  "context_fit",
  "critical_unknowns",
  "impact",
  "reversibility",
  "remaining_uncertainty",
] as const;

/** One research plan: what was searched per track, the search log, web leads and the sufficiency judgment. */
export default async function PlanPage(props: Props) {
  const { projectId, planId } = await props.params;
  const locale = await resolveLocale({ params: props.params });
  if (!/^[0-9a-f-]{36}$/i.test(projectId) || !/^[0-9a-f-]{36}$/i.test(planId)) notFound();
  const dict = getDictionary(locale);
  const r = dict.research;
  const base = `/api/v1/projects/${projectId}`;
  const [project, overview] = await Promise.all([loadEntity<Project>(base), loadEntity<PlanOverview>(`${base}/research-plans/${planId}`)]);
  const [profiles, aiJobs, leads] = await Promise.all([
    load<AIProfile[]>("/api/v1/ai/profiles"),
    load<Job[]>(`${base}/ai-tasks`),
    load<SourceLead[]>(`${base}/source-leads`),
  ]);
  const plan = overview.plan;
  const searchIds = new Set(overview.searches.map((s) => s.id));
  const webLeads = (leads ?? []).filter((l) => l.origin === "WEB_SEARCH" && l.search_record_id && searchIds.has(l.search_record_id));
  const webJobs = (aiJobs ?? []).filter((j) => j.kind === "orchestrator.web_search" && j.params.plan_id === planId);
  const ids = (
    <>
      <input type="hidden" name="project_id" value={projectId} />
      <input type="hidden" name="plan_id" value={planId} />
    </>
  );
  const searchFields = (
    <div className="grid gap-3 sm:grid-cols-2">
      <Field label={r.track}>
        <Select name="track" defaultValue="CHALLENGE">
          {ResearchTrackValues.map((v) => (
            <option key={v}>{v}</option>
          ))}
        </Select>
      </Field>
      <Field label={r.languages} hint={r.languagesHint}>
        <TextArea name="languages" rows={2} defaultValue={plan.languages.join("\n")} />
      </Field>
      <Field label={r.queries} hint={r.queriesHint}>
        <TextArea name="queries" rows={3} required />
      </Field>
    </div>
  );

  return (
    <AppShell locale={locale} active="map">
      <div className="space-y-6">
        <ProjectHeader project={project} dict={dict} locale={locale} active="research" />
        <Card title={r.question} testId="plan">
          <p dir="auto" className="text-lg font-medium">
            {plan.question}
          </p>
          <p dir="auto" className="text-sm">
            <span className="text-[var(--color-muted)]">{r.decisionServed}: </span>
            {plan.decision_served}
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge>{plan.question_type}</Badge>
            <Badge>
              {r.version} {plan.version_number}
            </Badge>
            {plan.languages.map((l) => (
              <Badge key={l}>{l}</Badge>
            ))}
          </div>
          <ul className="space-y-1 text-sm">
            {plan.tracks.map((t) => (
              <li key={t.track} dir="auto">
                <span className="font-medium">{t.track}:</span> {t.approach}
              </li>
            ))}
          </ul>
        </Card>

        <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
          <Card title={r.coverage} testId="coverage">
            <ul className="space-y-1 text-sm">
              {overview.coverage.map((c) => (
                <li key={c.track} data-testid={`coverage-${c.track}`}>
                  {c.track}:{" "}
                  <Badge tone={c.searched ? "good" : c.execution_failed ? "warn" : "neutral"}>
                    {c.searched ? r.searched : c.execution_failed ? r.failed : r.notSearched}
                  </Badge>{" "}
                  {c.last_outcome ? <Badge>{c.last_outcome}</Badge> : null}
                </li>
              ))}
            </ul>
            <p className="text-sm text-[var(--color-muted)]">
              {r.webUsed}: {overview.web_searches_used}
              {plan.max_web_searches !== null ? ` / ${plan.max_web_searches}` : ""}
            </p>
          </Card>

          <Card title={r.localSearch} testId="local-search">
            <p className="text-sm text-[var(--color-muted)]">{r.localExplainer}</p>
            <ActionForm action={searchLocalLibrary} submitLabel={r.search} pendingLabel={r.searching}>
              {ids}
              {searchFields}
            </ActionForm>
          </Card>

          <Card title={r.webSearch} testId="web-search">
            <ActionForm action={launchAITask} submitLabel={r.webSearch} pendingLabel={dict.ai.launching} successMessage={dict.ai.queued}>
              {ids}
              <input type="hidden" name="task" value="web_search" />
              {searchFields}
            </ActionForm>
            <AITasks ai={dict.ai} projectId={projectId} profiles={profiles} jobs={webJobs} launchers={[]} explainer={r.webExplainer} />
          </Card>

          <Card title={r.leads} testId="web-leads">
            {webLeads.length ? (
              <ul className="space-y-1 text-sm">
                {webLeads.map((lead) => (
                  <li key={lead.id} dir="auto">
                    <Badge>{lead.status}</Badge>{" "}
                    {lead.url ? (
                      <a href={lead.url} rel="noopener noreferrer nofollow" target="_blank" className="underline">
                        {lead.title ?? lead.url}
                      </a>
                    ) : (
                      lead.statement
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{r.noLeads}</Empty>
            )}
          </Card>
        </div>

        <Card title={r.searches} testId="search-log">
          {overview.searches.length ? (
            <ul className="space-y-2 text-sm">
              {overview.searches.map((s) => (
                <li key={s.id} className="rounded-md border border-[var(--color-border)] p-2" data-testid="search-record">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge>{s.provider}</Badge>
                    {s.track ? <Badge>{s.track}</Badge> : null}
                    <Badge tone={s.outcome === "RESULTS_FOUND" ? "good" : s.outcome === "NO_RELEVANT_EVIDENCE_FOUND" ? "neutral" : "warn"}>
                      {s.outcome}
                    </Badge>
                    <span>{s.result_count}</span>
                    <span className="text-[var(--color-muted)]">{new Date(s.performed_at).toLocaleString(locale)}</span>
                  </div>
                  <p dir="auto" className="mt-1">
                    {s.queries.join(" · ")}
                  </p>
                  <p dir="auto" className="text-[var(--color-muted)]">
                    {s.scope}
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <Empty>{r.noSearches}</Empty>
          )}
        </Card>

        <Card title={r.sufficiency} testId="sufficiency">
          <p className="text-sm text-[var(--color-muted)]">{r.sufficiencyExplainer}</p>
          {overview.current_sufficiency ? (
            <p className="text-sm" data-testid="current-sufficiency">
              {r.current}: <Badge tone="good">{overview.current_sufficiency.result}</Badge>{" "}
              <span dir="auto">{overview.current_sufficiency.rationale}</span>
            </p>
          ) : null}
          <ActionForm action={assessSufficiency} submitLabel={r.record} pendingLabel={dict.ui.saving} testId="sufficiency-form">
            {ids}
            <Field label={r.result}>
              <Select name="result" defaultValue="INSUFFICIENT_EVIDENCE">
                {SufficiencyResultValues.map((v) => (
                  <option key={v}>{v}</option>
                ))}
              </Select>
            </Field>
            <div className="grid gap-3 sm:grid-cols-2">
              {CONSIDERATIONS.map((k) => (
                <Field key={k} label={r.considerations[k] ?? k}>
                  <TextArea name={k} rows={2} required />
                </Field>
              ))}
            </div>
            <Field label={r.rationale}>
              <TextArea name="rationale" rows={2} required />
            </Field>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" name="recommend_experiment" />
              {r.recommendExperiment}
            </label>
          </ActionForm>
          {overview.sufficiency_history.length > 1 ? (
            <div>
              <h3 className="text-sm font-semibold">{r.history}</h3>
              <ul className="text-sm">
                {overview.sufficiency_history.slice(1).map((s) => (
                  <li key={s.id}>
                    <Badge>{s.result}</Badge> <span dir="auto">{s.rationale}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </Card>
      </div>
    </AppShell>
  );
}
