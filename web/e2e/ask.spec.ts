import { test, expect } from "@playwright/test";

test.describe("Ask page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/ask");
    await page.waitForSelector('input[aria-label="Research question"]', { timeout: 10000 });
  });

  test("ask form renders with input and button", async ({ page }) => {
    await expect(page.locator('input[aria-label="Research question"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test("shows placeholder text initially", async ({ page }) => {
    await page.goto("/ask");
    await expect(page.locator("text=Ask a research question")).toBeVisible();
  });

  test("disables button with empty input", async ({ page }) => {
    await page.goto("/ask");
    await expect(page.locator('button[type="submit"]')).toBeDisabled();
  });

  test("enables button with input", async ({ page }) => {
    const input = page.locator('input[aria-label="Research question"]');
    await input.evaluate((el) => {
      const nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, "value"
      )!.set!;
      nativeSetter.call(el, "What is AI?");
      el.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await page.waitForTimeout(200);
    await expect(page.locator('button[type="submit"]')).toBeEnabled();
  });
});
