import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report" }],
    ["json", { outputFile: "playwright-results.json" }],
  ],
  use: {
    baseURL: "http://localhost:3200",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1280, height: 800 },
      },
    },
    {
      name: "mobile",
      use: {
        ...devices["iPhone 13"],
        viewport: { width: 390, height: 844 },
      },
    },
  ],
  webServer: {
    command: "npx next dev --port 3200",
    url: "http://localhost:3200",
    reuseExistingServer: true,
    timeout: 30000,
    env: {
      NEXT_TELEMETRY_DISABLED: "1",
    },
  },
});
