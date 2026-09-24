import { notFound } from "next/navigation";

import { isLocale, type Locale } from "@/lib/i18n";

export type LocaleParams = { params: Promise<{ locale: string }> };

export async function resolveLocale({ params }: LocaleParams): Promise<Locale> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  return locale;
}

export type ProjectParams = { params: Promise<{ locale: string; projectId: string }> };

export async function resolveProjectParams({ params }: ProjectParams): Promise<{ locale: Locale; projectId: string }> {
  const { locale, projectId } = await params;
  if (!isLocale(locale) || !/^[0-9a-f-]{36}$/i.test(projectId)) notFound();
  return { locale, projectId };
}
