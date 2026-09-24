import { notFound } from "next/navigation";

import {
  assessHumanImpact,
  recordInterpretation,
  recordObservation,
  recordResult,
  transitionExperiment,
  updateProtocol,
} from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, Select, TextArea, TextInput } from "@/components/fields";
import { ProjectHeader } from "@/components/ProjectHeader";
import {
  HumanImpactDimensionValues,
  HumanImpactFindingValues,
  InterpretationOutcomeValues,
  type ExperimentState,
} from "@/lib/contracts/enums";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveLocale } from "@/lib/locale-params";
import type { DesignHypothesis, Experiment, ExperimentRecord, Project } from "@/lib/types";

export const dynamic = "force-dynamic";

type Props = { params: Promise<{ locale: string; projectId: string; experimentId: string }> };

const PROTOCOL_FIELDS = ["method", "sample", "duration", "data_collected", "analysis_plan", "success_criteria"] as const;

/** Offered moves only; the API enforces the workflow and the Experiment Readiness Gate. */
const FORWARD: Partial<Record<ExperimentState, ExperimentState[]>> = {
  PROPOSED: ["PROTOCOL_DEFINED"],
  PROTOCOL_DEFINED: ["RISK_REVIEW", "APPROVED"],
  RISK_REVIEW: ["APPROVED", "PROTOCOL_DEFINED"],
  APPROVED: ["RUNNING"],
  RUNNING: ["DATA_COLLECTION_COMPLETE"],
  DATA_COLLECTION_COMPLETE: ["ANALYSIS"],
  ANALYSIS: ["INTERPRETED"],
  INTERPRETED: ["CLOSED"],
};
const TERMINAL = new Set<ExperimentState>(["CLOSED", "ABORTED", "INVALIDATED"]);

function moves(e: Experiment): ExperimentState[] {
  if (TERMINAL.has(e.state)) return [];
  if (e.state === "PAUSED") return [...(e.paused_from ? [e.paused_from] : []), "ABORTED", "INVALIDATED"];
  const forward = (FORWARD[e.state] ?? []).filter((t) => !(e.affects_people && e.state === "PROTOCOL_DEFINED" && t === "APPROVED"));
  const pause: ExperimentState[] = ["PROPOSED", "INTERPRETED"].includes(e.state) ? [] : ["PAUSED"];
  return [...forward, ...pause, "ABORTED", "INVALIDATED"];
}

