import "server-only";

import { load } from "@/lib/load";
import type { Excerpt, Work } from "@/lib/types";

export type ExcerptOption = { id: string; label: string };

/** Source passages available to a project, for choosing evidence (evidence must cite a passage). */
export async function projectExcerpts(projectId: string): Promise<ExcerptOption[]> {
  const works = (await load<Work[]>(`/api/v1/sources?project_id=${projectId}`)) ?? [];
  const options: ExcerptOption[] = [];
  for (const work of works) {
    for (const edition of work.editions) {
      const excerpts = (await load<Excerpt[]>(`/api/v1/sources/editions/${edition.id}/excerpts`)) ?? [];
      for (const excerpt of excerpts) {
        const preview = excerpt.text.length > 60 ? `${excerpt.text.slice(0, 60)}…` : excerpt.text;
        options.push({ id: excerpt.id, label: `${work.title} — ${excerpt.location}: ${preview}` });
      }
    }
  }
  return options;
}
