import type { ReadinessResult } from "@/lib/api";
import type { Dictionary } from "@/lib/i18n";

type Props = { result: ReadinessResult; dict: Dictionary };

function Row({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4 py-1.5">
      <dt className="text-[var(--color-muted)]">{label}</dt>
      <dd className="flex items-center gap-2 font-medium">
        <span
          aria-hidden="true"
          className={`inline-block h-2 w-2 rounded-full ${ok ? "bg-emerald-500" : "bg-amber-500"}`}
        />
        {value}
      </dd>
    </div>
  );
}

export function StatusPanel({ result, dict }: Props) {
  if (!result.reachable) {
    return (
      <section aria-labelledby="system-status" role="status" className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
        <h2 id="system-status" className="mb-2 text-sm font-semibold">
          {dict.systemStatus}
        </h2>
        <p className="text-amber-600">{dict.status.unreachable}</p>
      </section>
    );
  }
  const { readiness } = result;
  const componentLabel = (ok: boolean) => (ok ? dict.status.ready : dict.status.unavailable);
  return (
    <section aria-labelledby="system-status" role="status" className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      <h2 id="system-status" className="mb-2 text-sm font-semibold">
        {dict.systemStatus}: <span data-testid="overall-status">{dict.status[readiness.status]}</span>
      </h2>
      <dl className="text-sm">
        <Row label={dict.components.database} value={componentLabel(readiness.database === "ok")} ok={readiness.database === "ok"} />
        <Row label={dict.components.queue} value={componentLabel(readiness.queue === "ok")} ok={readiness.queue === "ok"} />
        <Row
          label={dict.components.aiProviders}
          value={readiness.ai_providers_configured.length ? readiness.ai_providers_configured.join(", ") : dict.components.none}
          ok={readiness.ai_providers_configured.length > 0}
        />
      </dl>
    </section>
  );
}
