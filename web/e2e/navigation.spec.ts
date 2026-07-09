import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test("header nav links are visible and clickable", async ({ page }) => {
    await page.goto("/");
    const nav = page.locator("header nav");
    const links = ["Search", "Documents", "Ask", "Ingest"];
    for (const label of links) {
      await expect(nav.locator(`text=${label}`)).toBeVisible();
    }
  });

  test("active nav link has highlighted style", async ({ page }) => {
    await page.goto("/search");
    const activeLink = page.locator("header nav a:has-text('Search')");
    await expect(activeLink).toHaveClass(/bg-accent/);
  });

  test("logo links to home", async ({ page }) => {
    await page.goto("/search");
    await page.locator("header a:has-text('LORNEWS')").click();
    await expect(page).toHaveURL("/");
  });
});
