import Link from "next/link";

import type { Dictionary } from "@/lib/i18n";

export const PAGE_SIZE = 25;

/** 1-based page number from a search param; anything invalid is page 1. */
export function pageNumber(value: string | undefined): number {
  const n = Number(value);
  return Number.isInteger(n) && n > 1 ? n : 1;
}

/** Query for one page. It asks for one extra item to learn whether a next page exists without a count query. */
export function pageQuery(page: number): string {
  return `limit=${PAGE_SIZE + 1}&offset=${(page - 1) * PAGE_SIZE}`;
}

/** Split a limit+1 result into the page's items and whether more follow. */
export function pageSlice<T>(items: T[]): { items: T[]; hasNext: boolean } {
  return { items: items.slice(0, PAGE_SIZE), hasNext: items.length > PAGE_SIZE };
}

type Props = {
  page: number;
  hasNext: boolean;
  href: (page: number) => string;
  dict: Dictionary;
};

export function Pager({ page, hasNext, href, dict }: Props) {
  if (page === 1 && !hasNext) return null;
  const ui = dict.ui;
  return (
    <nav aria-label={ui.pagination} className="flex items-center gap-3 pt-2 text-sm" data-testid="pager">
      {page > 1 ? (
        <Link href={href(page - 1)} rel="prev" className="underline">
          {ui.previousPage}
        </Link>
      ) : null}
      <span className="text-[var(--color-muted)]">
        {ui.pageLabel} {page}
      </span>
      {hasNext ? (
        <Link href={href(page + 1)} rel="next" className="underline" data-testid="pager-next">
          {ui.nextPage}
        </Link>
      ) : null}
    </nav>
  );
}
