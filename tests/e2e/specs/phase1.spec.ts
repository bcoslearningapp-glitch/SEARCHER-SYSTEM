import { expect, test, type Page } from "@playwright/test";

import { makePdf } from "../support/pdf";

/** PRD §73 E2E flows 1-3 (issue #7). Each test uses unique names so reruns never collide. */

const unique = () => `${Date.now()}-${Math.floor(Math.random() * 1e6)}`;

async function createProject(page: Page, title: string): Promise<string> {
  await page.goto("/en");
  const form = page.getByTestId("new-project");
  await form.getByLabel("Provisional title").fill(title);
  await form.getByLabel("Initial question, problem, idea or system").fill("Why do apprentices disengage in year two?");
  await form.getByRole("button", { name: "Create project" }).click();
  await expect(page).toHaveURL(/\/en\/projects\/[0-9a-f-]{36}$/);
  // User content keeps its own direction inside RTL/LTR interfaces (NFR-I18N-002).
  await expect(page.getByRole("heading", { level: 1, name: title })).toHaveAttribute("dir", "auto");
  return page.url();
}

async function fillFrame(page: Page, values: Record<string, string>) {
  const form = page.getByTestId("frame-form");
  for (const [label, value] of Object.entries(values)) await form.getByLabel(label, { exact: true }).fill(value);
  await form.getByRole("button", { name: "Save draft" }).click();
  await expect(form.getByRole("status")).toHaveText("Saved.");
}

test("1. create project -> draft Problem Frame -> explicit approval", async ({ page }) => {
  await createProject(page, `Framing ${unique()}`);
  await expect(page.getByTestId("project-status")).toHaveText("DRAFT");
  await expect(page.getByTestId("current-question")).toContainText("None yet");

  // An incomplete frame is blocked by the Framing Gate.
  await fillFrame(page, { "Central issue": "Year-two disengagement" });
  await expect(page.getByTestId("project-status")).toHaveText("FRAMING");
  await expect(page.getByTestId("attention")).toContainText("Problem Frame v1 awaits your approval");
  const approve = page.getByTestId("approve-form");
  await approve.getByRole("button", { name: "Approve as baseline" }).click();
  await expect(approve.getByRole("alert")).toContainText("Framing Gate is BLOCKED");
  await expect(approve.getByRole("alert")).toContainText("Missing the gap.");

  await fillFrame(page, {
    "Current state (what is happening)": "Attendance drops about 30% in year two",
    "Desired state": "Sustained engagement",
    Gap: "Drivers unknown",
    Context: "Construction apprenticeships",
    "Current explanations": "Pay plateau",
    "Initial hypotheses": "Mentoring declines after year one",
    Constraints: "No budget for new staff",
    "What is known": "Drop starts around month 14",
    "What is unknown": "Role of pay progression",
    "Research questions": "What drives year-two disengagement?",
    "Points requiring reference review": "Just treatment of apprentices",
  });
  await page.getByTestId("approve-form").getByRole("button", { name: "Approve as baseline" }).click();

  await expect(page.getByTestId("project-status")).toHaveText("ACTIVE_RESEARCH");
  await expect(page.getByTestId("current-question")).toHaveText("What drives year-two disengagement?");
  await expect(page.getByTestId("frame-history")).toContainText("APPROVED");
  await expect(page.getByTestId("research-state")).toContainText("Role of pay progression");
});

test("2. add digital source -> extract text with page anchors -> find it", async ({ page }) => {
  const title = `Mentoring study ${unique()}`;
  const marker = `zephyrmentor${Math.floor(Math.random() * 1e9)}`;
  await page.goto("/en/library");
  const catalog = page.getByTestId("catalog-form");
  await catalog.getByLabel("Work title").fill(title);
  await catalog.getByRole("button", { name: "Catalog" }).click();

  const work = page.getByTestId("source-work").filter({ hasText: title });
  await expect(work.getByTestId("verification-state")).toHaveText("METADATA_ONLY");
  await expect(work.getByTestId("availability")).toHaveText("Not available here");

  await work.getByLabel("File to upload").setInputFiles({
    name: "study.pdf",
    mimeType: "application/pdf",
    buffer: makePdf(["Introduction.", `Mentoring declines sharply ${marker} in the second year.`]),
  });
  await work.getByRole("button", { name: "Upload file" }).click();
  await expect(work.getByTestId("availability")).toHaveText("Available here");
  // Uploading makes content available but never raises verification by itself.
  await expect(work.getByTestId("verification-state")).toHaveText("METADATA_ONLY");

  await expect(async () => {
    await page.reload();
    await expect(
      page.getByTestId("source-work").filter({ hasText: title }).getByTestId("ingestion-status"),
    ).toHaveText("Text extraction: COMPLETE");
  }).toPass({ timeout: 20_000 });

  await page.goto(`/en/library?q=${marker}`);
  const hit = page.getByTestId("search-hit");
  await expect(hit).toHaveCount(1);
  await expect(hit).toContainText(`${title} — p. 2`);
  await expect(page.getByTestId("search-results")).toContainText("not quotations");
});

test("3. physical metadata-only source -> Hybrid Source Access -> exact excerpt", async ({ page }) => {
  const projectUrl = await createProject(page, `Hybrid ${unique()}`);
  const bookTitle = `Muqaddimah ${unique()}`;
  await page.goto(`${projectUrl}/sources`);

  await page.getByText("Catalog a source").click();
  const catalog = page.getByTestId("catalog-form");
  await catalog.getByLabel("Work title").fill(bookTitle);
  await catalog.getByLabel("Authors (separate with ;)").fill("Ibn Khaldun");
  await catalog.getByLabel("Authority layer").selectOption("HISTORICAL_CIVILIZATIONAL");
  await catalog.getByLabel("Holding", { exact: true }).selectOption("PHYSICAL");
  await catalog.getByRole("button", { name: "Catalog" }).click();
  const work = page.getByTestId("source-work").filter({ hasText: bookTitle });
  await expect(work.getByTestId("availability")).toHaveText("Not available here");

  const request = page.getByTestId("access-request-form");
  await request.getByLabel("Edition").selectOption({ label: `${bookTitle} (Not available here)` });
  await request.getByLabel("Why it is needed").fill("Need the passage on cohesion decay");
  await request.getByLabel("Pages, chapter or section").fill("Chapter 2, sections 10-12");
  await request.getByRole("checkbox", { name: "RESEARCHER_SUMMARY" }).check();
  await request.getByRole("button", { name: "Request access" }).click();

  const item = page.getByTestId("access-request").filter({ hasText: "Chapter 2, sections 10-12" });
  await expect(item.getByTestId("request-status")).toHaveText("OPEN");
  await page.goto(projectUrl);
  await expect(page.getByTestId("attention")).toContainText("Source access needed: Chapter 2, sections 10-12");
  await page.goto(`${projectUrl}/sources`);

  const respond = item.getByTestId("respond-form");
  await respond.getByLabel("Response type").selectOption("EXACT_TEXT");
  await respond.getByLabel("Location (page, section)").fill("vol. 1, p. 278");
  await respond.getByLabel("Text", { exact: true }).fill("Exact words typed from the physical book.");
  await respond.getByRole("button", { name: "Provide content" }).click();

  const excerpt = item.getByTestId("excerpt");
  await expect(excerpt).toContainText("Exact words typed from the physical book.");
  await expect(excerpt).toContainText("RESEARCHER_SUPPLIED_EXACT");
  await expect(item.getByTestId("request-status")).toHaveText("PARTIALLY_FULFILLED");
});
