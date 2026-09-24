import Link from "next/link";
import type { ReactNode } from "react";

import { LOCALES, SPACES, getDictionary, type Locale, type Space } from "@/lib/i18n";

type Props = { locale: Locale; active: Space; children: ReactNode };

function hrefFor(locale: Locale, space: Space): string {
  return space === "desk" ? `/${locale}` : `/${locale}/${space}`;
}

export function AppShell({ locale, active, children }: Props) {
  const dict = getDictionary(locale);
  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <span className="font-semibold">{dict.productName}</span>
          <nav aria-label="Language" className="flex gap-2 text-sm">
            {LOCALES.map((l) => (
              <Link
                key={l}
                href={hrefFor(l, active)}
                hrefLang={l}
                aria-current={l === locale ? "true" : undefined}
                className={l === locale ? "font-semibold underline" : "text-[var(--color-muted)]"}
              >
                {getDictionary(l).languageName}
              </Link>
            ))}
          </nav>
        </div>
        <nav aria-label="Research spaces" className="mx-auto max-w-6xl px-4">
          <ul className="flex gap-1 overflow-x-auto">
            {SPACES.map((space) => (
              <li key={space}>
                <Link
                  href={hrefFor(locale, space)}
                  aria-current={space === active ? "page" : undefined}
                  className={`inline-block border-b-2 px-3 py-2 text-sm ${
                    space === active
                      ? "border-[var(--color-accent)] font-semibold"
                      : "border-transparent text-[var(--color-muted)] hover:text-[var(--color-text)]"
                  }`}
                >
                  {dict.spaces[space]}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
