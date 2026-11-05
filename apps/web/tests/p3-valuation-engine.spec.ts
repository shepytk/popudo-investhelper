import { test, expect } from "@playwright/test";

import { calculateDcf } from "../src/lib/valuation/model";
import { buildScenarios, buildSensitivity, marginOfSafety } from "../src/lib/valuation/scenarios";
import { parseValuationForm } from "../src/lib/valuation/input";

const inputs = {
  baseFcfMillions: 100,
  netDebtMillions: 0,
  dilutedSharesMillions: 100,
  growthRate: 0,
  discountRate: 0.10,
  terminalGrowthRate: 0,
  horizonYears: 5,
} as const;

test("pure DCF: exact zero-growth perpetuity, independent of UI", () => {
  const outcome = calculateDcf(inputs);
  expect(outcome.status).toBe("ok");
  if (outcome.status !== "ok") return;
  expect(outcome.result.enterpriseValueMillions).toBeCloseTo(1000, 8);
  expect(outcome.result.intrinsicValuePerShare).toBeCloseTo(10, 8);
  expect(outcome.result.years).toHaveLength(5);
});

test("pure DCF: net debt reduces equity and intrinsic value, net cash increases it", () => {
  const withDebt = calculateDcf({ ...inputs, netDebtMillions: 200 });
  const withCash = calculateDcf({ ...inputs, netDebtMillions: -200 });
  expect(withDebt.status).toBe("ok");
  expect(withCash.status).toBe("ok");
  if (withDebt.status === "ok" && withCash.status === "ok") {
    expect(withDebt.result.intrinsicValuePerShare).toBeCloseTo(8, 8);
    expect(withCash.result.intrinsicValuePerShare).toBeCloseTo(12, 8);
  }
});

test("invalid terminal growth, missing share count and nonfinite values fail closed", () => {
  expect(calculateDcf({ ...inputs, terminalGrowthRate: 0.10 }).status).toBe("invalid");
  expect(calculateDcf({ ...inputs, dilutedSharesMillions: 0 }).status).toBe("invalid");
  expect(calculateDcf({ ...inputs, baseFcfMillions: Number.NaN }).status).toBe("invalid");
});

test("scenario builder reuses the same pure calculation for every scenario", () => {
  const rows = buildScenarios(inputs, 0.02);
  expect(rows.map((row) => row.label)).toEqual(["Bear", "Base", "Bull"]);
  expect(rows[1].outcome).toEqual(calculateDcf(inputs));
  expect(rows[0].growthRate).toBeCloseTo(-0.02);
  expect(rows[2].growthRate).toBeCloseTo(0.02);
});

test("sensitivity rejects invalid discount and terminal combinations", () => {
  const rows = buildSensitivity(inputs, [-0.10, 0], [0, 0.10]);
  expect(rows).toHaveLength(4);
  expect(rows.filter((row) => row.outcome.status === "invalid")).toHaveLength(3);
});

test("form adapter never converts absent values into zero; explicit zero net debt is valid", () => {
  const form = {
    fcf: "100", debt: "", shares: "100", growth: "0", discount: "10",
    terminal: "0", spread: "2", years: "5", price: "", currency: "EUR",
  };
  expect(parseValuationForm(form).status).toBe("incomplete");
  expect(parseValuationForm({ ...form, debt: "0" }).status).toBe("ready");
});

test("margin of safety requires a positive intrinsic value", () => {
  expect(marginOfSafety(100, 75)).toBeCloseTo(0.25);
  expect(marginOfSafety(0, 75)).toBeNull();
});
