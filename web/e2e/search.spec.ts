import { test, expect } from "@playwright/test";

test.describe("Search page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/search");
    await page.waitForSelector('input[aria-label="Search query"]', { timeout: 10000 });
  });

  test("search form renders with input and button", async ({ page }) => {
    await expect(page.locator('input[aria-label="Search query"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test("shows placeholder text when no search performed", async ({ page }) => {
    await expect(page.locator("text=Enter a query")).toBeVisible();
  });

  test("disables search button with empty input", async ({ page }) => {
    await expect(page.locator('button[type="submit"]')).toBeDisabled();
  });

  test("enables search button with input", async ({ page }) => {
    const input = page.locator('input[aria-label="Search query"]');
    await input.evaluate((el) => {
      const nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, "value"
      )!.set!;
      nativeSetter.call(el, "machine learning");
      el.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await page.waitForTimeout(300);
    await expect(page.locator('button[type="submit"]')).toBeEnabled({ timeout: 3000 });
  });

  test("shows loading state during search", async ({ page }) => {
    await page.route("**/api/v1/search", async (route) => {
      await new Promise((r) => setTimeout(r, 1000));
      await route.fulfill({ status: 200, json: { articles: [], total: 0, elapsed_ms: 100 } });
    });
    const input = page.locator('input[aria-label="Search query"]');
    await input.evaluate((el) => {
      const nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, "value"
      )!.set!;
      nativeSetter.call(el, "test query");
      el.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await page.waitForTimeout(200);
    await page.locator('button[type="submit"]').click();
    await expect(page.locator(".animate-pulse").first()).toBeVisible();
  });
});