export default async function ExperimentPage(props: Props) {
  const { projectId, experimentId } = await props.params;
  const locale = await resolveLocale({ params: props.params });
  if (!/^[0-9a-f-]{36}$/i.test(projectId) || !/^[0-9a-f-]{36}$/i.test(experimentId)) notFound();
  const dict = getDictionary(locale);
  const x = dict.experiments;
  const base = `/api/v1/projects/${projectId}`;
  const [project, experiment, record] = await Promise.all([
    load<Project>(base),
    load<Experiment>(`${base}/experiments/${experimentId}`),
    load<ExperimentRecord>(`${base}/experiments/${experimentId}/record`),
  ]);
  if (project === null || experiment === null) notFound();
  const dh = await load<DesignHypothesis>(`${base}/design-hypotheses/${experiment.design_hypothesis_id}`);
  const data = record ?? { human_impact: [], observations: [], results: [], interpretations: [] };
  const hidden = (
    <>
      <input type="hidden" name="project_id" value={projectId} />
      <input type="hidden" name="experiment_id" value={experimentId} />
    </>
  );
  const editableProtocol = ["PROPOSED", "PROTOCOL_DEFINED"].includes(experiment.state);
  const reviewOpen = !TERMINAL.has(experiment.state);

  return (
    <AppShell locale={locale} active="lab">
      <div className="space-y-6">
        <ProjectHeader project={project} dict={dict} locale={locale} active="experiments" />
        <div className="flex flex-wrap items-center gap-2">
          <h2 dir="auto" className="text-xl font-semibold">{experiment.title}</h2>
          <span data-testid="experiment-state">
            <Badge tone={TERMINAL.has(experiment.state) && experiment.state !== "CLOSED" ? "warn" : "neutral"}>{experiment.state}</Badge>
          </span>
          {experiment.affects_people ? <Badge tone="warn">{x.affectsPeople}</Badge> : null}
        </div>
        {dh ? (
          <p dir="auto" className="text-sm">
            {x.designHypothesis}: {dh.content.intervention} → {dh.content.expected_outcome} <Badge>{dh.epistemic_state}</Badge>
          </p>
        ) : null}
        {experiment.state === "INVALIDATED" ? (
          <p className="rounded-md border border-amber-500/50 p-2 text-sm" data-testid="invalidated">
            {x.invalidated} <span dir="auto">{experiment.invalidation_reason}</span>
          </p>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-2">
          <Card title={x.state} testId="experiment-workflow">
            {moves(experiment).length ? (
              <ActionForm action={transitionExperiment} submitLabel={x.move} pendingLabel={x.saving} testId="transition-form">
                {hidden}
                <Field label={x.moveTo}>
                  <Select name="target">
                    {moves(experiment).map((t) => (
                      <option key={t}>{t}</option>
                    ))}
                  </Select>
                </Field>
                <Field label={x.reason}>
                  <TextInput name="reason" />
                </Field>
                <label className="flex items-center gap-2 text-xs">
                  <input type="checkbox" name="acknowledge_reservations" />
                  {x.acknowledge}
                </label>
              </ActionForm>
            ) : null}
            <p className="font-medium">{x.history}</p>
            <ol className="list-decimal ps-5 text-sm">
              {experiment.transitions.map((t, i) => (
                <li key={i}>
                  {t.from_state} → {t.to_state}
                  {t.reason ? <span dir="auto"> — {t.reason}</span> : null}
                </li>
              ))}
            </ol>
          </Card>

          <Card title={x.protocol} testId="protocol">
            {editableProtocol ? (
              <ActionForm action={updateProtocol} submitLabel={x.saveProtocol} pendingLabel={x.saving}>
                {hidden}
                {PROTOCOL_FIELDS.map((f) => (
                  <Field key={f} label={x.protocolFields[f]}>
                    <TextInput name={f} defaultValue={experiment.protocol[f]} />
                  </Field>
                ))}
              </ActionForm>
            ) : (
              <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
                {PROTOCOL_FIELDS.map((f) => (
                  <div key={f} className="contents">
                    <dt className="font-medium">{x.protocolFields[f]}</dt>
                    <dd dir="auto">{experiment.protocol[f] || "—"}</dd>
                  </div>
                ))}
              </dl>
            )}
          </Card>

          <Card title={x.humanImpact} testId="human-impact">
            <p className="text-sm text-[var(--color-muted)]">{x.humanImpactExplainer}</p>
            {data.human_impact.length ? (
              <ul className="space-y-1 text-sm">
                {data.human_impact.map((a) => (
                  <li key={a.id} className="flex flex-wrap gap-2">
                    <Badge>{a.dimension}</Badge>
                    <Badge tone={a.finding === "ADDRESSED" || a.finding === "NOT_APPLICABLE" ? "good" : "warn"}>{a.finding}</Badge>
                    <span dir="auto">{a.note}</span>
                    {a.external_authority ? <span dir="auto">({a.external_authority})</span> : null}
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{x.none}</Empty>
            )}
            {reviewOpen ? (
              <ActionForm action={assessHumanImpact} submitLabel={x.record} pendingLabel={x.saving} testId="impact-form">
                {hidden}
                <Field label={x.dimension}>
                  <Select name="dimension">
                    {HumanImpactDimensionValues.map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </Select>
                </Field>
                <Field label={x.finding}>
                  <Select name="finding" defaultValue="ADDRESSED">
                    {HumanImpactFindingValues.map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </Select>
                </Field>
                <Field label={x.note}>
                  <TextInput name="note" required />
                </Field>
                <Field label={x.externalAuthority}>
                  <TextInput name="external_authority" />
                </Field>
              </ActionForm>
            ) : null}
          </Card>

          <Card title={x.observations} testId="observations">
            <p className="text-sm text-[var(--color-muted)]">{x.observationExplainer}</p>
            {data.observations.length ? (
              <ul className="list-disc ps-5 text-sm">
                {data.observations.map((o) => (
                  <li key={o.id} dir="auto">
                    {o.description}
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{x.none}</Empty>
            )}
            {experiment.state === "RUNNING" ? (
              <ActionForm action={recordObservation} submitLabel={x.record} pendingLabel={x.saving} testId="observation-form">
                {hidden}
                <Field label={x.description}>
                  <TextArea name="description" rows={2} required />
                </Field>
                <Field label={x.observedAt}>
                  <TextInput name="observed_at" type="datetime-local" />
                </Field>
              </ActionForm>
            ) : null}
          </Card>

          <Card title={x.results} testId="results">
            <p className="text-sm text-[var(--color-muted)]">{x.resultExplainer}</p>
            {data.results.length ? (
              <ul className="list-disc ps-5 text-sm">
                {data.results.map((r) => (
                  <li key={r.id} dir="auto">
                    {r.method}: {r.summary}
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{x.none}</Empty>
            )}
            {experiment.state === "ANALYSIS" && data.observations.length ? (
              <ActionForm action={recordResult} submitLabel={x.record} pendingLabel={x.saving} testId="result-form">
                {hidden}
                <fieldset className="text-sm">
                  <legend className="font-medium">{x.fromObservations}</legend>
                  {data.observations.map((o) => (
                    <label key={o.id} className="flex items-center gap-2">
                      <input type="checkbox" name="observation_ids" value={o.id} defaultChecked />
                      <span dir="auto">{o.description}</span>
                    </label>
                  ))}
                </fieldset>
                <Field label={x.method}>
                  <TextInput name="method" required />
                </Field>
                <Field label={x.summary}>
                  <TextArea name="summary" rows={2} required />
                </Field>
              </ActionForm>
            ) : null}
          </Card>

          <Card title={x.interpretations} testId="interpretations">
            <p className="text-sm text-[var(--color-muted)]">{x.interpretationExplainer}</p>
            {data.interpretations.length ? (
              <ul className="space-y-1 text-sm">
                {data.interpretations.map((i) => (
                  <li key={i.id}>
                    <Badge>{i.outcome}</Badge> <span dir="auto">{i.statement}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{x.none}</Empty>
            )}
            {experiment.state === "ANALYSIS" && data.results.length ? (
              <ActionForm action={recordInterpretation} submitLabel={x.record} pendingLabel={x.saving} testId="interpretation-form">
                {hidden}
                <fieldset className="text-sm">
                  <legend className="font-medium">{x.fromResults}</legend>
                  {data.results.map((r) => (
                    <label key={r.id} className="flex items-center gap-2">
                      <input type="checkbox" name="result_ids" value={r.id} defaultChecked />
                      <span dir="auto">{r.summary}</span>
                    </label>
                  ))}
                </fieldset>
                <Field label={x.outcome}>
                  <Select name="outcome">
                    {InterpretationOutcomeValues.map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </Select>
                </Field>
                <Field label={x.statement}>
                  <TextArea name="statement" rows={2} required />
                </Field>
                <Field label={x.limitations}>
                  <TextInput name="limitations" />
                </Field>
              </ActionForm>
            ) : null}
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
