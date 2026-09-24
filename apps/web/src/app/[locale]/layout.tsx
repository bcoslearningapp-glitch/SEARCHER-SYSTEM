import type { Metadata } from "next";
import type { ReactNode } from "react";

import "@fontsource/amiri-quran/arabic-400.css";
import "../globals.css";

import { LOCALES, dirFor, getDictionary } from "@/lib/i18n";
import { resolveLocale, type LocaleParams } from "@/lib/locale-params";

export function generateStaticParams() {
  return LOCALES.map((locale) => ({ locale }));
}

export async function generateMetadata(props: LocaleParams): Promise<Metadata> {
  const locale = await resolveLocale(props);
  return { title: getDictionary(locale).productName };
}

export default async function LocaleLayout(props: LocaleParams & { children: ReactNode }) {
  const locale = await resolveLocale(props);
  return (
    <html lang={locale} dir={dirFor(locale)}>
      <body>{props.children}</body>
    </html>
  );
}
