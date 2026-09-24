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

test("6. design -> experiment -> learning review -> local knowledge, reused with a label", async ({ page, request }) => {
  const api = `${API_URL}/api/v1/projects`;
  const create = async (title: string) =>
    ((await (await request.post(api, { data: { title, initial_input: "x", input_type: "PROBLEM" } })).json()) as { id: string }).id;
  const projectId = await create(`Flow six ${unique()}`);
  const otherTitle = `Nursing ${unique()}`;
  const otherId = await create(otherTitle);

  // Design: a requirement before a concept.
  await page.goto(`/en/projects/${projectId}/design`);
  const requirement = page.getByTestId("new-requirement");
  await requirement.getByLabel("Statement").fill("Must fit within shift patterns");
  await requirement.getByRole("button", { name: "Add requirement" }).click();
  await expect(page.getByTestId("requirement-row")).toBeVisible();
  const concept = page.getByTestId("new-concept");
  await concept.getByLabel("Title").fill("Buddy rota");
  await concept.getByLabel("Description").fill("Weekly buddy check-ins");
  await concept.getByRole("button", { name: "Add concept" }).click();
  await expect(page.getByTestId("concept-row")).toBeVisible();

  // Design hypothesis and experiment.
  await page.getByRole("link", { name: "Experiments" }).click();
  const dh = page.getByTestId("new-design-hypothesis");
  for (const [label, value] of Object.entries({
    Intervention: "Weekly buddy check-in",
    "Target population": "Second-year apprentices",
    Context: "Construction sites",
    Mechanism: "Peer accountability",
    "Expected outcome": "Attendance above 90%",
    "Measurement plan": "Weekly attendance",
    "Failure conditions": "Below 80% after 8 weeks",
    "Possible side effects": "Buddy workload",
    "Stop conditions": "Safeguarding concern",
  }))
    await dh.getByLabel(label, { exact: true }).fill(value);
  await dh.getByRole("button", { name: "Create" }).click();
  await expect(page.getByTestId("design-hypothesis-row")).toContainText("UNRESOLVED");
  const experiment = page.getByTestId("new-experiment");
  await experiment.getByLabel("Title").fill("Buddy pilot");
  for (const [label, value] of Object.entries({
    Method: "Pilot",
    Sample: "20 apprentices",
    "Data collected": "Attendance",
    "Analysis plan": "Compare cohorts",
    "Success criteria": "90%",
  }))
    await experiment.getByLabel(label, { exact: true }).fill(value);
  await experiment.getByRole("button", { name: "Create" }).click();
  await page.getByTestId("experiment-row").getByRole("link").click();

  const move = async (target: string) => {
    const form = page.getByTestId("transition-form");
    await form.getByLabel("Move to").selectOption(target);
    await form.getByRole("button", { name: "Move" }).click();
    await expect(page.getByTestId("experiment-state")).toHaveText(target);
  };
  for (const target of ["PROTOCOL_DEFINED", "APPROVED", "RUNNING"]) await move(target);
  await page.getByTestId("observation-form").getByLabel("Description").fill("18 of 20 attended");
  await page.getByTestId("observation-form").getByRole("button", { name: "Record" }).click();
  await expect(page.getByTestId("observations")).toContainText("18 of 20");
  await move("DATA_COLLECTION_COMPLETE");
  await move("ANALYSIS");
  await page.getByTestId("result-form").getByLabel("Method").fill("Attendance rate");
  await page.getByTestId("result-form").getByLabel("Summary").fill("90%");
  await page.getByTestId("result-form").getByRole("button", { name: "Record" }).click();
  await expect(page.getByTestId("results")).toContainText("90%");
  await page.getByTestId("interpretation-form").getByLabel("Statement").fill("Attendance held");
  await page.getByTestId("interpretation-form").getByRole("button", { name: "Record" }).click();
  await expect(page.getByTestId("interpretations")).toContainText("Attendance held");
  await move("INTERPRETED");

  // Learning review: closing without one is refused by the Learning Integrity Gate.
  const transition = page.getByTestId("transition-form");
  await transition.getByLabel("Move to").selectOption("CLOSED");
  await transition.getByRole("button", { name: "Move" }).click();
  await expect(transition.getByRole("alert")).toContainText("learning review");
  const learning = page.getByTestId("learning-form");
  await learning.getByLabel("What was learned").fill("Buddy check-ins sustain attendance");
  await learning.getByLabel("What it means for the design hypothesis").fill("Supports it at one site");
  await learning.getByLabel("Limitations").fill("One site only");
  await learning.getByRole("button", { name: "Record" }).click();
  await expect(page.getByTestId("learning-review")).toContainText("Buddy check-ins sustain attendance");
  await move("CLOSED");

  // Local knowledge: recorded as a project finding, promoted by a person.
  await page.getByRole("link", { name: "Knowledge" }).click();
  const knowledge = page.getByTestId("new-knowledge");
  await knowledge.getByLabel("Statement").fill("Weekly buddy check-ins sustain year-two attendance");
  await knowledge.getByRole("group", { name: "Evidence basis" }).getByRole("checkbox").first().check();
  await knowledge.getByRole("button", { name: "Record" }).click();
  const row = page.getByTestId("knowledge-row");
  await expect(row.getByTestId("knowledge-stage")).toHaveText("PROJECT_FINDING");
  await row.getByTestId("promote-form").getByRole("button", { name: "Promote" }).click();
  await expect(row.getByTestId("knowledge-stage")).toHaveText("LOCAL_RESULT");

  // Reuse elsewhere is an explicit, labelled judgment and never evidence there.
  const reuse = row.getByTestId("reuse-form");
  await reuse.getByLabel("Project").selectOption({ label: otherTitle });
  await reuse.getByLabel("Transferability").selectOption("ANALOGICAL_ONLY");
  await reuse.getByLabel("Rationale").fill("Nursing shifts differ");
  await reuse.getByRole("button", { name: "Reuse in another project" }).click();
  await expect(reuse.getByRole("alert")).toHaveCount(0);
  await page.goto(`/en/projects/${otherId}/knowledge`);
  const reused = page.getByTestId("reused-knowledge");
  await expect(reused).toContainText("ANALOGICAL_ONLY");
  await expect(reused).toContainText("Not evidence in this project");
});

