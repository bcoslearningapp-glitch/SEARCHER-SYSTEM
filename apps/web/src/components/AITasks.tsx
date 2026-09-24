import { launchAITask } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { AutoRefresh } from "@/components/AutoRefresh";
import { Badge, Empty } from "@/components/fields";
import type { AIStrings } from "@/lib/i18n-ai";
import type { AIProfile, Job } from "@/lib/types";

type Launcher = { task: string; label: string; targetType?: string; targetId?: string };

const ACTIVE = new Set(["QUEUED", "RUNNING"]);

function tone(state: Job["state"]): "neutral" | "good" | "warn" {
  if (state === "SUCCEEDED") return "good";
  if (state === "FAILED" || state === "CANCELLED") return "warn";
  return "neutral";
}

/** Launch AI tasks and follow their durable status (FR-ORCH-005). Proposals are reviewed elsewhere on the page. */
export function AITasks({
  ai,
  projectId,
  profiles,
  jobs,
  launchers,
  explainer,
}: {
  ai: AIStrings;
  projectId: string;
  profiles: AIProfile[] | null;
  jobs: Job[] | null;
  launchers: Launcher[];
  explainer?: string;
}) {
  const available = (profiles ?? []).some((p) => p.configured);
  const list = jobs ?? [];
  return (
    <div className="space-y-3" data-testid="ai-tasks">
      <AutoRefresh active={list.some((j) => ACTIVE.has(j.state))} />
      <p className="text-sm text-[var(--color-muted)]">{explainer ?? ai.explainer}</p>
      {available ? (
        <div className="flex flex-wrap gap-3">
          {launchers.map((l) => (
            <ActionForm key={l.task} action={launchAITask} submitLabel={l.label} pendingLabel={ai.launching} successMessage={ai.queued}>
              <input type="hidden" name="project_id" value={projectId} />
              <input type="hidden" name="task" value={l.task} />
              {l.targetType ? <input type="hidden" name="target_type" value={l.targetType} /> : null}
              {l.targetId ? <input type="hidden" name="target_id" value={l.targetId} /> : null}
            </ActionForm>
          ))}
        </div>
      ) : (
        <p role="note" className="text-sm text-amber-800 dark:text-amber-300" data-testid="ai-unavailable">
          {ai.unavailable}
        </p>
      )}
      <h3 className="text-sm font-semibold">{ai.tasks}</h3>
      {list.length ? (
        <ul className="space-y-2 text-sm" data-testid="ai-task-list">
          {list.map((job) => (
            <li key={job.id} className="rounded-md border border-[var(--color-border)] p-2" data-testid="ai-task">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium">{ai.taskNames[job.kind] ?? job.kind}</span>
                <Badge tone={tone(job.state)}>{job.state}</Badge>
                {ACTIVE.has(job.state) ? <span className="text-[var(--color-muted)]">{ai.working}</span> : null}
                {job.failure_kind ? <Badge tone="warn">{job.failure_kind}</Badge> : null}
              </div>
              {job.failure_kind === "PROVIDER_ERROR" ? <p className="mt-1">{ai.providerFailure}</p> : null}
              {job.failure_kind === "STOPPED_RESOURCE_CONSTRAINT" ? <p className="mt-1">{ai.budgetStop}</p> : null}
              {job.error && job.failure_kind !== "PROVIDER_ERROR" ? (
                <p className="mt-1 text-[var(--color-muted)]" dir="auto">
                  {job.error}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      ) : (
        <Empty>{ai.noTasks}</Empty>
      )}
    </div>
  );
}
