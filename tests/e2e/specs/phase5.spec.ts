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
