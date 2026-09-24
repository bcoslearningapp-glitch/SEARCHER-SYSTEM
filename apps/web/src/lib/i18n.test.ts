import { describe, expect, it } from "vitest";

import { LOCALES, SPACES, dirFor, getDictionary, isLocale } from "./i18n";

function keyPaths(value: unknown, prefix = ""): string[] {
  if (typeof value !== "object" || value === null) return [prefix];
  return Object.entries(value).flatMap(([k, v]) => keyPaths(v, prefix ? `${prefix}.${k}` : k));
}

describe("i18n", () => {
  it("renders Arabic right-to-left and Latin-script locales left-to-right", () => {
    expect(dirFor("ar")).toBe("rtl");
    expect(dirFor("en")).toBe("ltr");
    expect(dirFor("fr")).toBe("ltr");
  });

  it("has identical, non-empty keys for every locale", () => {
    const reference = keyPaths(getDictionary("en")).sort();
    for (const locale of LOCALES) {
      const dict = getDictionary(locale);
      expect(keyPaths(dict).sort()).toEqual(reference);
      for (const space of SPACES) expect(dict.spaces[space].length).toBeGreaterThan(0);
    }
  });

  it("rejects unsupported locales", () => {
    expect(isLocale("de")).toBe(false);
    expect(isLocale("ar")).toBe(true);
  });
});

describe("workflow UI strings", () => {
  it("translates every Arabic workflow string rather than falling back to English", () => {
    const en = getDictionary("en").ui;
    const ar = getDictionary("ar").ui;
    const untranslated = (Object.keys(en) as (keyof typeof en)[]).filter(
      (key) => typeof en[key] === "string" && en[key] === ar[key] && key !== "page",
    );
    expect(untranslated).toEqual([]);
  });
});
