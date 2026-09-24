import { expect, test } from "@playwright/test";

/**
 * Phase 4 design synthesis (issue #33, PRD §32): requirements before solutions,
 * the Design Readiness Gate, human selection, and rejected designs kept in history.
 */

const API_URL = process.env.API_URL ?? "http://localhost:8000";
const unique = () => `${Date.now()}-${Math.floor(Math.random() * 1e6)}`;

test("design: requirement -> concept -> gate -> human selection; rejection keeps history", async ({ page, request }) => {
  const project = await request.post(`${API_URL}/api/v1/projects`, {
    data: { title: `Design ${unique()}`, initial_input: "How to keep apprentices engaged?", input_type: "PROBLEM" },
  });
  expect(project.ok()).toBeTruthy();
  const projectId = ((await project.json()) as { id: string }).id;
  const mechanism = await request.post(`${API_URL}/api/v1/projects/${projectId}/mechanisms`, {
    data: { name: "Peer accountability", description: "Reusable mechanism" },
  });
  expect(mechanism.ok()).toBeTruthy();

  await page.goto(`/en/projects/${projectId}/design`);
  await expect(page.getByTestId("design-requirements")).toContainText("No design requirements yet");

  const newRequirement = page.getByTestId("new-requirement");
  await newRequirement.getByLabel("Statement").fill("Must fit within existing shift patterns");
  await newRequirement.getByRole("button", { name: "Add requirement" }).click();
  await expect(page.getByTestId("requirement-row")).toContainText("ACTIVE");

  for (const title of ["Buddy rota", "Evening classes"]) {
    const form = page.getByTestId("new-concept");
    await form.getByLabel("Title").fill(title);
    await form.getByLabel("Description").fill(`${title} for second-year apprentices`);
    if (title === "Evening classes") await form.getByRole("group", { name: "Mechanisms" }).getByLabel("Peer accountability").check();
    await form.getByRole("button", { name: "Add concept" }).click();
    await expect(page.getByTestId("concept-row").filter({ hasText: title })).toBeVisible();
  }

  // Requirements before solutions: an unaddressed MUST requirement blocks selection.
  const buddy = page.getByTestId("concept-row").filter({ hasText: "Buddy rota" });
  await buddy.getByTestId("select-concept").getByRole("button", { name: "Select this concept" }).click();
  await expect(buddy.getByTestId("select-concept").getByRole("alert")).toContainText("is not addressed");

  await buddy.getByTestId("coverage-row").getByRole("button", { name: "Record coverage" }).click();
  await expect(buddy.getByTestId("coverage-row")).toContainText("MEETS");
  await buddy.getByTestId("select-concept").getByLabel("Reason").fill("Best fit for shifts");
  await buddy.getByTestId("select-concept").getByRole("button", { name: "Select this concept" }).click();
  await expect(buddy).toContainText("SELECTED");
  await expect(buddy.getByTestId("readiness")).toContainText("PASS_WITH_RESERVATIONS");

  // Selection is not a ranking: the other concept is untouched; rejecting it keeps it with its mechanism.
  const evening = page.getByTestId("concept-row").filter({ hasText: "Evening classes" });
  await expect(evening).toContainText("PROPOSED");
  const reject = evening.getByTestId("reject-concept");
  await reject.getByLabel("Reason").fill("Conflicts with rest rules");
  await reject.getByRole("button", { name: "Reject" }).click();
  await expect(evening.getByTestId("concept-rejection")).toContainText("Peer accountability");
  await expect(page.getByTestId("concept-row")).toHaveCount(2);
});
