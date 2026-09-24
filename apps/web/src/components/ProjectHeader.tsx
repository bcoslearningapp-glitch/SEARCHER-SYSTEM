import Link from "next/link";

import { transitionProject } from "@/app/actions";
import { ActionForm } from "@/components/ActionForm";
import { Badge, Select } from "@/components/fields";
import type { Dictionary, Locale } from "@/lib/i18n";
import type { Project } from "@/lib/types";

const MANUAL_TARGETS = ["FRAMING", "ACTIVE_RESEARCH", "ON_HOLD", "FROZEN", "READY_TO_CLOSE"] as const;

export function ProjectHeader({ project, dict, locale, active }: { project: Project; dict: Dictionary; locale: Locale; active: "desk" | "sources" }) {
  const ui = dict.ui;
  const base = `/${locale}/projects/${project.id}`;
  return (
    <header className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <h1 dir="auto" className="text-2xl font-semibold">{project.title}</h1>
        <span className="flex gap-2">
          <span data-testid="project-status">
            <Badge tone={project.status === "ACTIVE_RESEARCH" ? "good" : "neutral"}>{project.status}</Badge>
          </span>
          <Badge>{project.research_mode}</Badge>
          <Badge>{project.risk_level}</Badge>
        </span>
      </div>
      <p dir="auto" className="text-sm text-[var(--color-muted)]">{project.initial_input}</p>
      <nav aria-label="Project" className="flex gap-4 text-sm">
        <Link href={base} aria-current={active === "desk" ? "page" : undefined} className={active === "desk" ? "font-semibold underline" : "underline-offset-2 hover:underline"}>
          {dict.spaces.desk}
        </Link>
        <Link href={`${base}/sources`} aria-current={active === "sources" ? "page" : undefined} className={active === "sources" ? "font-semibold underline" : "underline-offset-2 hover:underline"}>
          {ui.sources}
        </Link>
      </nav>
      <ActionForm action={transitionProject} submitLabel={ui.moveTo} pendingLabel={ui.saving} className="flex flex-wrap items-end gap-2">
        <input type="hidden" name="project_id" value={project.id} />
        <label className="text-sm">
          <span className="sr-only">{ui.moveTo}</span>
          <Select name="target" defaultValue="">
            <option value="" disabled>
              {ui.moveTo}…
            </option>
            {MANUAL_TARGETS.filter((t) => t !== project.status).map((t) => (
              <option key={t}>{t}</option>
            ))}
          </Select>
        </label>
      </ActionForm>
    </header>
  );
}