test("terminology: approved canonical form; translation check flags association turned into causation", async ({ page }) => {
  const domain = `apprenticeships-${unique()}`;
  await page.goto("/en/library/terminology");
  const form = page.getByTestId("propose-term");
  await form.getByLabel("Term", { exact: true }).fill("year-two disengagement");
  await form.getByLabel("Domain").fill(domain);
  await form.getByLabel("Definition").fill("Falling engagement in the second year of an apprenticeship");
  await form.getByLabel("fr", { exact: true }).fill("désengagement de deuxième année");
  await form.getByLabel("ar", { exact: true }).fill("الانسحاب في السنة الثانية");
  await form.getByRole("button", { name: "Propose term" }).click();
  const row = page.getByTestId("term-row").filter({ hasText: domain });
  await expect(row).toContainText("PROPOSED");
  await row.getByRole("button", { name: "Approve" }).click();
  await expect(row).toContainText("APPROVED");

  const check = page.getByTestId("translation-check");
  await check.getByLabel("Source text").fill("Year-two disengagement is associated with pay freezes.");
  await check.getByLabel("Translation language").selectOption("fr");
  await check.getByLabel("Translation", { exact: true }).fill("Le gel des salaires provoque le décrochage.");
  await check.getByLabel("Domain").fill(domain);
  await check.getByRole("button", { name: "Check" }).click();
  const result = page.getByTestId("check-result");
  await expect(result).toContainText("Needs review");
  await expect(result.getByTestId("drift")).toContainText("association became causation");
  await expect(result.getByTestId("term-findings")).toContainText("désengagement de deuxième année");
});
