import { expect, test } from "@playwright/test";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

test.describe("platform foundation smoke", () => {
  test("API is ready with local dependencies and without cloud AI", async ({ request }) => {
    const response = await request.get(`${API_URL}/health/ready`);
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body).toMatchObject({ status: "ready", database: "ok", queue: "ok" });
  });

  test("background job round-trips API -> queue -> worker -> database", async ({ request }) => {
    const created = await request.post(`${API_URL}/api/v1/system/jobs/ping`);
    expect(created.status()).toBe(202);
    const { id } = await created.json();

    await expect
      .poll(async () => (await (await request.get(`${API_URL}/api/v1/system/jobs/${id}`)).json()).state, {
        timeout: 15_000,
      })
      .toBe("SUCCEEDED");
  });

  test("root redirects to the English desk and shows system status", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/en$/);
    await expect(page.locator("html")).toHaveAttribute("dir", "ltr");
    await expect(page.getByRole("navigation", { name: "Research spaces" }).getByRole("link")).toHaveCount(5);
    await expect(page.getByTestId("overall-status")).toHaveText("Ready");
  });

  test("Arabic interface renders right-to-left", async ({ page }) => {
    await page.goto("/ar/library");
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await expect(page.locator("html")).toHaveAttribute("lang", "ar");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("المكتبة");
  });

  test("unknown locale is a 404, not a crash", async ({ page }) => {
    const response = await page.goto("/de");
    expect(response?.status()).toBe(404);
  });

  test("an unknown project is a not-found page, not an error", async ({ page }) => {
    // Pages stream behind a loading state, so the not-found view arrives in the stream rather than as a 404 status.
    await page.goto("/en/projects/00000000-0000-4000-8000-000000000000/lab");
    await expect(page.getByTestId("page-not-found")).toBeVisible();
    await expect(page.getByTestId("page-error")).toHaveCount(0);
  });

  test("pages and the API send security headers", async ({ page, request }) => {
    const response = await page.goto("/en");
    expect(response?.headers()["x-frame-options"]).toBe("DENY");
    expect(response?.headers()["x-content-type-options"]).toBe("nosniff");
    const api = await request.get(`${process.env.API_URL ?? "http://localhost:8000"}/health/live`);
    expect(api.headers()["content-security-policy"]).toContain("default-src 'none'");
  });
});
