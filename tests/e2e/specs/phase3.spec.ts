import { expect, test, type Page } from "@playwright/test";

/**
 * PRD §73 E2E flow 9 (issue #22): provider outage -> project remains usable.
 * The stack runs the mock AI provider in outage mode (AI_MOCK_ENABLED=true, AI_MOCK_MODE=unavailable).
 */

const API_URL = process.env.API_URL ?? "http://localhost:8000";
const unique = () => `${Date.now()}-${Math.floor(Math.random() * 1e6)}`;

async function fillFrame(page: Page, values: Record<string, string>) {
  const form = page.getByTestId("frame-form");
  for (const [label, value] of Object.entries(values)) await form.getByLabel(label, { exact: true }).fill(value);
  await form.getByRole("button", { name: "Save draft" }).click();
  await expect(form.getByRole("status")).toHaveText("Saved.");
}

test("9. provider outage -> AI tasks fail visibly, research continues, data intact", async ({ page, request }) => {
  const profiles = (await (await request.get(`${API_URL}/api/v1/ai/profiles`)).json()) as { name: string; configured: boolean }[];
  test.skip(!profiles.some((p) => p.name === "mock" && p.configured), "stack runs without the mock AI provider");

  const title = `Outage ${unique()}`;
  await page.goto("/en");
  const form = page.getByTestId("new-project");
  await form.getByLabel("Provisional title").fill(title);
  await form.getByLabel("Initial question, problem, idea or system").fill("Why do apprentices disengage in year two?");
  await form.getByRole("button", { name: "Create project" }).click();
  await expect(page).toHaveURL(/\/en\/projects\/[0-9a-f-]{36}$/);
  const projectId = page.url().split("/").pop()!;

  // The AI task fails as a provider failure, visibly and without changing anything.
  const ai = page.getByTestId("ai-assistance");
  await ai.getByRole("button", { name: "Draft Problem Frame with AI" }).click();
  await expect(ai.getByRole("status")).toHaveText("Task queued. Progress appears below.");
  const task = ai.getByTestId("ai-task").first();
  await expect(task).toContainText("FAILED", { timeout: 20_000 });
  await expect(task).toContainText("PROVIDER_ERROR");
  await expect(task).toContainText("does not mean no evidence exists");
  await expect(page.getByTestId("frame-history")).toHaveCount(0);

  // The researcher keeps working by hand: frame, approve.
  await fillFrame(page, {
    "Central issue": "Year-two disengagement",
    "Current state (what is happening)": "Attendance drops in year two",
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

  // "Challenge this" during the outage is recorded as an execution failure, never as "no evidence".
  const created = await request.post(`${API_URL}/api/v1/projects/${projectId}/hypotheses`, {
    data: { content: { statement: `Mentoring loss drives disengagement ${unique()}` } },
  });
  expect(created.ok()).toBeTruthy();
  const hypothesisId = ((await created.json()) as { id: string }).id;
  await page.goto(`/en/projects/${projectId}/hypotheses/${hypothesisId}`);
  const challenge = page.getByTestId("challenge");
  await challenge.getByRole("button", { name: "Challenge this" }).click();
  await expect(challenge.getByTestId("ai-task").first()).toContainText("PROVIDER_ERROR", { timeout: 20_000 });
  await page.reload();
  await expect(page.getByTestId("track-CHALLENGE")).toContainText("search failed");
  await expect(page.getByTestId("track-ALTERNATIVE_EXPLANATION")).toContainText("search failed");

  // Project data is intact and readable through the API.
  const project = await (await request.get(`${API_URL}/api/v1/projects/${projectId}`)).json();
  expect(project.title).toBe(title);
  const frames = (await (await request.get(`${API_URL}/api/v1/projects/${projectId}/problem-frames`)).json()) as {
    status: string;
    provenance: { kind: string };
  }[];
  expect(frames.map((f) => [f.status, f.provenance.kind])).toEqual([["APPROVED", "HUMAN_INPUT"]]);
  const log = (await (await request.get(`${API_URL}/api/v1/projects/${projectId}/ai-requests`)).json()) as {
    status: string;
    error_kind: string;
  }[];
  expect(log.length).toBeGreaterThanOrEqual(2);
  expect(log.every((entry) => entry.status === "FAILED")).toBeTruthy();
});
