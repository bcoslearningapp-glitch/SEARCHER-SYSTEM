import { expect, test } from "@playwright/test";

/**
 * Foundational library: import a KFGQPC-format Qur'an dataset, stage, approve, look up (ADR-009).
 * The fixture is SYNTHETIC placeholder text in the KFGQPC JSON shape, never Qur'anic text.
 * Approval retires any approved Qur'an text, so that step only runs on disposable stacks (CI).
 */

const disposable = process.env.E2E_DISPOSABLE_STACK === "1";

function syntheticKfgqpc(tag: string): Buffer {
  const record = (sura: number, aya: number) => ({
    id: aya,
    jozz: 1,
    page: "1",
    sura_no: sura,
    sura_name_en: `Placeholder ${sura}`,
    sura_name_ar: `سورة تجريبية ${sura} `,
    line_start: 1,
    line_end: 1,
    aya_no: aya,
    aya_text: `PLACEHOLDER-${tag}-${sura}-${aya} نص تجريبي `,
  });
  const records = [record(1, 1), record(1, 2), record(2, 1)];
  return Buffer.from("﻿" + JSON.stringify(records), "utf-8");
}

test("foundational library: import KFGQPC dataset -> staged, not served -> approve -> exact lookup", async ({ page }) => {
  const tag = `${Date.now()}`;
  const version = `Synthetic KFGQPC-format fixture ${tag}`;
  await page.goto("/en/library");
  await page.getByRole("link", { name: "Foundational library (Qur'an text)" }).click();
  await expect(page).toHaveURL(/\/en\/library\/foundational$/);

  const form = page.getByTestId("import-quran");
  await form.getByLabel("Edition and version", { exact: true }).fill(version);
  await form.getByLabel("Dataset file", { exact: true }).setInputFiles({
    name: "synthetic_kfgqpc.json",
    mimeType: "application/json",
    buffer: syntheticKfgqpc(tag),
  });
  await form.getByRole("button", { name: "Import (staged, not yet served)" }).click();
  await expect(form.getByRole("status")).toHaveText("Imported and staged. Review it, then approve.");

  const staged = page.getByTestId("foundational-source").filter({ hasText: version });
  await expect(staged).toContainText("STAGED");
  await expect(staged).toContainText("2 Surah · 3 Ayah · kfgqpc-json");

  test.skip(!disposable, "approval would retire the approved Qur'an text on a non-disposable stack");
  await staged.getByLabel("Reason for approval", { exact: true }).fill("E2E synthetic fixture");
  await staged.getByRole("button", { name: "Approve" }).click();
  await expect(page.getByTestId("foundational-source").filter({ hasText: version })).toContainText("APPROVED");

  await page.goto("/en/library/foundational?surah=1&ayah=1&to=2");
  const text = page.getByTestId("ayah-text");
  await expect(text).toHaveAttribute("dir", "rtl");
  await expect(text).toContainText(`PLACEHOLDER-${tag}-1-1 نص تجريبي`);
  await expect(text).toContainText(`PLACEHOLDER-${tag}-1-2`);
  await expect(page.getByTestId("ayat")).toContainText(version);
});
