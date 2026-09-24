import Link from "next/link";

import { AppShell } from "@/components/AppShell";
import { CatalogForm } from "@/components/CatalogForm";
import { Card, Empty, TextInput } from "@/components/fields";
import { LoadError } from "@/components/LoadError";
import { SourceList } from "@/components/SourceList";
import { getDictionary } from "@/lib/i18n";
import { load } from "@/lib/load";
import { resolveLocale, type LocaleParams } from "@/lib/locale-params";
import type { Project, SearchResponse, Work } from "@/lib/types";

export const dynamic = "force-dynamic";

type Props = LocaleParams & { searchParams: Promise<{ q?: string }> };

export default async function LibraryPage(props: Props) {
  const locale = await resolveLocale(props);
  const { q } = await props.searchParams;
  const query = (q ?? "").trim();
  const dict = getDictionary(locale);
  const ui = dict.ui;
  const [works, projects, results] = await Promise.all([
    load<Work[]>("/api/v1/sources"),
    load<Project[]>("/api/v1/projects"),
    query ? load<SearchResponse>(`/api/v1/sources/search?q=${encodeURIComponent(query)}`) : Promise.resolve(null),
  ]);
  return (
    <AppShell locale={locale} active="library">
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">{dict.spaces.library}</h1>
        <p className="text-[var(--color-muted)]">{dict.spaceDescriptions.library}</p>
        <p>
          <Link href={`/${locale}/library/foundational`} className="text-sm underline">
            {dict.foundational.link}
          </Link>
        </p>
        <Card title={ui.search} testId="search">
          <form method="get" className="flex flex-wrap gap-2" role="search">
            <div className="grow">
              <TextInput name="q" defaultValue={query} placeholder={ui.searchPlaceholder} aria-label={ui.search} />
            </div>
            <button type="submit" className="rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-sm font-medium text-white dark:text-black">
              {ui.search}
            </button>
          </form>
          {query && results === null ? <LoadError dict={dict} /> : null}
          {results ? (
            <div className="space-y-2" data-testid="search-results">
              <p className="text-xs text-[var(--color-muted)]">
                {ui.searchedScope}: {results.scope} ({results.searched_assets}). {ui.discoveryOnly}
              </p>
              {results.hits.length === 0 ? (
                <Empty>{ui.noResults}</Empty>
              ) : (
                <ul className="space-y-2 text-sm">
                  {results.hits.map((hit) => (
                    <li key={hit.chunk_id} className="rounded-md border border-[var(--color-border)] p-2" data-testid="search-hit">
                      <p dir="auto" className="font-medium">
                        {hit.work_title} — {ui.page} {hit.page_number}
                      </p>
                      {/* ts_headline marks matches with <b>; render as text to keep source content inert. */}
                      <p dir="auto">{hit.snippet.replaceAll("<b>", "").replaceAll("</b>", "")}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : null}
        </Card>
        <Card title={ui.catalogSource}>
          <CatalogForm dict={dict} />
        </Card>
        <Card title={ui.sources}>
          {works === null ? <LoadError dict={dict} /> : <SourceList works={works} dict={dict} projects={projects ?? []} />}
        </Card>
      </div>
    </AppShell>
  );
}
