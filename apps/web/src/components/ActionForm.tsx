"use client";

import { useActionState, type ReactNode } from "react";

import { INITIAL_RESULT, type ActionResult } from "@/lib/form";

type Props = {
  action: (state: ActionResult, form: FormData) => Promise<ActionResult>;
  submitLabel: string;
  pendingLabel: string;
  children: ReactNode;
  className?: string;
  testId?: string;
  successMessage?: string;
};

/** A form bound to a server action, with pending, error and success states. */
export function ActionForm({ action, submitLabel, pendingLabel, children, className, testId, successMessage }: Props) {
  const [state, formAction, pending] = useActionState(action, INITIAL_RESULT);
  const findings = (state.details?.findings as { message: string }[] | undefined) ?? [];
  return (
    <form action={formAction} className={className ?? "space-y-3"} data-testid={testId}>
      {children}
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-sm font-medium text-white disabled:opacity-60 dark:text-black"
        >
          {pending ? pendingLabel : submitLabel}
        </button>
        {state.ok && successMessage ? (
          <span role="status" className="text-sm text-emerald-700 dark:text-emerald-400">
            {successMessage}
          </span>
        ) : null}
      </div>
      {!state.ok && state.message ? (
        <div role="alert" className="rounded-md border border-amber-500/50 bg-amber-50 p-2 text-sm text-amber-900 dark:bg-amber-950 dark:text-amber-200">
          <p>{state.message}</p>
          {findings.length ? (
            <ul className="mt-1 list-disc ps-5">
              {findings.map((f) => (
                <li key={f.message}>{f.message}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </form>
  );
}
