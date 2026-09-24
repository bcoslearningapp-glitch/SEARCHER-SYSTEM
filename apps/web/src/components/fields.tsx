import { cloneElement, isValidElement, type ReactElement, type ReactNode } from "react";

const INPUT =
  "w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1.5 text-sm focus:outline-2 focus:outline-[var(--color-accent)]";

/**
 * Labelled control. The control's accessible name is exactly `label` (a wrapping
 * label would otherwise absorb hint text and a select's current option).
 */
export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  const control = isValidElement(children)
    ? cloneElement(children as ReactElement<{ "aria-label"?: string }>, { "aria-label": label })
    : children;
  return (
    <div className="space-y-1 text-sm">
      <label className="block space-y-1">
        <span className="font-medium" aria-hidden="true">
          {label}
        </span>
        {control}
      </label>
      {hint ? <p className="text-xs text-[var(--color-muted)]">{hint}</p> : null}
    </div>
  );
}

export function TextInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input dir="auto" {...props} className={INPUT} />;
}

export function TextArea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea dir="auto" rows={3} {...props} className={INPUT} />;
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={INPUT} />;
}

export function Card({ title, children, testId }: { title: string; children: ReactNode; testId?: string }) {
  return (
    <section
      className="space-y-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4"
      data-testid={testId}
      aria-label={title}
    >
      <h2 className="text-base font-semibold">{title}</h2>
      {children}
    </section>
  );
}

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "good" | "warn" }) {
  const tones = {
    neutral: "border-[var(--color-border)] text-[var(--color-muted)]",
    good: "border-emerald-500/50 text-emerald-700 dark:text-emerald-400",
    warn: "border-amber-500/50 text-amber-700 dark:text-amber-400",
  };
  return <span className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${tones[tone]}`}>{children}</span>;
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="text-sm text-[var(--color-muted)]">{children}</p>;
}
