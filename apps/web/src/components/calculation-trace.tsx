/** Formula transparency over actual, source-attributed statement inputs. */
export type TraceStatement = {
  fiscal_year: number;
  period_end_date: string;
  reporting_currency: string | null;
  amount_unit: string | null;
  operating_cash_flow: string;
  capital_expenditure: string;
  free_cash_flow: string;
  total_debt: string;
  cash_and_equivalents: string;
  source: string;
  source_url: string | null;
};

function finiteDecimal(value: string): number | null {
  if (!/^-?\d+(?:\.\d+)?$/.test(value)) return null;
  const result = Number(value);
  return Number.isFinite(result) && Math.abs(result) <= Number.MAX_SAFE_INTEGER ? result : null;
}

export function CalculationTrace({ statements }: { statements: TraceStatement[] }) {
  const latest = statements[0];
  if (!latest) return <p role="status">No verified statement inputs are available for calculation traces.</p>;
  const cash = finiteDecimal(latest.operating_cash_flow);
  const capex = finiteDecimal(latest.capital_expenditure);
  const fcf = finiteDecimal(latest.free_cash_flow);
  const debt = finiteDecimal(latest.total_debt);
  const balance = finiteDecimal(latest.cash_and_equivalents);
  const currency = latest.reporting_currency;
  const unit = latest.amount_unit;
  const comparable = currency && unit === "ones";
  const fcfValid = comparable && cash !== null && capex !== null && capex >= 0 && fcf !== null &&
    Math.abs(cash - capex - fcf) <= 0.01;
  const netDebtValid = comparable && debt !== null && balance !== null;
  return (
    <section aria-labelledby="traces-title" className="rounded-xl border border-slate-300 p-4 dark:border-slate-700 sm:p-6">
      <h2 id="traces-title" className="text-xl font-semibold">Calculation audit trail</h2>
      <p className="mt-2 text-sm">Inputs from fiscal year {latest.fiscal_year} (ended {latest.period_end_date}).
        Reported currency: {currency || "unknown"}; unit: {unit || "unknown"}.</p>
      <dl className="mt-4 space-y-4 text-sm">
        <div>
          <dt className="font-semibold">Free cash flow = operating cash flow − capital expenditure</dt>
          <dd className="mt-1">{fcfValid
            ? `${latest.operating_cash_flow} − ${latest.capital_expenditure} = ${latest.free_cash_flow} ${currency}`
            : "Not computable or not reconciled from current source inputs."}</dd>
        </div>
        <div>
          <dt className="font-semibold">Net debt = total debt − cash and equivalents</dt>
          <dd className="mt-1">{netDebtValid
            ? `${latest.total_debt} − ${latest.cash_and_equivalents} = ${debt! - balance!} ${currency}`
            : "Not computable with comparable sourced debt and cash inputs."}</dd>
        </div>
        <div>
          <dt className="font-semibold">Price / earnings (P/E)</dt>
          <dd>Market capitalization ÷ trailing earnings. Requires verified shares outstanding and dated prices matched to the same security; not computed here.</dd>
        </div>
        <div>
          <dt className="font-semibold">Enterprise value (EV) and dilution</dt>
          <dd>EV = equity market value + debt − cash (plus other applicable adjustments). Per-share values need a verified diluted share count and capital structure; unavailable until sourced.</dd>
        </div>
        <div>
          <dt className="font-semibold">DCF / intrinsic value</dt>
          <dd>Discounted future free cash flows and terminal value less net debt, divided by diluted shares. Forecast assumptions, discount rate and sources are not available; no valuation is inferred.</dd>
        </div>
      </dl>
      <p className="mt-4 text-xs text-slate-700 dark:text-slate-300">
        Source: {latest.source_url?.startsWith("https://")
          ? <a className="underline" href={latest.source_url} target="_blank" rel="noopener noreferrer">{latest.source} (opens in a new tab)</a>
          : latest.source}. These arithmetic traces are research explanations, not investment recommendations.
      </p>
    </section>
  );
}
