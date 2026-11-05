/** Pure five-year DCF engine. This module has no React, API, or storage dependencies. */
export type ValuationInputs = Readonly<{
  baseFcfMillions: number;
  netDebtMillions: number;
  dilutedSharesMillions: number;
  growthRate: number;
  discountRate: number;
  terminalGrowthRate: number;
  horizonYears: number;
}>;

export type ValuationYear = Readonly<{
  year: number;
  projectedFcfMillions: number;
  discountFactor: number;
  presentValueMillions: number;
}>;

export type DcfResult = Readonly<{
  years: readonly ValuationYear[];
  terminalValueMillions: number;
  presentValueTerminalMillions: number;
  enterpriseValueMillions: number;
  equityValueMillions: number;
  intrinsicValuePerShare: number;
}>;

export type ValuationOutcome =
  | Readonly<{ status: "ok"; result: DcfResult }>
  | Readonly<{ status: "invalid"; reason: string }>;

export function calculateDcf(input: ValuationInputs): ValuationOutcome {
  const numbers = [
    input.baseFcfMillions, input.netDebtMillions, input.dilutedSharesMillions,
    input.growthRate, input.discountRate, input.terminalGrowthRate, input.horizonYears,
  ];
  if (!numbers.every(Number.isFinite)) return { status: "invalid", reason: "All assumptions must be finite numbers." };
  if (input.baseFcfMillions <= 0 || input.dilutedSharesMillions <= 0) {
    return { status: "invalid", reason: "Free cash flow and diluted shares must be greater than zero." };
  }
  if (!Number.isInteger(input.horizonYears) || input.horizonYears < 1 || input.horizonYears > 20) {
    return { status: "invalid", reason: "Forecast horizon must be an integer between 1 and 20 years." };
  }
  if (input.growthRate <= -1 || input.growthRate > 1) {
    return { status: "invalid", reason: "FCF growth must be greater than −100% and at most 100%." };
  }
  if (input.discountRate <= 0 || input.discountRate > 1) {
    return { status: "invalid", reason: "Discount rate must be greater than zero and at most 100%." };
  }
  if (input.terminalGrowthRate <= -1 || input.discountRate <= input.terminalGrowthRate) {
    return { status: "invalid", reason: "Terminal growth must exceed −100% and remain below the discount rate." };
  }
  const years: ValuationYear[] = [];
  let presentValueFcfMillions = 0;
  for (let year = 1; year <= input.horizonYears; year++) {
    const projectedFcfMillions = input.baseFcfMillions * (1 + input.growthRate) ** year;
    const discountFactor = (1 + input.discountRate) ** year;
    const presentValueMillions = projectedFcfMillions / discountFactor;
    years.push({ year, projectedFcfMillions, discountFactor, presentValueMillions });
    presentValueFcfMillions += presentValueMillions;
  }
  const terminalFcf = years[years.length - 1].projectedFcfMillions * (1 + input.terminalGrowthRate);
  const terminalValueMillions = terminalFcf / (input.discountRate - input.terminalGrowthRate);
  const presentValueTerminalMillions =
    terminalValueMillions / years[years.length - 1].discountFactor;
  const enterpriseValueMillions = presentValueFcfMillions + presentValueTerminalMillions;
  const equityValueMillions = enterpriseValueMillions - input.netDebtMillions;
  const intrinsicValuePerShare = equityValueMillions / input.dilutedSharesMillions;
  if (![terminalValueMillions, presentValueTerminalMillions, enterpriseValueMillions,
    equityValueMillions, intrinsicValuePerShare].every(Number.isFinite)) {
    return { status: "invalid", reason: "The assumptions cause numerical overflow." };
  }
  return {
    status: "ok",
    result: {
      years, terminalValueMillions, presentValueTerminalMillions, enterpriseValueMillions,
      equityValueMillions, intrinsicValuePerShare,
    },
  };
}
