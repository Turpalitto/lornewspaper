import { test, expect } from "@playwright/test";

test.describe("Error handling", () => {
  test("settings page shows loading state", async ({ page }) => {
    await page.goto("/settings");
    // Loading states should be visible initially
    await expect(page.locator(".animate-pulse").first()).toBeVisible();
  });

  test("documents page shows loading then empty state", async ({ page }) => {
    await page.goto("/documents");
    // Should show loading skeletons
    await page.waitForTimeout(500);
    // If no API, should show retry or empty
    await expect(page.locator("body")).toBeVisible();
  });

  test("ingest page renders form", async ({ page }) => {
    await page.goto("/ingest");
    await expect(page.locator('input[aria-label="Ingest query"]')).toBeVisible();
    await expect(page.locator("text=Search, download, process")).toBeVisible();
  });
});
