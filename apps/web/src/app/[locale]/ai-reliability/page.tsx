import { AppShell } from "@/components/AppShell";
import { Badge, Card, Empty } from "@/components/fields";
import { LoadError } from "@/components/LoadError";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveLocale, type LocaleParams } from "@/lib/locale-params";
import type { Reliability } from "@/lib/types";

export const dynamic = "force-dynamic";

const pct = (value: number | null) => (value === null ? "—" : `${(value * 100).toFixed(1)}%`);

/** AI capability/reliability registry (PRD §52): observed behaviour and evaluation standing per model. */
export default async function ReliabilityPage(props: LocaleParams) {
  const locale = await resolveLocale(props);
  const dict = getDictionary(locale);
  const r = dict.reliability;
  const data = await load<Reliability>("/api/v1/ai/reliability");

  return (
    <AppShell locale={locale} active="desk">
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">{r.title}</h1>
        <p className="text-[var(--color-muted)]">{r.explainer}</p>
        {data === null ? <LoadError dict={dict} /> : null}

        <Card title={r.operational} testId="operational">
          {data?.operational.length ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-start text-[var(--color-muted)]">
                  <tr>
                    {[r.provider, r.model, r.task, r.calls, r.succeeded, r.invalid, r.refusals, r.unavailable, r.blocked, r.reliability, r.cost].map((h) => (
                      <th key={h} className="px-2 py-1 text-start font-medium">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.operational.map((row) => (
                    <tr key={`${row.provider}-${row.model}-${row.task}`} className="border-t border-[var(--color-border)]">
                      <td className="px-2 py-1">{row.provider}</td>
                      <td className="px-2 py-1 font-mono text-xs">{row.model}</td>
                      <td className="px-2 py-1">{row.task}</td>
                      <td className="px-2 py-1">{row.calls}</td>
                      <td className="px-2 py-1">{row.succeeded}</td>
                      <td className="px-2 py-1">{row.invalid_output}</td>
                      <td className="px-2 py-1">{row.refusals}</td>
                      <td className="px-2 py-1">{row.unavailable}</td>
                      <td className="px-2 py-1">{row.blocked}</td>
                      <td className="px-2 py-1">{pct(row.structured_output_reliability)}</td>
                      <td className="px-2 py-1">{Number(row.estimated_cost_usd).toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>{r.noCalls}</Empty>
          )}
        </Card>

        <Card title={r.models} testId="models">
          {data?.models.length ? (
            <ul className="space-y-4 text-sm">
              {data.models.map((m) => (
                <li key={`${m.provider}-${m.model}`} className="space-y-2 rounded-md border border-[var(--color-border)] p-3" data-testid="model-standing">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge>{m.provider}</Badge>
                    <span className="font-mono">{m.model}</span>
                  </div>
                  {m.blocking_failures.length + m.blocking_unevaluated.length > 0 ? (
                    <p className="text-amber-800 dark:text-amber-300">
                      {r.blockingGaps}: {[...m.blocking_failures, ...m.blocking_unevaluated].join(", ")}
                    </p>
                  ) : null}
                  <ul className="grid gap-1 sm:grid-cols-2">
                    {data.dimensions.map((d) => {
                      const latest = m.latest[d.key];
                      return (
                        <li key={d.key} className="flex flex-wrap items-center gap-2">
                          <span>{d.label}</span>
                          {latest ? (
                            <Badge tone={latest.passed ? "good" : "warn"}>
                              {latest.score} {latest.passed ? r.passed : r.failed}
                            </Badge>
                          ) : (
                            <Badge>{r.notEvaluated}</Badge>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                </li>
              ))}
            </ul>
          ) : (
            <Empty>{r.noEvaluations}</Empty>
          )}
        </Card>

        <Card title={r.thresholds} testId="thresholds">
          <ul className="space-y-1 text-sm">
            {(data?.dimensions ?? []).map((d) => (
              <li key={d.key}>
                {d.label}: {d.comparator} {d.threshold} {d.blocking ? <Badge tone="warn">{r.blocking}</Badge> : null}
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </AppShell>
  );
}
