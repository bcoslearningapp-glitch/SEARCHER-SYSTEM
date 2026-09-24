import type { Dictionary } from "@/lib/i18n";

export function LoadError({ dict }: { dict: Dictionary }) {
  return (
    <p role="alert" className="rounded-md border border-amber-500/50 p-4 text-amber-800 dark:text-amber-300">
      {dict.ui.loadError}
    </p>
  );
}
