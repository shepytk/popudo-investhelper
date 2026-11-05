/** Boundary adapter: form text to validated domain assumptions; no financial calculations. */
import type { ValuationInputs } from "./model";

export type ValuationForm = Readonly<{
  fcf: string;
  debt: string;
  shares: string;
  growth: string;
  discount: string;
  terminal: string;
  spread: string;
  years: string;
  price: string;
  currency: string;
}>;

type FormResult =
  | { status: "ready"; input: ValuationInputs; spread: number; price: number | null }
  | { status: "incomplete"; reason: string };

function enteredNumber(value: string): number | null {
  if (!value.trim() || !/^[+-]?(?:\d+\.?\d*|\.\d+)$/.test(value.trim())) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function parseValuationForm(form: ValuationForm): FormResult {
  const numeric = [form.fcf, form.debt, form.shares, form.growth, form.discount,
    form.terminal, form.spread, form.years].map(enteredNumber);
  if (numeric.some((value) => value === null)) {
    return { status: "incomplete", reason: "Enter every required assumption to calculate a hypothetical valuation." };
  }
  const [baseFcfMillions, netDebtMillions, dilutedSharesMillions, growthPct,
    discountPct, terminalPct, spreadPct, horizonYears] = numeric as number[];
  if (spreadPct < 0 || spreadPct > 50) {
    return { status: "incomplete", reason: "Scenario growth spread must be between 0 and 50 percentage points." };
  }
  if (!Number.isInteger(horizonYears) || horizonYears < 1 || horizonYears > 20) {
    return { status: "incomplete", reason: "Forecast length must be between 1 and 20 years." };
  }
  const price = form.price.trim() ? enteredNumber(form.price) : null;
  if (form.price.trim() && (price === null || price < 0)) {
    return { status: "incomplete", reason: "The optional comparison price must be a nonnegative number." };
  }
  return {
    status: "ready",
    input: {
      baseFcfMillions, netDebtMillions, dilutedSharesMillions,
      growthRate: growthPct / 100, discountRate: discountPct / 100,
      terminalGrowthRate: terminalPct / 100, horizonYears,
    },
    spread: spreadPct / 100,
    price,
  };
}
