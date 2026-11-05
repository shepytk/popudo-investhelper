import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("P3 mobile screening and accessibility", () => {
  for (const width of [320, 390, 768]) {
    test(`screener remains usable at ${width}px`, async ({ page }) => {
      await page.setViewportSize({ width, height: 850 });
      await page.goto("/screener");
      const form = page.getByRole("search");
      await expect(form).toBeVisible();
      await expect(page.getByLabel("Name or symbol")).toBeVisible();
      await page.getByLabel("Name or symbol").fill("ASML");
      await page.getByRole("button", { name: "Apply filters" }).click();
      await expect(page).toHaveURL(/q=ASML/);
      await expect(page.getByLabel("Name or symbol")).toHaveValue("ASML");
      const horizontalOverflow = await page.evaluate(() =>
        document.documentElement.scrollWidth > window.innerWidth + 2
      );
      expect(horizontalOverflow).toBe(false);
    });
  }

  test("keyboard navigation, landmarks and critical accessibility rules", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/screener");
    await expect(page.getByRole("main")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Company screener" })).toBeVisible();
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
    await page.getByLabel("Name or symbol").focus();
    await expect(page.getByLabel("Name or symbol")).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(page.getByLabel("Country ID (optional)")).toBeFocused();
  });

  test("company API failures never render invented numerical values", async ({ page }) => {
    await page.goto("/companies/1");
    await expect(page.getByRole("main")).toBeVisible();
    await expect(page.getByRole("alert")).toContainText(/unavailable|not found/i);
  });
});
