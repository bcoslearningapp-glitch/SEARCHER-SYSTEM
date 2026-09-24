import { defineConfig, devices } from "@playwright/test";

/**
 * Cross-stack smoke tests against a running `docker compose` stack.
 * WEB_URL / API_URL default to the compose host ports.
 */
export default defineConfig({
  testDir: "./specs",
  timeout: 30_000,
  retries: 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.WEB_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        launchOptions: process.env.PW_CHROMIUM_EXECUTABLE
          ? { executablePath: process.env.PW_CHROMIUM_EXECUTABLE }
          : {},
      },
    },
  ],
});
