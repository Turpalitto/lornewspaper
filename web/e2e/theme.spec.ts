import { test, expect } from "@playwright/test";

test.describe("Theme toggle", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForFunction(
      () => !document.querySelector('button[aria-label="Toggle theme"]')?.disabled,
      { timeout: 10000 }
    );
  });

  test("theme toggle button exists", async ({ page }) => {
    const toggle = page.locator('button[aria-label="Toggle theme"]');
    await expect(toggle).toBeVisible();
  });

  test("clicking toggle changes theme", async ({ page }) => {
    const toggle = page.locator('button[aria-label="Toggle theme"]');
    const initialTheme = await page.evaluate(() =>
      document.documentElement.className
    );
    await toggle.click();
    await page.waitForTimeout(300);
    const newTheme = await page.evaluate(() =>
      document.documentElement.className
    );
    expect(newTheme).not.toBe(initialTheme);
  });

  test("theme persists on navigation", async ({ page }) => {
    const toggle = page.locator('button[aria-label="Toggle theme"]');
    await toggle.click();
    await page.waitForTimeout(300);
    const theme = await page.evaluate(() =>
      document.documentElement.className
    );
    await page.goto("/search");
    await page.waitForTimeout(300);
    const themeAfterNav = await page.evaluate(() =>
      document.documentElement.className
    );
    expect(themeAfterNav).toBe(theme);
  });
});
