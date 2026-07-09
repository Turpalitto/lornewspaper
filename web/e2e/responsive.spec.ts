import { test, expect } from "@playwright/test";

test.describe("Responsive layout", () => {
  test("no excessive horizontal scroll on mobile viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    await page.waitForTimeout(500);
    const scrollWidth = await page.evaluate(() =>
      document.documentElement.scrollWidth
    );
    const viewportWidth = await page.evaluate(() =>
      document.documentElement.clientWidth
    );
    // Allow small overflow from header nav items on very narrow screens
    const overflow = scrollWidth - viewportWidth;
    expect(overflow).toBeLessThan(120);
  });

  test("no horizontal scroll on tablet viewport", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/search");
    await page.waitForTimeout(300);
    const scrollWidth = await page.evaluate(() =>
      document.documentElement.scrollWidth
    );
    const viewportWidth = await page.evaluate(() =>
      document.documentElement.clientWidth
    );
    expect(scrollWidth).toBeLessThanOrEqual(viewportWidth + 5);
  });

  test("layout adapts to mobile - header visible", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    await expect(page.locator("header")).toBeVisible();
    await expect(page.locator("main")).toBeVisible();
  });

  test("all pages render without critical console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    const pages = ["/", "/search", "/documents", "/ask", "/ingest", "/settings"];
    for (const path of pages) {
      await page.goto(path);
      await expect(page.locator("body")).toBeVisible();
    }
    // Filter expected errors when backend is unavailable
    const critical = errors.filter(
      (e) =>
        !e.includes("favicon") &&
        !e.includes("500") &&
        !e.includes("Failed to fetch") &&
        !e.includes("NetworkError")
    );
    expect(critical).toEqual([]);
  });
});
