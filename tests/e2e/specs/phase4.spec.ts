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

test("experiment: observation -> result -> interpretation stay distinct; invalidation is not a failed test", async ({ page, request }) => {
  const api = `${API_URL}/api/v1/projects`;
  const projectId = ((await (await request.post(api, { data: { title: `Exp ${unique()}`, initial_input: "x", input_type: "IDEA" } })).json()) as { id: string }).id;
  const concept = (await (await request.post(`${api}/${projectId}/design/concepts`, { data: { title: "Buddy rota", description: "d" } })).json()) as { id: string };
  const content = {
    intervention: "Weekly buddy check-in",
    target_population: "Second-year apprentices",
    context: "Sites",
    mechanism: "Peer accountability",
    expected_outcome: "Attendance above 90%",
    measurement_plan: "Weekly attendance",
    failure_conditions: ["Below 80%"],
    side_effects: ["Buddy workload"],
    stop_conditions: ["Safeguarding concern"],
  };
  const dh = await request.post(`${api}/${projectId}/design-hypotheses`, { data: { concept_id: concept.id, content, affects_people: false } });
  expect(dh.ok()).toBeTruthy();

  await page.goto(`/en/projects/${projectId}/experiments`);
  for (const title of ["Buddy pilot", "Rerun pilot"]) {
    const form = page.getByTestId("new-experiment");
    await form.getByLabel("Title").fill(title);
    for (const [label, value] of Object.entries({
      Method: "Pilot",
      Sample: "20 apprentices",
      "Data collected": "Attendance",
      "Analysis plan": "Compare with last cohort",
      "Success criteria": "90%",
    }))
      await form.getByLabel(label, { exact: true }).fill(value);
    await form.getByRole("button", { name: "Create" }).click();
    await expect(page.getByTestId("experiment-row").filter({ hasText: title })).toBeVisible();
  }

  const move = async (target: string, reason = "") => {
    const form = page.getByTestId("transition-form");
    await form.getByLabel("Move to").selectOption(target);
    await form.getByLabel("Reason").fill(reason);
    await form.getByRole("button", { name: "Move" }).click();
    await expect(page.getByTestId("experiment-state")).toHaveText(target);
  };

  await page.getByTestId("experiment-row").filter({ hasText: "Buddy pilot" }).getByRole("link").click();
  for (const target of ["PROTOCOL_DEFINED", "APPROVED", "RUNNING"]) await move(target);
  const observe = page.getByTestId("observation-form");
  await observe.getByLabel("Description").fill("Week 1: 18 of 20 attended");
  await observe.getByRole("button", { name: "Record" }).click();
  await expect(page.getByTestId("observations")).toContainText("18 of 20");
  await move("DATA_COLLECTION_COMPLETE");
  await move("ANALYSIS");
  const result = page.getByTestId("result-form");
  await result.getByLabel("Method").fill("Attendance rate");
  await result.getByLabel("Summary").fill("90% attendance");
  await result.getByRole("button", { name: "Record" }).click();
  const interpret = page.getByTestId("interpretation-form");
  await interpret.getByLabel("Statement").fill("Attendance held in week one");
  await interpret.getByRole("button", { name: "Record" }).click();
  await expect(page.getByTestId("interpretations")).toContainText("Attendance held");
  await expect(page.getByTestId("observations")).toContainText("18 of 20");
  await expect(page.getByTestId("results")).toContainText("90% attendance");
  await move("INTERPRETED");

  await page.goto(`/en/projects/${projectId}/experiments`);
  await page.getByTestId("experiment-row").filter({ hasText: "Rerun pilot" }).getByRole("link").click();
  for (const target of ["PROTOCOL_DEFINED", "APPROVED", "RUNNING"]) await move(target);
  await move("INVALIDATED", "Attendance system outage corrupted the data");
  await expect(page.getByTestId("invalidated")).toContainText("not a failed test");
  await page.goto(`/en/projects/${projectId}/experiments`);
  await expect(page.getByTestId("design-hypothesis-row")).toContainText("UNRESOLVED");
});
