
import { deleteWorkspaceStaging, stageInWorkspace } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty, Field, TextInput } from "@/components/fields";
import { ProjectHeader } from "@/components/ProjectHeader";
import { getDictionary } from "@/lib/i18n";
import type { WorkspaceStrings } from "@/lib/i18n-workspace";
import { load, loadEntity } from "@/lib/load";
import { resolveProjectParams, type ProjectParams } from "@/lib/locale-params";
import type { Claim, EvidenceMap, Hypothesis, Output, Project, Staging, WorkspaceInfo } from "@/lib/types";

export const dynamic = "force-dynamic";

type Choice = { kind: keyof WorkspaceStrings["kinds"]; id: string; label: string };

const TONE = { ACTIVE: "good", BLOCKED: "warn", DELETED: "neutral", EXPIRED: "neutral" } as const;

/** Selective cloud workspace and its disclosure manifest (PRD §56). */
export default async function WorkspacePage(props: ProjectParams) {
  const { locale, projectId } = await resolveProjectParams(props);
  const dict = getDictionary(locale);
  const t = dict.workspace;
  const base = `/api/v1/projects/${projectId}`;
  const project = await loadEntity<Project>(base);
  const [info, stagings, claims, hypotheses, outputs] = await Promise.all([
    load<WorkspaceInfo>("/api/v1/workspace"),
    load<Staging[]>(`${base}/workspace/stagings`),
    load<Claim[]>(`${base}/claims`),
    load<Hypothesis[]>(`${base}/hypotheses`),
    load<Output[]>(`${base}/outputs`),
  ]);
  const maps = await Promise.all((claims ?? []).map((c) => load<EvidenceMap>(`${base}/evidence-map/CLAIM/${c.id}`)));
  const excerpts = new Map<string, string>();
  for (const map of maps) {
    for (const item of Object.values(map?.by_role ?? {}).flat()) excerpts.set(item.excerpt_id, item.finding);
  }
  const choices: Choice[] = [
    ...[...excerpts].map(([id, finding]) => ({ kind: "SourceExcerpt" as const, id, label: finding })),
    ...(claims ?? []).map((c) => ({ kind: "Claim" as const, id: c.id, label: c.statement })),
    ...(hypotheses ?? []).map((h) => ({ kind: "Hypothesis" as const, id: h.id, label: h.content.statement })),
    ...(outputs ?? []).map((o) => ({ kind: "OutputVersion" as const, id: o.latest.id, label: `${o.title} v${o.current_version}` })),
  ];

  return (
    <AppShell locale={locale} active="outputs">
      <div className="space-y-6">
        <ProjectHeader project={project} dict={dict} locale={locale} active="workspace" />
        <p className="text-sm text-[var(--color-muted)]">{t.explainer}</p>
        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <Card title={t.manifest} testId="disclosure-manifest">
            {stagings?.length ? (
              <ul className="space-y-4 text-sm">
                {stagings.map((s) => (
                  <li key={s.id} className="space-y-1" data-testid="staging-row">
                    <div className="flex flex-wrap items-center gap-2">
                      <span data-testid="staging-status">
                        <Badge tone={TONE[s.status]}>{s.status}</Badge>
                      </span>
                      <Badge>{s.sensitivity}</Badge>
                      <span dir="auto" className="font-medium">
                        {s.purpose}
                      </span>
                    </div>
                    <p className="text-[var(--color-muted)]">
                      {t.policy}: {s.policy_decision.reason}
                      {s.expires_at ? ` · ${t.expires}: ${new Date(s.expires_at).toLocaleString(locale)}` : ""}
                      {s.delete_reason ? ` · ${s.delete_reason}` : ""}
                    </p>
                    <ul className="ms-4 list-disc">
                      {s.items.map((i) => (
                        <li key={`${i.entity_type}:${i.entity_id}`} data-testid="staged-item">
                          {t.kinds[i.entity_type as Choice["kind"]] ?? i.entity_type} · <code dir="ltr">{i.sha256.slice(0, 12)}</code> ·{" "}
                          {i.byte_size} B
                        </li>
                      ))}
                    </ul>
                    {s.status === "ACTIVE" ? (
                      <ActionForm action={deleteWorkspaceStaging} submitLabel={t.delete} pendingLabel={t.deleting} className="flex flex-wrap items-end gap-2">
                        <input type="hidden" name="project_id" value={projectId} />
                        <input type="hidden" name="staging_id" value={s.id} />
                        <Field label={t.deleteReason}>
                          <TextInput name="reason" required minLength={3} />
                        </Field>
                      </ActionForm>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>{t.noStagings}</Empty>
            )}
          </Card>
          <Card title={t.stageTitle} testId="stage-selection">
            {!info?.enabled ? (
              <Empty>{t.notConfigured}</Empty>
            ) : choices.length === 0 ? (
              <Empty>{t.nothingToSelect}</Empty>
            ) : (
              <ActionForm action={stageInWorkspace} submitLabel={t.stage} pendingLabel={t.staging}>
                <input type="hidden" name="project_id" value={projectId} />
                <p className="text-sm">
                  {t.adapter}: <Badge>{info.adapter}</Badge>
                </p>
                <Field label={t.purpose}>
                  <TextInput name="purpose" required minLength={3} />
                </Field>
                <Field label={t.ttl}>
                  <TextInput name="ttl_hours" type="number" min={1} max={info.max_ttl_hours} defaultValue={info.default_ttl_hours} />
                </Field>
                <fieldset className="space-y-1 text-sm">
                  <legend className="font-medium">{t.select}</legend>
                  {choices.map((c) => (
                    <label key={`${c.kind}:${c.id}`} className="flex items-start gap-2">
                      <input type="checkbox" name="items" value={`${c.kind}:${c.id}`} />
                      <span dir="auto">
                        <Badge>{t.kinds[c.kind]}</Badge> {c.label}
                      </span>
                    </label>
                  ))}
                </fieldset>
              </ActionForm>
            )}
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
