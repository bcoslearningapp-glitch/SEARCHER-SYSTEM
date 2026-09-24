import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

/** PRD §73 E2E flows 4 and 5 (issue #16). Setup uses the API; the judgments under test go through the UI. */

const API_URL = process.env.API_URL ?? "http://localhost:8000";
const unique = () => `${Date.now()}-${Math.floor(Math.random() * 1e6)}`;

async function api<T>(request: APIRequestContext, method: "get" | "post", path: string, data?: unknown): Promise<T> {
  const response = await request[method](`${API_URL}${path}`, data === undefined ? {} : { data });
  expect(response.ok(), `${method} ${path}: ${await response.text()}`).toBeTruthy();
  return (await response.json()) as T;
}

/** Project with one hypothesis and three researcher-supplied exact source passages. */
async function setup(request: APIRequestContext) {
  const project = await api<{ id: string }>(request, "post", "/api/v1/projects", {
    title: `Phase 2 ${unique()}`,
    initial_input: "Does mentoring loss drive disengagement?",
    input_type: "HYPOTHESIS",
  });
  const pid = project.id;
  const hypothesis = await api<{ id: string }>(request, "post", `/api/v1/projects/${pid}/hypotheses`, {
    content: { statement: `Mentoring loss drives disengagement ${unique()}` },
  });
  const passages: Record<string, string> = {};
  for (const [title, text] of [
    ["Cohort study", "Cohort passage on mentoring"],
    ["Regional survey", "Survey passage on mentoring"],
    ["Counter study", "Retention rose where mentoring was cut"],
  ]) {
    const work = await api<{ editions: { id: string }[] }>(request, "post", "/api/v1/sources", {
      work: { title: `${title} ${unique()}` },
      project_id: pid,
    });
    const req = await api<{ id: string }>(request, "post", `/api/v1/projects/${pid}/access-requests`, {
      edition_id: work.editions[0]!.id,
      reason: "evidence",
      requested_scope: "p. 1",
      acceptable_forms: ["EXACT_TEXT"],
    });
    await api(request, "post", `/api/v1/projects/${pid}/access-requests/${req.id}/responses`, {
      form: "EXACT_TEXT",
      location: "p. 1",
      text,
    });
    passages[title] = text;
  }
  return { pid, hid: hypothesis.id, passages };
}

async function addAndAcceptEvidence(page: Page, passage: string, role: string, finding: string, strength: string) {
  const form = page.getByTestId("add-evidence");
  const option = form.getByLabel("Source passage").locator("option", { hasText: passage });
  await form.getByLabel("Source passage").selectOption({ label: (await option.textContent())! });
  await form.getByLabel("Role").selectOption(role);
  await form.getByLabel("What the passage shows").fill(finding);
  await form.getByRole("button", { name: "Add evidence" }).click();
  const candidate = page.getByTestId("evidence-candidate").filter({ hasText: finding });
  await candidate.getByLabel("Evidence strength").selectOption(strength);
  await candidate.getByRole("button", { name: "Save" }).click();
  await expect(page.getByTestId("accepted-evidence").filter({ hasText: finding })).toBeVisible();
}

test("4. hypothesis -> supporting and challenging evidence -> downgrade with history", async ({ page, request }) => {
  const { pid, hid, passages } = await setup(request);
  await page.goto(`/en/projects/${pid}/hypotheses/${hid}`);
  await expect(page.getByTestId("counter-evidence")).toContainText("not complete");

  await addAndAcceptEvidence(page, passages["Cohort study"]!, "SUPPORTS", "Cohort shows the drop", "SUPPORTED");
  await addAndAcceptEvidence(page, passages["Regional survey"]!, "SUPPORTS", "Survey agrees", "SUPPORTED");
  await expect(page.getByTestId("support-origins")).toHaveText("2");

  const assess = page.getByTestId("assess");
  await assess.getByLabel("Assessment").selectOption("SUPPORTED");
  await assess.getByLabel("Reason").fill("Two independent origins");
  await assess.getByRole("button", { name: "Record assessment" }).click();
  await expect(page.getByTestId("hypothesis-assessment")).toHaveText("SUPPORTED");

  // Challenge track: counter-evidence found and accepted.
  await addAndAcceptEvidence(page, passages["Counter study"]!, "CONTRADICTS", "Counter-example", "SUPPORTED");
  await expect(page.getByTestId("hypothesis-assessment")).toHaveText("CONTESTED");
  const versions = page.getByTestId("versions");
  await expect(versions).toContainText("SUPPORTED");
  await expect(versions).toContainText("SYSTEM");

  const search = page.getByTestId("record-search");
  for (const track of ["CHALLENGE", "ALTERNATIVE_EXPLANATION"]) {
    await search.getByLabel("Search track").selectOption(track);
    await search.getByLabel("What was searched").fill("Local library, en/ar");
    await search.getByRole("button", { name: "Record a search" }).click();
    await expect(page.getByTestId(`track-${track}`)).toContainText("searched");
  }
  await expect(page.getByTestId("counter-evidence")).toContainText("complete");
});

test("5. reference review -> blocking reservation -> human decision", async ({ page, request }) => {
  const { pid, hid } = await setup(request);
  await page.goto(`/en/projects/${pid}/hypotheses/${hid}`);

  const newReview = page.getByTestId("new-review");
  await newReview.getByLabel("Question").fill("Is the incentive acceptable?");
  await newReview.getByLabel("Analytical category").selectOption("VALUES_AND_EVALUATIVE_STANDARDS");
  await newReview.getByRole("button", { name: "Start a reference review" }).click();

  const review = page.getByTestId("review").filter({ hasText: "Is the incentive acceptable?" });
  const judge = review.getByTestId("judge-form");
  await judge.getByLabel("Assessment").selectOption("RESERVED");
  await judge.getByLabel("Reservation").selectOption("BLOCKING_RESERVATION");
  await judge.getByLabel("Rationale").fill("Approved readings differ on the incentive");
  await judge.getByRole("button", { name: "Record judgment" }).click();
  await expect(review.getByTestId("current-judgment")).toContainText("BLOCKING_RESERVATION");
  await expect(page.getByTestId("standing")).toContainText("BLOCKED");

  // The reservation became a blocking decision the researcher must take on the Desk.
  await page.goto(`/en/projects/${pid}`);
  await expect(page.getByTestId("attention")).toContainText("BLOCKING");
  const decision = page.getByTestId("decisions").locator("li").filter({ hasText: "Blocking reference reservation" });
  await decision.getByLabel("Decision").selectOption("Keep the reservation");
  await decision.getByLabel("Justification").fill("Await the authority's ruling");
  await decision.getByRole("button", { name: "Decide" }).click();
  await expect(page.getByTestId("decisions")).toContainText("Await the authority's ruling");

  await page.goto(`/en/projects/${pid}/map`);
  await expect(page.getByTestId("map-decisions")).toContainText("DECIDED");
});
