const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;

test("research missing data is honest, accessible and mobile usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://127.0.0.1:3000/companies/1", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "Verified fundamentals" })).toBeVisible();
  await expect(page.getByText(/No complete, verified annual statements/)).toBeVisible();
  await expect(page.getByText(/No independently verified listing/)).toBeVisible();
  await expect(page.getByText(/No source-verified quotations/)).toBeVisible();
  const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
  expect(bodyWidth).toBeLessThanOrEqual(392);
  const audit = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(audit.violations).toEqual([]);
});

test("unknown company produces an explicit error state", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/companies/999999");
  await expect(page.getByRole("heading", { name: "Company not found" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Back to sectors" })).toBeVisible();
});

test("keyboard-accessible research summary action exists", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/companies/1");
  await expect(page.getByRole("button", { name: "Generate sourced summary" })).toBeEnabled();
  expect(await page.locator("a, button").count()).toBeGreaterThan(1);
});
