/** Scenario orchestration depends on the pure valuation function, not on any UI. */
import { calculateDcf, type DcfResult, type ValuationInputs, type ValuationOutcome } from "./model";

export type Scenario = Readonly<{ label: "Bear" | "Base" | "Bull"; growthRate: number; outcome: ValuationOutcome }>;
export type SensitivityCell = Readonly<{ discountRate: number; terminalGrowthRate: number; outcome: ValuationOutcome }>;

export function buildScenarios(input: ValuationInputs, spread: number): readonly Scenario[] {
  return ([
    ["Bear", input.growthRate - spread],
    ["Base", input.growthRate],
    ["Bull", input.growthRate + spread],
  ] as const).map(([label, growthRate]) => ({
    label, growthRate, outcome: calculateDcf({ ...input, growthRate }),
  }));
}

export function buildSensitivity(
  input: ValuationInputs, discountOffsets: readonly number[], terminalOffsets: readonly number[],
): readonly SensitivityCell[] {
  return discountOffsets.flatMap((discountOffset) => terminalOffsets.map((terminalOffset) => {
    const discountRate = input.discountRate + discountOffset;
    const terminalGrowthRate = input.terminalGrowthRate + terminalOffset;
    return {
      discountRate, terminalGrowthRate,
      outcome: calculateDcf({ ...input, discountRate, terminalGrowthRate }),
    };
  }));
}

export function marginOfSafety(
  intrinsicValue: number, enteredPrice: number,
): number | null {
  if (![intrinsicValue, enteredPrice].every(Number.isFinite) ||
      intrinsicValue <= 0 || enteredPrice < 0) return null;
  return (intrinsicValue - enteredPrice) / intrinsicValue;
}

export function enterpriseValueShareFromTerminal(result: DcfResult): number {
  return result.enterpriseValueMillions === 0 ? 0 :
    result.presentValueTerminalMillions / result.enterpriseValueMillions;
}
