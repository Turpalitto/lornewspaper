import { test, expect } from "@playwright/test";

test.describe("Home page", () => {
  test("loads and shows quick actions", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toHaveText("LORNEWS");
    const cards = page.locator("a[href]").filter({ has: page.locator("h2") });
    await expect(cards).toHaveCount(4);
  });

  test("all quick action links navigate correctly", async ({ page }) => {
    await page.goto("/");
    const links = [
      { href: "/search", label: "Search Literature" },
      { href: "/documents", label: "Browse Documents" },
      { href: "/ask", label: "Ask a Question" },
      { href: "/ingest", label: "Ingest Articles" },
    ];
    for (const link of links) {
      await page.locator(`a[href="${link.href}"]`).first().click();
      await expect(page).toHaveURL(link.href);
      await page.goBack();
    }
  });
});
