import { expect, test, type APIRequestContext } from "@playwright/test";

/** Phase 5 outputs (issues #43-#47, PRD §37, §45). */

const API_URL = process.env.API_URL ?? "http://localhost:8000";
const unique = () => `${Date.now()}-${Math.floor(Math.random() * 1e6)}`;
export const PASSAGE = "Mentoring declines sharply in the second year.";

async function post<T>(request: APIRequestContext, path: string, data: unknown): Promise<T> {
  const response = await request.post(`${API_URL}${path}`, { data });
  expect(response.ok(), `${path}: ${await response.text()}`).toBeTruthy();
  return (await response.json()) as T;
}

/** A project with one claim supported by an accepted, exact excerpt. */
export async function projectWithEvidence(request: APIRequestContext): Promise<{ projectId: string; claim: string }> {
  const project = await post<{ id: string }>(request, "/api/v1/projects", { title: `Outputs ${unique()}`, initial_input: "x", input_type: "PROBLEM" });
  const p = `/api/v1/projects/${project.id}`;
  const claim = await post<{ id: string; statement: string }>(request, `${p}/claims`, {
    statement: "Mentoring drops in year two",
    claim_type: "OBSERVATION",
  });
  const work = await post<{ editions: { id: string }[] }>(request, "/api/v1/sources", { work: { title: "Cohort study" }, project_id: project.id });
  const access = await post<{ id: string }>(request, `${p}/access-requests`, {
    edition_id: work.editions[0].id,
    reason: "evidence",
    requested_scope: "p. 1",
    acceptable_forms: ["EXACT_TEXT"],
  });
  const response = await post<{ excerpt: { id: string } }>(request, `${p}/access-requests/${access.id}/responses`, {
    form: "EXACT_TEXT",
    location: "p. 1",
    text: PASSAGE,
  });
  const evidence = await post<{ id: string }>(request, `${p}/evidence`, {
    target_type: "CLAIM",
    target_id: claim.id,
    role: "SUPPORTS",
    finding: "Cohort data shows the drop",
    excerpt_id: response.excerpt.id,
    track: "SUPPORT",
  });
  await post(request, `${p}/evidence/${evidence.id}/assess`, { decision: "ACCEPT", strength: "SUPPORTED", limitations: "one cohort" });
  return { projectId: project.id, claim: claim.statement };
}

test("outputs: composed report traces claims, protects quotes, and is approved by a person", async ({ page, request }) => {
  const { projectId, claim } = await projectWithEvidence(request);
  await page.goto(`/en/projects/${projectId}/outputs`);
  const form = page.getByTestId("new-output");
  await form.getByLabel("Title").fill("Year-two report");
  await form.getByLabel("Mode").selectOption("AUDIT");
  await form.getByRole("button", { name: "Compose" }).click();
  await page.getByTestId("output-row").getByRole("link", { name: "Year-two report" }).click();

  const preview = page.getByTestId("output-preview");
  await expect(preview).toContainText(claim);
  await expect(preview.getByTestId("protected-quote")).toContainText(PASSAGE);
  await expect(preview).toContainText("Claim:");
  await expect(page.getByTestId("output-status")).toContainText("DRAFT");

  await page.getByTestId("approve-output").getByRole("button", { name: "Approve this version" }).click();
  await expect(page.getByTestId("output-status")).toContainText("APPROVED");
});

test("7. referenced output passes the integrity pipeline, is approved, and exports with verbatim quotes", async ({ page, request }) => {
  const { projectId } = await projectWithEvidence(request);
  await page.goto(`/en/projects/${projectId}/outputs`);
  const form = page.getByTestId("new-output");
  await form.getByLabel("Title").fill("Referenced report");
  await form.getByRole("button", { name: "Compose" }).click();
  await page.getByTestId("output-row").getByRole("link", { name: "Referenced report" }).click();

  const integrity = page.getByTestId("integrity");
  await integrity.getByRole("button", { name: "Run integrity checks" }).click();
  const report = page.getByTestId("integrity-report");
  await expect(report).toContainText("VERIFIED");
  await expect(report).toContainText("EXACT_QUOTE_VERIFICATION: PASS");
  await expect(report).toContainText("FINAL_RENDERING: PASS");

  await page.getByTestId("approve-output").getByRole("button", { name: "Approve this version" }).click();
  await expect(page.getByTestId("output-status")).toContainText("APPROVED");

  const href = await page.getByTestId("export-md").getAttribute("href");
  const download = await page.request.get(href!);
  expect(download.ok()).toBeTruthy();
  const markdown = await download.text();
  expect(markdown).toContain(`> ${PASSAGE}`);
  expect(markdown).toContain("Cohort study");

  const docx = await page.request.get((await page.getByTestId("export-docx").getAttribute("href"))!);
  expect(docx.headers()["content-type"]).toBe("application/vnd.openxmlformats-officedocument.wordprocessingml.document");
  expect((await docx.body()).subarray(0, 2).toString()).toBe("PK");
  const pdf = await page.request.get((await page.getByTestId("export-pdf").getAttribute("href"))!);
  expect(pdf.headers()["content-type"]).toBe("application/pdf");
  const pdfBytes = await pdf.body();
  expect(pdfBytes.subarray(0, 4).toString()).toBe("%PDF");
  expect(pdfBytes.includes("quotes.json")).toBeTruthy();
});

test("8. export a Research Core Package; importing it where the project exists never overwrites it", async ({ page, request }) => {
  const { projectId } = await projectWithEvidence(request);
  await page.goto(`/en/projects/${projectId}`);
  const href = await page.getByTestId("export-package").getAttribute("href");
  const download = await page.request.get(href!);
  expect(download.ok()).toBeTruthy();
  expect(download.headers()["content-type"]).toBe("application/zip");
  const zip = await download.body();
  expect(zip.subarray(0, 2).toString()).toBe("PK");

  await page.goto("/en");
  const form = page.getByTestId("import-package");
  await form.locator('input[type="file"]').setInputFiles({ name: "package.zip", mimeType: "application/zip", buffer: zip });
  await form.getByRole("button", { name: "Import" }).click();
  await expect(page.getByTestId("import-card").getByRole("alert")).toContainText("already exists");
});

test("workspace: an explicit selection is staged, recorded in the disclosure manifest, and deleted", async ({ page, request }) => {
  const info = (await (await request.get(`${API_URL}/api/v1/workspace`)).json()) as { enabled: boolean };
  test.skip(!info.enabled, "no cloud workspace adapter is configured for this stack");
  const { projectId, claim } = await projectWithEvidence(request);
  await page.goto(`/en/projects/${projectId}/workspace`);
  await expect(page.getByTestId("disclosure-manifest")).toContainText("Nothing has been staged.");
  const form = page.getByTestId("stage-selection");
  await form.getByLabel("Purpose").fill("Remote review of the year-two claim");
  await form.getByRole("checkbox", { name: claim }).check();
  await form.getByRole("button", { name: "Stage", exact: true }).click();

  const row = page.getByTestId("staging-row");
  await expect(row.getByTestId("staging-status")).toHaveText("ACTIVE");
  await expect(row.getByTestId("staged-item")).toHaveCount(1);
  await expect(row).toContainText("Claim");

  await row.getByLabel("Reason").fill("Review finished");
  await row.getByRole("button", { name: "Delete from workspace" }).click();
  await expect(row.getByTestId("staging-status")).toHaveText("DELETED");
  await expect(row).toContainText("Review finished");
});
