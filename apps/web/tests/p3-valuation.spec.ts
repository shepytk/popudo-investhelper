import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("DCF engine remains empty until user supplies assumptions, then uses exact perpetuity", async ({ page }) => {
  await page.goto("/valuation-lab");
  await expect(page.getByRole("heading", { name: "Valuation methodology" })).toBeVisible();
  await expect(page.getByText("Hypothetical intrinsic value per diluted share")).toHaveCount(0);
  await page.getByLabel(/Starting annual free cash flow/).fill("100");
  await page.getByLabel(/Net debt/).fill("0");
  await page.getByLabel(/Diluted shares outstanding/).fill("100");
  await page.getByLabel(/Annual FCF growth/).fill("0");
  await page.getByLabel(/Discount rate/).fill("10");
  await page.getByLabel(/Terminal growth/).fill("0");
  await page.getByLabel(/Bear\/bull growth difference/).fill("2");
  await page.getByRole("button", { name: "Calculate scenarios" }).click();
  await expect(page.getByText("Hypothetical intrinsic value per diluted share")).toBeVisible();
  const result = page.getByRole("region", { name: "Hypothetical valuation results" });
  await expect(result.getByText("10 EUR", { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Sensitivity to discount rate and terminal growth" })).toBeVisible();
  await expect(page.getByRole("table", { name: /Hypothetical five-by-five DCF sensitivity matrix/ })).toBeVisible();
  const violations = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(violations.violations).toEqual([]);
});

test("invalid terminal assumptions do not produce valuation", async ({ page }) => {
  await page.goto("/valuation-lab");
  await page.getByLabel(/Starting annual free cash flow/).fill("100");
  await page.getByLabel(/Net debt/).fill("10");
  await page.getByLabel(/Diluted shares outstanding/).fill("100");
  await page.getByLabel(/Annual FCF growth/).fill("5");
  await page.getByLabel(/Discount rate/).fill("4");
  await page.getByLabel(/Terminal growth/).fill("5");
  await page.getByLabel(/Bear\/bull growth difference/).fill("2");
  await page.getByRole("button", { name: "Calculate scenarios" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Terminal growth" })).toContainText("Terminal growth");
  await expect(page.getByText("Hypothetical intrinsic value per diluted share")).toHaveCount(0);
});
